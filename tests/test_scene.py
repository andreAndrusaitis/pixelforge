"""Testes do motor de cena (etapa 1). Rodar: python -m unittest discover -s tests"""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from pixelforge.cli import main
from pixelforge.config import DEFAULTS, load_config
from pixelforge.scene import (Library, SceneError, Timeline, has_mp4, open_scene, parse_resolution,
                              parse_scene, render_all, render_frame, save_gif, save_mp4, save_webp,
                              storyboard)
from pixelforge.scene.timeline import quantize, shot_ranges

PRESETS = DEFAULTS["cena"]["presets"]


def tmpdir() -> Path:
    d = tempfile.TemporaryDirectory()
    unittest.addModuleCleanup(d.cleanup)
    return Path(d.name)


def png(path: Path, width: int, height: int, color=(255, 0, 0, 255), marks: dict | None = None) -> Path:
    """PNG de cor sólida; `marks` = {(x, y): cor} pinta pixels marcadores."""
    pixels = np.zeros((height, width, 4), np.uint8)
    pixels[:] = color
    for (x, y), c in (marks or {}).items():
        pixels[y, x] = c
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(pixels, "RGBA").save(path)
    return path


def timeline(data: dict, folder: Path, resolution=(16, 8), fps: int = 10, art_dir: Path | None = None) -> Timeline:
    scene = parse_scene(data, folder / "roteiro.json")
    return Timeline(scene, Library(art_dir), resolution, fps)


class ScriptValidationTests(unittest.TestCase):
    def test_minimal_scene(self):
        scene = parse_scene({"cenario": "x", "planos": [{"dur": 2}]})
        self.assertEqual(scene.name, "cena")
        self.assertEqual(scene.duration, 2)
        self.assertEqual(scene.intro.kind, "corte")

    def test_requires_shots_and_duration(self):
        with self.assertRaisesRegex(SceneError, "planos"):
            parse_scene({"cenario": "x"})
        with self.assertRaisesRegex(SceneError, "plano 2, dur: obrigatório"):
            parse_scene({"cenario": "x", "planos": [{"dur": 1}, {}]})
        with self.assertRaisesRegex(SceneError, "cenario"):
            parse_scene({"planos": [{"dur": 1}]})

    def test_unknown_field_lists_valid_fields(self):
        with self.assertRaises(SceneError) as ctx:
            parse_scene({"cenario": "x", "planos": [{"dur": 1}], "titulo": "a"})
        self.assertIn("'titulo'", str(ctx.exception))
        self.assertIn("Campos válidos: name, resolucao", str(ctx.exception))
        with self.assertRaisesRegex(SceneError, "plano 1: campo 'som'.*Campos válidos: dur"):
            parse_scene({"cenario": "x", "planos": [{"dur": 1, "som": []}]})
        with self.assertRaisesRegex(SceneError, "paleta.*ainda não"):
            parse_scene({"cenario": "x", "planos": [{"dur": 1}], "paleta": "pico8"})

    def test_comment_fields_are_ignored(self):
        parse_scene({"_nota": "oi", "cenario": "x", "planos": [{"dur": 1, "_x": 1}]})

    def test_errors_point_to_shot_and_field(self):
        with self.assertRaisesRegex(SceneError, r"plano 2, camera\.de: esperado \[x, y\]"):
            parse_scene({"cenario": "x", "planos": [{"dur": 1}, {"dur": 1, "camera": {"de": [0.5, 0], "para": [1, 1]}}]})
        with self.assertRaisesRegex(SceneError, "plano 1, camera: use 'pos'"):
            parse_scene({"cenario": "x", "planos": [{"dur": 1, "camera": {"pos": [0, 0], "para": [1, 1]}}]})
        with self.assertRaisesRegex(SceneError, "curva"):
            parse_scene({"cenario": "x", "planos": [{"dur": 1, "camera": {"para": [1, 1], "curva": "mola"}}]})
        with self.assertRaisesRegex(SceneError, "transicoes.entrada"):
            parse_scene({"cenario": "x", "planos": [{"dur": 1}], "transicoes": {"entrada": "persiana"}})
        with self.assertRaisesRegex(SceneError, "plano 1, transicao"):
            parse_scene({"cenario": "x", "planos": [{"dur": 1, "transicao": "fade"}]})

    def test_resolution_formats(self):
        self.assertEqual(parse_resolution("hd", PRESETS), (320, 180))
        self.assertEqual(parse_resolution("GBA", PRESETS), (240, 160))
        self.assertEqual(parse_resolution("256x224", PRESETS), (256, 224))
        self.assertEqual(parse_resolution([480, 270], PRESETS), (480, 270))
        with self.assertRaisesRegex(SceneError, "Disponíveis: gba"):
            parse_resolution("cinemascope", PRESETS)
        with self.assertRaises(SceneError):
            parse_resolution([0, 10], PRESETS)


