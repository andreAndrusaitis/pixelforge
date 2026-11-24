"""Testes do vídeo/animação por IA (pixelforge.ai_video) e da integração `"ia"` na cena.

A pixelização temporal e a integração rodam sempre, com um gerador falso; a geração
real com o Wan 2.2 só com o extra [video-ia], os pesos baixados e PIXELFORGE_TESTES_IA=1.
Rodar: python -m unittest discover -s tests"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
from PIL import Image

from pixelforge.ai_video import clips
from pixelforge.ai_video.pixelize import (PixelizeOptions, downscale, flicker, key_alpha, palette_of,
                                          pixelize_clip, quantize, remove_orphans, resample_times,
                                          temporal_median)
from pixelforge.ai_video.sprite import key_color, save_animated, SpriteAnimation
from pixelforge.artfile import load_art
from pixelforge.scene import Library, SceneError, Timeline, parse_scene, render_frame
from pixelforge.scene.ai import has_ai, prepare
from pixelforge.scene.library import loop_index

SKY, GRASS, SUN = (40, 60, 120), (30, 90, 40), (230, 200, 90)


def tmpdir() -> Path:
    d = tempfile.TemporaryDirectory()
    unittest.addModuleCleanup(d.cleanup)
    return Path(d.name)


class FakeGenerator:
    """Faz o papel do Wan: devolve a imagem ampliada com um sol amarelo andando para a direita."""

    def __init__(self, rows=(1 / 8, 1 / 4)):
        self.calls = 0
        self.rows = rows

    def generate(self, image, prompt, seconds, seed, long_side):
        self.calls += 1
        base = np.asarray(image.convert("RGB"))
        n = int(round(seconds * 24)) // 4 * 4 + 1
        h, w = base.shape[:2]
        out = []
        for i in range(n):
            f = base.copy()
            x = int(i / n * w * 0.5)
            f[int(h * self.rows[0]):int(h * self.rows[1]), x:x + w // 8] = SUN
            out.append(f)
        return out, clips_timing()


def clips_timing():
    from pixelforge.ai_video.wan import Timing
    return Timing(sample=1.0)


class PixelizeTests(unittest.TestCase):
    def test_resample_and_grid(self):
        self.assertEqual(resample_times(48, 24, 12), list(range(0, 48, 2)))
        self.assertEqual(len(resample_times(49, 24, 8)), 16)
        frame = np.zeros((100, 200, 3), np.uint8)
        frame[:, :100] = 255
        small = downscale(frame, (20, 10))
        self.assertEqual(small.shape, (10, 20, 3))
        self.assertTrue((small[:, :10] == 255).all() and (small[:, 10:] == 0).all())   # grade fixa, sem borrar
        wide = downscale(np.zeros((90, 400, 3), np.uint8), (16, 9))                      # recorta a proporção
        self.assertEqual(wide.shape, (9, 16, 3))

    def test_temporal_median_removes_one_frame_spikes(self):
        frames = np.zeros((5, 4, 4, 3), np.uint8)
        frames[2, 1, 1] = 255
        self.assertEqual(int(temporal_median(frames, 3).max()), 0)

    def test_palette_is_locked_and_hysteresis_kills_flicker(self):
        rng = np.random.default_rng(1)
        palette = np.array([SKY, GRASS, (35, 75, 80)], np.uint8)
        mid = ((np.array(SKY) + np.array((35, 75, 80))) / 2).astype(np.int16)
        frames = np.stack([np.clip(mid + rng.integers(-6, 7, (8, 8, 3)), 0, 255).astype(np.uint8)
                           for _ in range(12)])
        loose = palette[quantize(frames, palette, hysteresis=0.0, cleanup=False)]
        stable = palette[quantize(frames, palette)]
        self.assertGreater(flicker(list(loose)), 0.2)
        self.assertLess(flicker(list(stable)), flicker(list(loose)) / 4)
        colors = {tuple(c) for c in stable.reshape(-1, 3)}
        self.assertTrue(colors <= {tuple(c) for c in palette})

    def test_orphans(self):
        idx = np.zeros((5, 5), np.int32)
        idx[2, 2] = 1
        idx[0, 0:2] = 2                     # par: não é órfão
        out = remove_orphans(idx)
        self.assertEqual(out[2, 2], 0)
        self.assertEqual(list(out[0, :2]), [2, 2])

    def test_region_and_base_keep_the_rest_identical(self):
        base = np.zeros((9, 16, 3), np.uint8)
        base[:] = SKY
        base[5:] = GRASS
        clip = [np.kron(base, np.ones((8, 8, 1), np.uint8)) for _ in range(6)]
        for f in clip[3:]:
            f[:] = SUN                      # a IA "estragou" tudo na segunda metade
        region = np.zeros((9, 16), bool)
        region[:4] = True
        out = pixelize_clip(clip, PixelizeOptions((16, 9), 24, 12, palette=palette_of(base), median=1),
                            base=base, region=region)
        for f in out:
            np.testing.assert_array_equal(f[4:], base[4:])
        self.assertTrue((out[0] == base).all())          # começa igual ao quadro original

    def test_only_moving_pixels_are_repainted_keeping_dither(self):
        base = np.zeros((8, 16, 3), np.uint8)
        base[:] = SKY
        base[::2, ::2] = (60, 80, 140)                     # dithering do artista
        smooth = np.asarray(Image.fromarray(base).resize((16, 8), Image.BOX))
        clip = []
        for i in range(12):
            f = np.kron(base, np.ones((8, 8, 1), np.uint8))
            f = np.asarray(Image.fromarray(f).resize((128, 64), Image.BILINEAR))   # a IA não dá dithering
            f = f.copy()
            f[:, i * 8:i * 8 + 16] = SUN                   # algo atravessando
            clip.append(f)
        pal = np.unique(np.concatenate([palette_of(base), np.array([SUN], np.uint8)]), axis=0)
        out = pixelize_clip(clip, PixelizeOptions((16, 8), 24, 24, palette=pal, median=1), base=base)
        last = out[-1]
        np.testing.assert_array_equal(last[:, :8], base[:, :8])          # por onde passou: original de volta
        self.assertTrue((last[:, 11:13] == SUN).all())                    # onde está agora: repintado
        self.assertEqual(smooth.shape, base.shape)

    def test_key_alpha_for_sprites(self):
        frames = np.zeros((3, 4, 4, 3), np.uint8)
        frames[:] = (0, 177, 64)
        frames[:, 1:3, 1:3] = (200, 50, 50)
        alpha = key_alpha(frames, (0, 177, 64))
        self.assertEqual(int(alpha[0].sum()), 4)
        self.assertEqual(key_color(np.array([(0, 170, 60), (10, 180, 70)])), (255, 0, 255))

    def test_loop_modes(self):
        self.assertEqual([loop_index(i, 4, "repetir") for i in range(6)], [0, 1, 2, 3, 0, 1])
        self.assertEqual([loop_index(i, 4, "vaivem") for i in range(8)], [0, 1, 2, 3, 2, 1, 0, 1])
        self.assertEqual([loop_index(i, 4, "segurar") for i in range(6)], [0, 1, 2, 3, 3, 3])


class ClipTests(unittest.TestCase):
    def setUp(self):
        self.cache = tmpdir()
        self.image = np.zeros((18, 32, 3), np.uint8)
        self.image[:] = SKY
        self.image[12:] = GRASS
        self.image[2:5, 2:6] = SUN

    def test_cache_by_hash(self):
        gen = FakeGenerator()
        a = clips.make_clip(self.image, "sun moving", 1.0, cache_dir=self.cache, generator=gen, log=lambda m: None)
        b = clips.make_clip(self.image, "sun moving", 1.0, cache_dir=self.cache, generator=gen, log=lambda m: None)
        self.assertEqual(gen.calls, 1)
        for x, y in zip(a.frames, b.frames):
            np.testing.assert_array_equal(x, y)
        clips.make_clip(self.image, "outra coisa", 1.0, cache_dir=self.cache, generator=gen, log=lambda m: None)
        self.assertEqual(gen.calls, 2)
        self.assertEqual(len(a.frames), 12)
        self.assertGreater(a.flicker, 0)

    def test_low_score_retries_with_new_seed(self):
        gen = FakeGenerator()
        notes = iter([90.0, 70.0, 80.0, 88.0])        # imagem original, tentativa 1, 2, 3
        with mock.patch.object(clips, "technical_score", side_effect=lambda *a, **k: next(notes)):
            result = clips.make_clip(self.image, "x", 1.0, cache_dir=self.cache, generator=gen, config=object(),
                                     seed=5, log=lambda m: None)
        self.assertEqual([a["semente"] for a in result.attempts], [5, 6, 7])
        self.assertEqual((result.seed, result.score), (7, 88.0))


class SceneAITests(unittest.TestCase):
    def setUp(self):
        self.root = tmpdir()
        img = np.zeros((18, 64, 4), np.uint8)
        img[:] = (*SKY, 255)
        img[12:] = (*GRASS, 255)
        Image.fromarray(img, "RGBA").save(self.root / "fundo.png")
        spec = {"name": "heroi", "size": [4, 6], "anchor": [1, 5],
                "palette": {".": "transparent", "r": "#c03030", "w": "#f0f0f0"},
                "frames": [["rrrr", "rwwr", "rrrr", "rrrr", "r..r", "r..r"]]}
        (self.root / "heroi.json").write_text(json.dumps(spec), encoding="utf-8")
        (self.root / "cenario.json").write_text(json.dumps({"size": [64, 18], "camadas": [
            {"arte": "fundo", "ia": {"movimento": "clouds", "dur": 1}}]}), encoding="utf-8")

    def make(self, data: dict) -> Timeline:
        data = {"cenario": "fundo", "atores": {"h": {"sprite": "heroi", "pos": [10, 16]}}, **data}
        library = Library()
        tl = Timeline(parse_scene(data, self.root / "roteiro.json"), library, (32, 18), 12)
        tl.library = library
        return tl

    def test_parse_errors(self):
        cases = [({"origem": "sprite", "movimento": "x"}, "com origem sprite, diga qual ator"),
                 ({"origem": "foto", "movimento": "x"}, "origem: 'foto' inválido"),
                 ({"origem": "quadro"}, "movimento: esperado texto"),
                 ({"movimento": "x", "regiao": [[0, 0, 0, 4]]}, r"regiao\[1\]"),
                 ({"movimento": "x", "imagem": "a.png"}, "só vale com \"origem\": \"imagem\"")]
        for ai, message in cases:
            with self.subTest(ai=ai), self.assertRaisesRegex(SceneError, message):
                self.make({"planos": [{"dur": 1, "ia": ai}]})

    def test_quadro_clip_replaces_world_and_is_cached(self):
        tl = self.make({"planos": [{"dur": 1}, {"dur": 2, "ia": {"movimento": "sun", "dur": 1,
                                                                 "regiao": [[0, 0, 32, 9]]}}]})
        self.assertTrue(has_ai(tl))
        before = render_frame(tl, tl.at(1.9))
        gen = FakeGenerator()
        reports, warnings = prepare(tl, tl.library, None, cache_dir=self.root / "_ia", generator=gen, log=lambda m: None)
        self.assertEqual((len(reports), warnings, gen.calls), (1, [], 1))
        self.assertEqual(len(tl.ai_clips[2]), 12)
        a, b = render_frame(tl, tl.at(1.1)), render_frame(tl, tl.at(1.9))
        self.assertFalse((a == b).all())                                  # anima
        np.testing.assert_array_equal(b[9:], before[9:])                  # fora da região, igual
        np.testing.assert_array_equal(render_frame(tl, tl.at(2.5)), render_frame(tl, tl.at(2.95)))   # segura
        np.testing.assert_array_equal(render_frame(tl, tl.at(0.5)), render_frame(tl, tl.frames[0]))
        tl2 = self.make({"planos": [{"dur": 1}, {"dur": 2, "ia": {"movimento": "sun", "dur": 1,
                                                                  "regiao": [[0, 0, 32, 9]]}}]})
        prepare(tl2, tl2.library, None, cache_dir=self.root / "_ia", generator=gen, log=lambda m: None)
        self.assertEqual(gen.calls, 1)                                    # do cache

    def test_sprite_origin_animates_only_the_actor(self):
        tl = self.make({"planos": [{"dur": 2, "ia": {"origem": "sprite", "ator": "h", "movimento": "wave",
                                                     "dur": 1}}]})
        prepare(tl, tl.library, None, cache_dir=self.root / "_ia", generator=FakeGenerator((0.7, 1.0)),
                log=lambda m: None)
        frames = tl.ai_clips[1]
        self.assertEqual(frames[0].shape, (6, 4, 4))
        self.assertEqual(len({f.tobytes() for f in frames}) > 1, True)
        frame = render_frame(tl, tl.at(0.9))
        self.assertEqual(tuple(frame[1, 30]), SKY)                        # cenário intacto

    def test_layer_ai_and_fallback_without_ai(self):
        tl = self.make({"cenario": "cenario", "planos": [{"dur": 2}]})
        reports, warnings = prepare(tl, tl.library, None, cache_dir=self.root / "_ia", use_ai=False,
                                    log=lambda m: None)
        self.assertEqual(reports, [])
        self.assertIn("--sem-ia", warnings[0])
        layer = tl.frames[0].backdrop.layers[0]
        self.assertEqual(len(layer.frames), 1)
        prepare(tl, tl.library, None, cache_dir=self.root / "_ia", generator=FakeGenerator(), log=lambda m: None)
        self.assertEqual((len(layer.frames), layer.loop), (12, "vaivem"))
        self.assertEqual(layer.frames[0].shape[-1], 4)


class SpriteSaveTests(unittest.TestCase):
    def test_saved_spec_has_animations_and_anchor(self):
        root = tmpdir()
        spec = {"name": "s", "size": [2, 2], "anchor": [1, 1], "palette": {"r": "#ff0000"},
                "frames": [["rr", "rr"]]}
        (root / "s.json").write_text(json.dumps(spec), encoding="utf-8")
        art = load_art(root / "s.json")
        frame = np.zeros((2, 2, 4), np.uint8)
        frame[0] = (255, 0, 0, 255)
        out = save_animated(art, [SpriteAnimation("andar", [frame, frame], 8, 3, 90.0)], root / "s_ia.json")
        again = load_art(out)
        self.assertEqual(again.meta["anchor"], [1, 1])
        self.assertEqual(again.meta["animations"]["andar"], {"frames": [1, 2], "fps": 8})
        self.assertEqual(len(again.frames), 3)


@unittest.skipUnless(os.environ.get("PIXELFORGE_TESTES_IA") == "1", "geração real: PIXELFORGE_TESTES_IA=1")
class WanTests(unittest.TestCase):
    def test_generate_short_clip(self):
        from pixelforge.ai_video.wan import WanI2V, dependencies_ok, installed
        if not (dependencies_ok() and installed()):
            self.skipTest("extra [video-ia] ou pesos ausentes")
        image = Image.new("RGB", (64, 36), SKY)
        frames, timing = WanI2V(steps=4).generate(image, "clouds drifting", 0.5, 0, long_side=320)
        self.assertGreaterEqual(len(frames), 9)
        self.assertEqual(frames[0].shape[2], 3)


if __name__ == "__main__":
    unittest.main()
