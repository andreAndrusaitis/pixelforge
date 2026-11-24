"""Testes da via de IA de imagem: pixelização (núcleo, só numpy + Pillow), presets e CLI.

Os testes que geram com a IA são pulados sem o extra [imagem-ia] e sem
PIXELFORGE_TESTES_IA=1 (lentos e precisam de GPU + pesos em models/).

Rodar: python -m unittest discover -s tests
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

from pixelforge import load_spec
from pixelforge.ai_image import cycle, presets, style, train
from pixelforge.ai_image.cli import find_record, slug
from pixelforge.cli import main
from pixelforge.config import load_config
from pixelforge.pixelize import (PixelizeOptions, cell_edges, detect_grid, load_palette_spec, pixelize,
                                 selective_outline)
from pixelforge.sprite import Sprite

ROOT = Path(__file__).resolve().parent.parent
HAS_ANALYSES = (ROOT / "docs" / "estilo" / "analises" / "1.json").is_file()


def tmpdir() -> Path:
    d = tempfile.TemporaryDirectory()
    unittest.addModuleCleanup(d.cleanup)
    return Path(d.name)


def fake_ai(small: np.ndarray, scale: float, offset: int = 0, blur: float = 1.0, noise: float = 5.0,
            seed: int = 0) -> np.ndarray:
    """Imita o rascunho da IA: arte pequena ampliada (pseudo-pixel), deslocada, borrada e com ruído."""
    h, w = small.shape[:2]
    big = Image.fromarray(small).resize((round(w * scale), round(h * scale)), Image.Resampling.NEAREST)
    arr = np.roll(np.array(big), (offset, offset), (0, 1))
    arr = np.array(Image.fromarray(arr).filter(ImageFilter.GaussianBlur(blur))).astype(float)
    arr += np.random.default_rng(seed).normal(0, noise, arr.shape)
    return np.clip(arr, 0, 255).astype(np.uint8)


def blocky(h: int = 24, w: int = 24, colors: int = 5, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    palette = rng.integers(20, 235, (colors, 3)).astype(np.uint8)
    return palette[rng.integers(0, colors, (h, w))]


class GridTests(unittest.TestCase):
    def test_detects_integer_and_fractional_scale(self):
        for scale, offset in ((8, 3), (6, 0), (12, 5), (16, 4), (7.5, 2)):
            with self.subTest(scale=scale):
                grid = detect_grid(fake_ai(blocky(40, 40, 6, seed=int(scale * 2)), scale, offset))
                self.assertAlmostEqual(grid.scale, scale, delta=0.26)
                self.assertGreater(grid.confidence, 1.0)

    def test_noise_has_no_confident_grid(self):
        noise = np.random.default_rng(3).integers(0, 255, (256, 256, 3)).astype(np.uint8)
        smooth = np.array(Image.fromarray(noise).filter(ImageFilter.GaussianBlur(2)))
        self.assertLess(detect_grid(smooth).confidence, 0.6)

    def test_cell_edges_cover_image(self):
        edges = cell_edges(100, 8, 3)
        self.assertEqual(edges[0], 3)  # fatia de 3 px < meia célula: fora
        self.assertEqual(edges[-1], 99)  # fatia final de 1 px: fora
        self.assertEqual(cell_edges(104, 8, 3)[-1], 104)  # fatia final de 5 px: entra
        self.assertTrue(np.all(np.diff(edges) >= 4))
        self.assertEqual(list(cell_edges(64, 8, 0)), list(range(0, 65, 8)))


class PixelizeTests(unittest.TestCase):
    def test_recovers_original_pixels(self):
        small = blocky(32, 32, 5, seed=1)
        img = Image.fromarray(fake_ai(small, 8, 0))
        for method in ("mode", "median"):
            with self.subTest(method=method):
                art = pixelize(img, PixelizeOptions(colors=5, method=method, cleanup=0))
                self.assertEqual(art.size, (32, 32))
                out = art.frames[0].pixels[..., :3].astype(int)
                close = np.abs(out - small.astype(int)).max(axis=2) <= 24
                self.assertGreater(close.mean(), 0.97)
                self.assertLessEqual(len(art.colors()), 5)

    def test_offset_grid_is_aligned(self):
        small = blocky(30, 30, 4, seed=2)
        # deslocada 3 px: a fatia de 3 px na borda fica de fora; as células batem com os pixels
        art = pixelize(Image.fromarray(fake_ai(small, 8, 3)), PixelizeOptions(colors=4, cleanup=0))
        self.assertEqual(art.size, (30, 30))
        out = art.frames[0].pixels[..., :3].astype(int)
        self.assertGreater((np.abs(out - small.astype(int)).max(axis=2) <= 24).mean(), 0.97)

    def test_requested_size_without_grid(self):
        noise = np.random.default_rng(4).integers(0, 255, (200, 300, 3)).astype(np.uint8)
        art = pixelize(Image.fromarray(noise), PixelizeOptions(size=(30, 20), colors=8))
        self.assertEqual(art.size, (30, 20))
        self.assertIsNone(art.meta["grid"])

    def test_named_palette_and_file_palette(self):
        img = Image.fromarray(fake_ai(blocky(16, 16, 4, seed=5), 8))
        art = pixelize(img, PixelizeOptions(palette="pico8"))
        pico = {tuple(c[:3]) for c in load_palette_spec("pico8")}
        self.assertTrue({c[:3] for c in art.colors()} <= pico)

        folder = tmpdir()
        swatch = folder / "cena.png"
        Image.fromarray(np.array([[[10, 20, 30], [200, 100, 50], [90, 90, 90]]], dtype=np.uint8)).save(swatch)
        art = pixelize(img, PixelizeOptions(palette=str(swatch)))
        self.assertTrue({c[:3] for c in art.colors()} <= {(10, 20, 30), (200, 100, 50), (90, 90, 90)})

    def test_remove_background_and_selective_outline(self):
        small = np.full((20, 20, 3), 230, dtype=np.uint8)
        small[5:15, 6:14] = (180, 60, 40)
        img = Image.fromarray(fake_ai(small, 8, blur=0.5, noise=2))
        art = pixelize(img, PixelizeOptions(colors=4, remove_bg="auto", outline="selective"))
        px = art.frames[0].pixels
        self.assertEqual(px[0, 0, 3], 0)  # fundo removido
        opaque = px[..., 3] > 0
        body = px[opaque][:, :3].astype(int)
        # contorno mais escuro que o corpo e da mesma família (vermelho)
        darkest = body[body.sum(axis=1).argmin()]
        self.assertLess(darkest.sum(), 180 + 60 + 40)
        self.assertGreater(darkest[0], darkest[2])

    def test_selective_outline_uses_darker_neighbor_shade(self):
        sprite = Sprite.blank(5, 5)
        sprite.pixels[1:4, 1:4] = (200, 50, 50, 255)
        colors = np.array([[200, 50, 50], [90, 20, 20], [20, 20, 90]])
        out = selective_outline(sprite, colors)
        self.assertEqual(tuple(out.pixels[0, 2]), (90, 20, 20, 255))
        self.assertEqual(out.pixels[0, 0, 3], 0)  # diagonal fica vazia

    def test_options_validation(self):
        with self.assertRaises(ValueError):
            PixelizeOptions.from_dict({"cor": 3})
        with self.assertRaises(ValueError):
            PixelizeOptions(method="media").validate()
        with self.assertRaises(ValueError):
            PixelizeOptions(grid="x").validate()
        self.assertIsNone(PixelizeOptions.from_dict({"size": "auto"}).size)
        self.assertEqual(PixelizeOptions.from_dict({"size": "64x48"}).size, (64, 48))


class PresetTests(unittest.TestCase):
    def test_repo_presets_are_valid(self):
        config = load_config(ROOT / "pixelforge.toml")
        names = set(presets.settings(config)["presets"])
        self.assertTrue({"retrato", "personagem-corpo", "cenario", "cena-noturna"} <= names)
        for name in names:
            values = presets.preset(config, name)
            PixelizeOptions.from_dict(presets.pixel_options(values)).validate()
            w, h = presets.resolution(values)
            self.assertEqual((w % 8, h % 8), (0, 0))
            self.assertIn("anime", values.get("negativo", ""))

    def test_portuguese_values_are_translated(self):
        opts = presets.pixel_options({"metodo": "mediana", "contorno": "seletivo", "tamanho": [8, 9], "grade": 8})
        self.assertEqual(opts, {"method": "median", "outline": "selective", "size": [8, 9], "grid": "8"})

    def test_prompt_puts_description_first(self):
        self.assertEqual(presets.join_prompt("menino", "pixel art, luz"), "pixel art, menino, luz")
        self.assertEqual(presets.join_prompt("menino", "luz"), "menino, luz")
        self.assertEqual(slug("Seu Geraldo, o padrinho!"), "seu-geraldo-o-padrinho")


class CliTests(unittest.TestCase):
    def run_cli(self, *argv) -> tuple[int, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(["--config", str(ROOT / "pixelforge.toml"), *argv])
        return code, out.getvalue() + err.getvalue()

    def test_pixelizar_writes_spec_png_and_record(self):
        folder = tmpdir()
        src = folder / "rascunho_bruta.png"
        Image.fromarray(fake_ai(blocky(24, 16, 5, seed=7), 8)).save(src)
        code, text = self.run_cli("ia", "pixelizar", str(src), "--cores", "5", "--tamanho", "16x24",
                                  "--out", str(folder / "saida"))
        self.assertEqual(code, 0, text)
        out = folder / "saida"
        art = load_spec(out / "rascunho.json")
        self.assertEqual(art.size, (16, 24))
        self.assertTrue((out / "rascunho@8x.png").is_file())
        self.assertTrue((out / "rascunho_comparar.png").is_file())
        side, record = find_record(out / "rascunho.png")
        self.assertEqual(record["tamanho_final"], [16, 24])
        self.assertEqual(record["grade"]["scale"], 8.0)

    def test_repixelize_keeps_generation_record(self):
        folder = tmpdir() / "x"
        folder.mkdir()
        Image.fromarray(fake_ai(blocky(12, 12, 4, seed=8), 8)).save(folder / "x_bruta.png")
        (folder / "x_ia.json").write_text(json.dumps({"nome": "x", "pedido": {"seed": 9}}), encoding="utf-8")
        code, text = self.run_cli("ia", "pixelizar", str(folder / "x_bruta.png"), "--cores", "4", "--out", str(folder))
        self.assertEqual(code, 0, text)
        _, record = find_record(folder / "x.png")
        self.assertEqual(record["pedido"], {"seed": 9})
        self.assertEqual(record["tamanho_final"], [12, 12])

    @unittest.skipUnless(HAS_ANALYSES, "sem docs/estilo/analises")
    def test_pixelizar_with_preset_writes_sheet_and_grade(self):
        folder = tmpdir()
        src = folder / "r_bruta.png"
        Image.fromarray(fake_ai(blocky(32, 24, 6, seed=4), 8)).save(src)
        code, text = self.run_cli("ia", "pixelizar", str(src), "--preset", "retrato", "--out", str(folder / "o"))
        self.assertEqual(code, 0, text)
        self.assertIn("nota técnica", text)
        self.assertTrue((folder / "o" / "r_folha.png").is_file())
        _, record = find_record(folder / "o" / "r.png")
        self.assertEqual(record["estilo"]["refs_folha"], [4, 10, 22])
        code, text = self.run_cli("ia", "folha", str(folder / "o" / "r.json"), "--tipo", "retrato")
        self.assertEqual(code, 0, text)

    def test_variar_needs_generation_record(self):
        folder = tmpdir()
        (folder / "x_ia.json").write_text(json.dumps({"nome": "x"}), encoding="utf-8")
        code, text = self.run_cli("ia", "variar", str(folder / "x.png"))
        self.assertEqual(code, 2)
        self.assertIn("pedido", text)

    def test_unknown_preset_is_reported(self):
        code, text = self.run_cli("ia", "pixelizar", "nada.png", "--preset", "nenhum")
        self.assertEqual(code, 2)
        self.assertIn("retrato", text)



class StyleTests(unittest.TestCase):
    def test_presets_have_type_and_clean_refs(self):
        config = load_config(ROOT / "pixelforge.toml")
        index = {r.n for r in style.load_index(config)}
        for name in ("retrato", "personagem-corpo", "cenario", "cena-noturna"):
            values = presets.preset(config, name)
            self.assertIn(style.tipo_for(name, values), ("retrato", "personagem", "cenario", "cena"))
            self.assertEqual(len(values["refs"]), 3)
            self.assertTrue(set(values["refs"]) <= index)
            self.assertFalse(set(values["refs"]) & style.NO_COPY, name)

    def test_join_prompt_puts_trigger_first(self):
        self.assertEqual(presets.join_prompt("menino", "pixel art, luz", "pxfrg style"),
                         "pxfrg style, pixel art, menino, luz")

    def test_caption_uses_index_and_metrics(self):
        metrics = {"paleta": {"cores_efetivas": 20, "croma_media": 0.03}, "contorno": {"ausente": 0.9},
                   "luz_de_borda": {"fracao": 0.3}, "clusters": {"dithering": 0.0, "tamanho_medio": 5}}
        caption = train.caption_for("pxfrg style", "personagem", ["moletom-capuz", "tag-desconhecida"], metrics)
        self.assertTrue(caption.startswith("pxfrg style, pixel art, character, hoodie"))
        for word in ("limited palette", "selective outline", "rim light", "no dithering"):
            self.assertIn(word, caption)
        self.assertNotIn("desconhecida", caption)

    def test_prepare_image_is_integer_upscale_in_64_multiples(self):
        folder = tmpdir()
        small = blocky(40, 24, 5, seed=9)
        src = folder / "ref.png"
        Image.fromarray(fake_ai(small, 6, blur=0.3, noise=1)).save(src)
        img = train.prepare_image(src, 768)
        self.assertEqual((img.width % 64, img.height % 64), (0, 0))
        arr = np.array(img)
        # pixel limpo: cada bloco de 8x8 (fator ×8) tem uma cor só
        block = arr[64:72, 64:72].reshape(-1, 3)
        self.assertEqual(len(np.unique(block, axis=0)), 1)

    def test_cycle_corrections_follow_metric_side(self):
        from types import SimpleNamespace as NS

        low = NS(path="valor.contraste", value=0.3, low=0.5, high=0.8, label="contraste", score=0.4, weight=10)
        high = NS(path="clusters.orfaos", value=0.5, low=0.1, high=0.3, label="órfãos", score=0.5, weight=10)
        result = NS(fora_da_faixa=lambda: [low, high])
        fixes = cycle.corrections(result)
        pixel = cycle.tweak_pixel({"contrast": 1.0, "cleanup": 1, "merge": 0.0}, fixes)
        self.assertGreater(pixel["contrast"], 1.0)
        self.assertEqual(pixel["cleanup"], 2)
        prompt, negative, notes = cycle.tweak_prompt("pixel art", "anime", fixes)
        self.assertIn("strong value contrast", prompt)
        self.assertTrue(negative.endswith("anime"))
        self.assertIn("noisy pixels", negative)

    @unittest.skipUnless(HAS_ANALYSES, "sem docs/estilo/analises")
    def test_score_and_review_sheet(self):
        config = load_config(ROOT / "pixelforge.toml")
        rgba = np.dstack([blocky(96, 72, 12, seed=3), np.full((96, 72), 255, np.uint8)])
        sheet, result = style.review_sheet(rgba, "personagem", config, "teste", chosen=[21, 11, 1])
        self.assertEqual([r.n for r in result.nearest], [21, 11, 1])
        self.assertTrue(0 <= result.nota <= 100)
        self.assertGreater(sheet.width, 600)


class RetouchTests(unittest.TestCase):
    def sprite(self):
        sp = Sprite.blank(10, 10)
        sp.pixels[2:8, 2:8] = (200, 100, 50, 255)
        return sp

    def test_rect_stroke_rim_and_erase(self):
        from pixelforge.retouch import apply_ops

        out = apply_ops(self.sprite(), [
            {"retangulo": [2, 2, 5, 8, "#c86432", "#102030"]},
            {"traco": [[[5, 2, 1], [5, 7, 1]], "#ffffff"]},
            {"rim": [0, 0, 10, 10, "#00ff00", "dir"]},
            {"apagar": [0, 7, 10, 8]},
        ])
        px = out.pixels
        self.assertEqual(tuple(px[3, 3]), (16, 32, 48, 255))
        self.assertEqual(tuple(px[3, 5]), (255, 255, 255, 255))
        self.assertEqual(tuple(px[3, 7]), (0, 255, 0, 255))  # borda direita da silhueta
        self.assertEqual(px[7, 4, 3], 0)
        self.assertEqual(px[0, 0, 3], 0)  # traço/rim não pintam o transparente

    def test_ramp_mode_shift_scale_and_errors(self):
        from pixelforge.retouch import apply_ops

        sp = self.sprite()
        sp.pixels[4, 4] = (90, 40, 20, 255)
        out = apply_ops(sp, [{"moda": [0, 0, 10, 10]}])
        self.assertEqual(tuple(out.pixels[4, 4]), (200, 100, 50, 255))  # órfão absorvido
        out = apply_ops(sp, [{"rampa": [0, 0, 10, 10, ["#000000", "#ffffff"]]}])
        self.assertLessEqual({tuple(c[:3]) for c in out.colors()}, {(0, 0, 0), (255, 255, 255)})
        out = apply_ops(self.sprite(), [{"deslocar": [1, 0, "transparent"]}])
        self.assertEqual(out.pixels[3, 2, 3], 0)
        self.assertEqual(out.pixels[3, 8, 3], 255)
        out = apply_ops(self.sprite(), [{"escalar": [2, 2, 8, 8, 1.5]}])
        self.assertGreater((out.pixels[..., 3] > 0).sum(), 36)
        with self.assertRaises(ValueError):
            apply_ops(self.sprite(), [{"pincel": 1}])

    def test_cli_retocar(self):
        from pixelforge import save_spec
        from pixelforge.sprite import Art

        folder = tmpdir()
        save_spec(Art("a", [self.sprite()]), folder / "a.json")
        (folder / "ops.json").write_text(json.dumps({"retoque": [{"pixels": [[0, 0, "#ff0000"]]}]}),
                                         encoding="utf-8")
        code, text = CliTests.run_cli(self, "ia", "retocar", str(folder / "a.json"), str(folder / "ops.json"),
                                      "--out", str(folder / "o"))
        self.assertEqual(code, 0, text)
        art = load_spec(folder / "o" / "a-r.json")
        self.assertEqual(tuple(art.frames[0].pixels[0, 0]), (255, 0, 0, 255))


def has(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


@unittest.skipUnless(has("diffusers") and has("torch"), "extra [imagem-ia] não instalado")
class GenerationTests(unittest.TestCase):
    def test_request_roundtrip(self):
        from pixelforge.ai_image.generate import Request

        request = Request(prompt="x", seed=5, ref="a.png", style_refs=["b.png"])
        self.assertEqual(Request.from_dict({**request.to_dict(), "novo": 1}), request)
        self.assertEqual(request.adapters(), ("plus", "plus"))
        self.assertEqual(Request(prompt="x").adapters(), ())

    def test_long_prompt_is_split_on_commas(self):
        from transformers import CLIPTokenizer

        from pixelforge.ai_image.generate import split_prompt

        folder = ROOT / "models" / "Lykon--dreamshaper-xl-lightning" / "tokenizer"
        if not folder.is_dir():
            self.skipTest("tokenizer não baixado")
        tokenizer = CLIPTokenizer.from_pretrained(folder)
        text = ", ".join(f"term number {i}" for i in range(40))
        parts = split_prompt(tokenizer, text)
        self.assertGreater(len(parts), 1)
        self.assertEqual(", ".join(parts), text)
        self.assertTrue(all(len(tokenizer(p).input_ids) <= 77 for p in parts))

    @unittest.skipUnless(os.environ.get("PIXELFORGE_TESTES_IA") == "1", "lento: defina PIXELFORGE_TESTES_IA=1")
    def test_generate_is_reproducible(self):
        from pixelforge.ai_image import models
        from pixelforge.ai_image.generate import Engine, Request

        base = models.models_dir("models", ROOT)
        request = Request(prompt="pixel art, red apple", width=512, height=512, seed=11, steps=4)
        engine = Engine.for_request(request, base)
        a = np.array(engine.run(request).image, dtype=int)
        b = np.array(engine.run(request).image, dtype=int)
        self.assertLess(np.abs(a - b).mean(), 2.0)


if __name__ == "__main__":
    unittest.main()