class TimelineTests(unittest.TestCase):
    def setUp(self):
        self.root = tmpdir()
        png(self.root / "fundo.png", 64, 8)

    def test_frame_count_does_not_accumulate_error(self):
        self.assertEqual(shot_ranges([1, 0.5, 2.25], 12), [(0, 12), (12, 18), (18, 45)])
        self.assertEqual(shot_ranges([0.01], 12), [(0, 1)])          # mínimo 1 quadro
        tl = timeline({"cenario": "fundo", "planos": [{"dur": 1}, {"dur": 0.55}]}, self.root)
        self.assertEqual(tl.frame_count, 16)
        self.assertEqual([f.shot for f in tl.frames].count(2), 6)
        self.assertEqual(tl.at(1.0).shot, 2)
        self.assertEqual(tl.at(tl.duration).index, 15)
        with self.assertRaises(ValueError):
            tl.at(5)

    def test_linear_and_smooth_camera(self):
        tl = timeline({"cenario": "fundo", "planos": [
            {"dur": 1.1, "camera": {"de": [0, 0], "para": [40, 0]}},
            {"dur": 1.1, "camera": {"de": [0, 0], "para": [40, 0], "curva": "suave"}},
            {"dur": 0.5}]}, self.root)
        linear = [f.camera[0] for f in tl.frames[:11]]
        self.assertEqual(linear, [0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40])
        smooth = [f.camera[0] for f in tl.frames[11:22]]
        self.assertEqual((smooth[0], smooth[5], smooth[10]), (0, 20, 40))
        self.assertLess(smooth[1], linear[1])                      # começa devagar
        self.assertEqual({f.camera for f in tl.frames[22:]}, {(40, 0)})  # câmera persiste

    def test_camera_is_clamped_to_backdrop(self):
        tl = timeline({"cenario": "fundo", "planos": [
            {"dur": 0.2, "camera": {"pos": [500, 9]}},
            {"dur": 0.2, "camera": {"pos": [-5, 0]}}]}, self.root)
        self.assertEqual(tl.frames[0].camera, (48, 0))             # 64 - 16
        self.assertEqual(tl.frames[-1].camera, (0, 0))

    def test_backdrop_change_resets_camera(self):
        png(self.root / "outro.png", 32, 8, (0, 0, 255, 255))
        tl = timeline({"cenario": "fundo", "planos": [
            {"dur": 0.2, "camera": {"pos": [30, 0]}},
            {"dur": 0.2, "cenario": "outro"}]}, self.root)
        self.assertEqual(tl.frames[0].camera, (30, 0))
        self.assertEqual(tl.frames[-1].camera, (0, 0))
        self.assertEqual(tuple(render_frame(tl, tl.frames[-1])[0, 0]), (0, 0, 255))

    def test_fades_in_steps(self):
        tl = timeline({"cenario": "fundo", "planos": [{"dur": 1}, {"dur": 1, "transicao": "fade-branco"}],
                       "transicoes": {"entrada": {"tipo": "fade", "dur": 0.4}, "saida": "fade"}}, self.root)
        amounts = [f.fade[1] if f.fade else 0 for f in tl.frames]
        self.assertEqual(amounts[:5], [1.0, 0.75, 0.5, 0.25, 0])
        self.assertTrue(set(amounts) <= {0, 0.25, 0.5, 0.75, 1.0})
        self.assertEqual(tl.frames[9].fade, ((255, 255, 255), 1.0))  # último quadro do plano 1
        self.assertEqual(tl.frames[10].fade, ((255, 255, 255), 1.0))  # primeiro do plano 2
        self.assertEqual(tl.frames[-1].fade, ((0, 0, 0), 1.0))
        self.assertEqual(tuple(render_frame(tl, tl.frames[0])[0, 0]), (0, 0, 0))
        self.assertEqual(tuple(render_frame(tl, tl.frames[2])[0, 0]), (128, 0, 0))  # meio caminho
        self.assertEqual(quantize(0.6, 4), 0.5)


class LibraryTests(unittest.TestCase):
    def test_resolves_relative_to_script_then_art_dir(self):
        root = tmpdir()
        art = root / "art"
        png(art / "cenarios" / "patio.png", 8, 8, (0, 255, 0, 255))
        png(root / "cenas" / "local.png", 8, 8, (0, 0, 255, 255))
        (art / "cenarios" / "spec.json").write_text(
            '{"palette": {"r": "#ff0000"}, "pixels": ["rr", "rr"]}', encoding="utf-8")
        lib = Library(art)
        self.assertEqual(lib.resolve("cenarios/patio", root / "cenas").name, "patio.png")
        self.assertEqual(lib.resolve("local", root / "cenas").name, "local.png")
        self.assertEqual(lib.resolve("cenarios/spec.json", None).name, "spec.json")
        self.assertEqual(lib.backdrop("cenarios/spec", None).size, (2, 2))
        with self.assertRaisesRegex(FileNotFoundError, "arte 'nada' não encontrada"):
            lib.resolve("nada", root / "cenas")

    def test_layered_backdrop_file(self):
        root = tmpdir()
        png(root / "ceu.png", 10, 8)
        png(root / "chao.png", 40, 4, (0, 255, 0, 255))
        (root / "vale.json").write_text(json.dumps({"camadas": [
            {"arte": "ceu", "parallax": 0.2, "repetir": "x"},
            {"arte": "chao", "pos": [0, 4]}]}), encoding="utf-8")
        backdrop = Library().backdrop("vale", root)
        self.assertEqual(backdrop.size, (40, 8))
        self.assertEqual(len(backdrop.layers), 2)
        (root / "ruim.json").write_text('{"camadas": [{"arte": "ceu", "brilho": 2}]}', encoding="utf-8")
        with self.assertRaisesRegex(SceneError, r"ruim.json: camada 1 \('ceu'\): campo 'brilho'.*parallax"):
            Library().backdrop("ruim", root)


class ComposeTests(unittest.TestCase):
    def setUp(self):
        self.root = tmpdir()
        png(self.root / "ceu.png", 32, 8, (0, 0, 80, 255), {(10, 0): (255, 255, 0, 255)})
        png(self.root / "chao.png", 64, 8, (0, 0, 0, 0), {(20, 7): (0, 255, 0, 255)})

    def frame_at_camera(self, layers: list, x: int) -> np.ndarray:
        tl = timeline({"cenario": {"size": [64, 8], "camadas": layers},
                       "planos": [{"dur": 0.1, "camera": {"pos": [x, 0]}}]}, self.root, (24, 8))
        return render_frame(tl, tl.frames[0])

    def test_parallax_moves_layers_at_different_speeds(self):
        layers = [{"arte": "ceu", "parallax": 0.5}, {"arte": "chao"}]
        frame = self.frame_at_camera(layers, 10)
        self.assertEqual(tuple(frame[0, 5]), (255, 255, 0))       # 10 - 10 × 0.5
        self.assertEqual(tuple(frame[7, 10]), (0, 255, 0))        # 20 - 10 × 1.0
        self.assertEqual(tuple(frame[7, 11]), (0, 0, 80))         # chão transparente mostra o céu

    def test_repeat_and_front_order(self):
        layers = [{"arte": "chao", "frente": True}, {"arte": "ceu", "parallax": 2, "repetir": "x"}]
        frame = self.frame_at_camera(layers, 12)
        # céu: marcador em 10 - 24 = -14 → repete a cada 32 px → x = 18
        self.assertEqual(tuple(frame[0, 2]), (0, 0, 80))
        self.assertEqual(tuple(frame[0, 18]), (255, 255, 0))
        self.assertEqual(tuple(frame[7, 8]), (0, 255, 0))         # frente desenhada por cima

    def test_background_color_and_animated_layer(self):
        script = self.root / "pisca.py"
        script.write_text("from pixelforge import Canvas\nFPS = 2\n"
                          "def build():\n    return [Canvas(4, 4).px(0, 0, '#ffffff'), Canvas(4, 4)]\n",
                          encoding="utf-8")
        tl = timeline({"cenario": "pisca", "fundo": "#102030", "planos": [{"dur": 1}]}, self.root)
        first, later = render_frame(tl, tl.at(0)), render_frame(tl, tl.at(0.5))
        self.assertEqual(tuple(first[0, 0]), (255, 255, 255))
        self.assertEqual(tuple(later[0, 0]), (16, 32, 48))
        self.assertEqual(tuple(first[7, 15]), (16, 32, 48))      # fora do cenário: cor de fundo

    def test_deterministic(self):
        layers = [{"arte": "ceu", "parallax": 0.5}, {"arte": "chao"}]
        self.assertTrue(np.array_equal(self.frame_at_camera(layers, 7), self.frame_at_camera(layers, 7)))


class VideoTests(unittest.TestCase):
    def setUp(self):
        self.root = tmpdir()
        self.frames = [np.full((6, 8, 3), (i * 40, 10, 200 - i * 30), np.uint8) for i in range(4)]

    def test_gif_exact_palette_and_scale(self):
        path = self.root / "a.gif"
        save_gif(self.frames, path, 12, 3)
        with Image.open(path) as im:
            self.assertEqual((im.size, im.n_frames), ((24, 18), 4))
            im.seek(2)
            self.assertEqual(im.convert("RGB").getpixel((0, 0)), (80, 10, 140))

    def test_gif_many_colors_is_quantized(self):
        ramp = np.arange(32 * 32 * 3, dtype=np.uint32).reshape(32, 32, 3) % 256
        frames = [ramp.astype(np.uint8), (255 - ramp).astype(np.uint8)]
        path = self.root / "b.gif"
        save_gif(frames, path, 12, 1)
        with Image.open(path) as im:
            self.assertEqual(im.n_frames, 2)

    def test_webp(self):
        path = self.root / "a.webp"
        save_webp(self.frames, path, 12, 2)
        with Image.open(path) as im:
            self.assertEqual((im.size, im.n_frames), ((16, 12), 4))

    @unittest.skipUnless(has_mp4(), "extra [video] (imageio-ffmpeg) não instalado")
    def test_mp4(self):
        import imageio_ffmpeg

        path = self.root / "a.mp4"
        save_mp4(self.frames * 3, path, 12, 5)
        odd = self.root / "impar.mp4"
        save_mp4([f[:5, :7] for f in self.frames], odd, 12, 1)   # 7x5 → completa para 8x6
        for file, size in ((path, (40, 30)), (odd, (8, 6))):
            reader = imageio_ffmpeg.read_frames(str(file))
            meta = next(reader)
            reader.close()
            self.assertEqual((meta["size"], meta["fps"]), (size, 12))


class SceneCliTests(unittest.TestCase):
    def setUp(self):
        self.root = tmpdir()
        (self.root / "pixelforge.toml").write_text(
            '[cena]\nresolucao = "16x8"\nescala = 2\nfps = 10\nformatos = ["gif"]\n'
            '[cena.presets]\nmini = [12, 8]\n', encoding="utf-8")
        self.cfg = str(self.root / "pixelforge.toml")
        png(self.root / "art" / "vale.png", 40, 8, (40, 90, 40, 255), {(30, 3): (255, 255, 255, 255)})
        self.script = self.root / "cenas" / "teste.json"
        self.script.parent.mkdir()
        self.script.write_text(json.dumps({
            "cenario": "vale", "transicoes": {"entrada": "fade"},
            "planos": [{"dur": 1, "camera": {"para": [24, 0]}}, {"dur": 0.5, "transicao": "fade"}]}),
            encoding="utf-8")

    def run_cli(self, *args) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(["--config", self.cfg, *args])
        return code, out.getvalue(), err.getvalue()

    def test_cena_writes_storyboard_and_gif(self):
        code, out, err = self.run_cli("cena", str(self.script))
        self.assertEqual(code, 0, err)
        folder = self.root / "out" / "teste"
        self.assertTrue((folder / "teste_storyboard.png").exists())
        with Image.open(folder / "teste.gif") as im:
            self.assertEqual(im.size, (32, 16))
        self.assertIn("15 quadros", out)

    def test_cli_overrides_and_quadro(self):
        out_dir = self.root / "saida"
        code, out, err = self.run_cli("quadro", str(self.script), "--t", "1.0", "--resolucao", "mini",
                                      "--escala", "3", "--out", str(out_dir))
        self.assertEqual(code, 0, err)
        self.assertIn("plano 2", out)
        with Image.open(out_dir / "teste_t1s.png") as im:
            self.assertEqual(im.size, (36, 24))

    def test_storyboard_and_mp4_fallback_message(self):
        code, _, err = self.run_cli("storyboard", str(self.script))
        self.assertEqual(code, 0, err)
        with Image.open(self.root / "out" / "teste" / "teste_storyboard.png") as im:
            self.assertGreater(im.width, 3 * 16)
        from unittest import mock
        with mock.patch("pixelforge.scene.has_mp4", return_value=False):
            code, out, err = self.run_cli("cena", str(self.script), "--formats", "mp4")
        self.assertEqual(code, 0, err)
        self.assertIn("extra [video]", err)
        self.assertIn("teste.gif", out)
        code, _, err = self.run_cli("cena", str(self.script), "--formats", "avi")
        self.assertEqual(code, 2)
        self.assertIn("gif, webp, mp4", err)

    def test_invalid_script_returns_2_with_location(self):
        self.script.write_text('{"cenario": "vale", "planos": [{"dur": 1, "som": {}}]}', encoding="utf-8")
        code, _, err = self.run_cli("storyboard", str(self.script))
        self.assertEqual(code, 2)
        self.assertIn("teste.json: plano 1: campo 'som'", err)

    def test_open_scene_uses_config_defaults(self):
        tl = open_scene(self.script, load_config(Path(self.cfg)))
        self.assertEqual((tl.resolution, tl.scale, tl.fps), ((16, 8), 2, 10))
        self.assertEqual(len(storyboard_rows := render_all(tl)), tl.frame_count)
        self.assertEqual(storyboard_rows[0].shape, (8, 16, 3))
        self.assertGreater(storyboard(tl).height, 0)


class ConfigTests(unittest.TestCase):
    def test_scene_defaults(self):
        cena = DEFAULTS["cena"]
        self.assertEqual((cena["resolucao"], cena["escala"], cena["fps"]), ("hd", 6, 12))
        self.assertEqual(cena["formatos"], ["gif", "mp4"])
        self.assertEqual(PRESETS["snes"], [256, 224])

    def test_cli_still_exposes_art_loaders(self):
        from pixelforge import artfile, cli
        self.assertIs(cli.load_art, artfile.load_art)


if __name__ == "__main__":
    unittest.main()
