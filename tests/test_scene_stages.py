"""Testes do motor de cena, etapas 2–4: atores, diálogo e efeitos.
Rodar: python -m unittest discover -s tests"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from pixelforge.artfile import load_art
from pixelforge.scene import Library, SceneError, Timeline, parse_scene, render_frame
from pixelforge.scene import font
from pixelforge.scene.actors import sheet_from_art
from pixelforge.scene.dialog import BORDER, plan_line
from pixelforge.scene.script import Line

RED, BLUE, GREEN = (255, 0, 0), (0, 0, 255), (0, 255, 0)
SKY = (0, 0, 80)


def tmpdir() -> Path:
    d = tempfile.TemporaryDirectory()
    unittest.addModuleCleanup(d.cleanup)
    return Path(d.name)


def write_sprite(path: Path, color: str = "#ff0000", animated: bool = True) -> Path:
    """Sprite 4x4: frame 0 cheio, frame 1 só a metade de cima, frame 2 só a coluna da esquerda."""
    spec = {"name": path.stem, "size": [4, 4], "palette": {".": "transparent", "r": color},
            "frames": [["rrrr"] * 4, ["rrrr", "rrrr", "....", "...."], ["r...", "r...", "r...", "r..."]]}
    if animated:
        spec["anchor"] = [1, 3]
        spec["animations"] = {"parado": {"frames": [0], "fps": 1}, "andar": {"frames": [1, 0], "fps": 4},
                              "falar": {"frames": [2], "fps": 1}}
    path.write_text(json.dumps(spec), encoding="utf-8")
    return path


def make(data: dict, folder: Path, resolution=(32, 16), fps: int = 10) -> Timeline:
    data = {"cenario": "fundo", **data}
    return Timeline(parse_scene(data, folder / "roteiro.json"), Library(), resolution, fps)


def setup_folder() -> Path:
    root = tmpdir()
    pixels = np.zeros((16, 64, 4), np.uint8)
    pixels[:] = (*SKY, 255)
    Image.fromarray(pixels, "RGBA").save(root / "fundo.png")
    write_sprite(root / "heroi.json")
    write_sprite(root / "azul.json", "#0000ff")
    return root


class SpriteSheetTests(unittest.TestCase):
    def setUp(self):
        self.root = setup_folder()

    def test_animations_and_anchor_from_spec(self):
        sheet = sheet_from_art(load_art(self.root / "heroi.json"))
        self.assertEqual(sheet.anchor, (1, 3))
        self.assertEqual(list(sheet.animations), ["parado", "andar", "falar"])
        self.assertEqual(sheet.frame("andar", 0.3)[3, 0, 3], 255)     # 0.3 s × 4 fps → frame 1 → 0 (cheio)
        self.assertEqual(sheet.frame("andar", 0.1)[3, 0, 3], 0)       # frame 1: metade de baixo vazia

    def test_defaults_without_animations(self):
        write_sprite(self.root / "simples.json", animated=False)
        sheet = sheet_from_art(load_art(self.root / "simples.json"))
        self.assertEqual(sheet.anchor, (2, 3))
        self.assertEqual(sheet.animations["parado"].frames, [0, 1, 2])

    def test_script_constants(self):
        script = self.root / "boneco.py"
        script.write_text("from pixelforge import Canvas\nANCHOR = [0, 1]\n"
                          "ANIMATIONS = {'parado': [0], 'pulo': {'frames': [1], 'fps': 2}}\n"
                          "def build():\n    return [Canvas(2), Canvas(2)]\n", encoding="utf-8")
        sheet = sheet_from_art(load_art(script))
        self.assertEqual((sheet.anchor, sheet.animations["pulo"].fps), ((0, 1), 2))

    def test_bad_animation_index(self):
        spec = json.loads((self.root / "heroi.json").read_text(encoding="utf-8"))
        spec["animations"]["andar"]["frames"] = [7]
        (self.root / "ruim.json").write_text(json.dumps(spec), encoding="utf-8")
        with self.assertRaisesRegex(SceneError, "andar.frames.*0 a 2"):
            sheet_from_art(load_art(self.root / "ruim.json"))


class ActorTests(unittest.TestCase):
    def setUp(self):
        self.root = setup_folder()

    def test_walk_position_animation_and_facing(self):
        tl = make({"atores": {"h": {"sprite": "heroi", "pos": [0, 10]}},
                   "planos": [{"dur": 1.5, "acoes": [{"ator": "h", "ate": [20, 10], "vel": 20}]},
                              {"dur": 1, "acoes": [{"ator": "h", "ate": [10, 10], "dur": 0.5}]}]},
                  self.root)
        view = lambda i: tl.frames[i].actors[0]  # noqa: E731
        self.assertEqual((view(5).x, view(5).anim, view(5).facing), (10, "andar", "direita"))
        self.assertEqual((view(12).x, view(12).anim), (20, "parado"))
        self.assertEqual((view(15).facing, view(17).x), ("esquerda", 16))   # 2º plano: volta
        self.assertEqual(view(24).x, 10)

    def test_walk_continues_into_next_shot(self):
        tl = make({"atores": {"h": {"sprite": "heroi", "pos": [0, 10]}},
                   "planos": [{"dur": 0.5, "acoes": [{"ator": "h", "ate": [20, 10], "vel": 20}]}, {"dur": 1}]},
                  self.root)
        self.assertEqual([tl.frames[i].actors[0].x for i in (5, 10)], [10, 20])

    def test_mirror_anchor_and_camera(self):
        tl = make({"atores": {"h": {"sprite": "heroi", "pos": [10, 10], "anim": "falar"}},
                   "planos": [{"dur": 0.1}, {"dur": 0.1, "acoes": [{"ator": "h", "olhar": "esquerda"}]}]},
                  self.root)
        right, left = render_frame(tl, tl.frames[0]), render_frame(tl, tl.frames[1])
        # coluna do sprite fica no x da âncora; espelhado, a âncora vira 4-1-1 = 2
        self.assertEqual(tuple(right[7, 9]), RED)       # 10 - 1
        self.assertEqual(tuple(right[7, 10]), SKY)
        self.assertEqual(tuple(left[7, 11]), RED)       # 10 - 2 + 3
        self.assertEqual(tuple(left[7, 9]), SKY)

    def test_depth_order_by_y(self):
        tl = make({"atores": {"baixo": {"sprite": "heroi", "pos": [10, 12]},
                              "cima": {"sprite": "azul", "pos": [10, 11]}},
                   "planos": [{"dur": 0.1}]}, self.root)
        frame = render_frame(tl, tl.frames[0])
        self.assertEqual(tuple(frame[10, 9]), RED)       # o de y maior fica na frente

    def test_appear_with_fade_is_dithered(self):
        tl = make({"atores": {"h": {"sprite": "heroi", "pos": [10, 10], "visivel": False}},
                   "planos": [{"dur": 2, "acoes": [{"ator": "h", "aparecer": True, "fade": 1}]}]}, self.root)
        self.assertEqual(tl.frames[0].actors[0].alpha, 0)
        half = render_frame(tl, tl.frames[5])[7:11, 9:13]
        reds = int(np.all(half == RED, axis=-1).sum())
        self.assertTrue(0 < reds < 16, reds)
        self.assertEqual(int(np.all(render_frame(tl, tl.frames[15])[7:11, 9:13] == RED, axis=-1).sum()), 16)

    def test_vanish(self):
        tl = make({"atores": {"h": {"sprite": "heroi", "pos": [10, 10]}},
                   "planos": [{"dur": 1, "acoes": [{"ator": "h", "inicio": 0.5, "sumir": True}]}]}, self.root)
        self.assertEqual((len(tl.frames[4].actors), len(tl.frames[5].actors)), (1, 0))

    def test_follow_zoom_and_shake(self):
        tl = make({"atores": {"h": {"sprite": "heroi", "pos": [40, 10]}},
                   "planos": [{"dur": 0.5, "camera": {"seguir": "h"}},
                              {"dur": 0.5, "camera": {"zoom": 2, "pos": [0, 0]}},
                              {"dur": 1, "camera": {"pos": [10, 0], "tremor": [2, 0.5]}}]}, self.root)
        self.assertEqual(tl.frames[0].camera, (24, 0))                  # 40 - 32/2
        zoomed = render_frame(tl, tl.frames[5])
        self.assertEqual(zoomed.shape, (16, 32, 3))
        self.assertEqual(tl.frames[5].zoom, 2)
        shakes = [tl.frames[i].shake for i in range(10, 20)]
        self.assertTrue(any(s != (0, 0) for s in shakes[:5]))
        self.assertTrue(all(abs(s[0]) <= 2 and abs(s[1]) <= 2 for s in shakes))
        self.assertEqual(shakes[5:], [(0, 0)] * 5)

    def test_errors(self):
        with self.assertRaisesRegex(SceneError, r"plano 1, acao 1\.ator: 'zé' não existe"):
            make({"atores": {"h": {"sprite": "heroi", "pos": [0, 0]}},
                  "planos": [{"dur": 1, "acoes": [{"ator": "zé", "anim": "andar"}]}]}, self.root)
        with self.assertRaisesRegex(SceneError, r"plano 1, acao 1: animação 'correr' não existe em 'heroi'"):
            make({"atores": {"h": {"sprite": "heroi", "pos": [0, 0]}},
                  "planos": [{"dur": 1, "acoes": [{"ator": "h", "anim": "correr"}]}]}, self.root)
        with self.assertRaisesRegex(SceneError, "inicio 3 s passa do fim do plano"):
            make({"atores": {"h": {"sprite": "heroi", "pos": [0, 0]}},
                  "planos": [{"dur": 1, "acoes": [{"ator": "h", "inicio": 3, "anim": "andar"}]}]}, self.root)
        with self.assertRaisesRegex(SceneError, "camera.seguir"):
            make({"planos": [{"dur": 1, "camera": {"seguir": "ninguem"}}]}, self.root)


class FontTests(unittest.TestCase):
    def test_portuguese_characters_have_glyphs(self):
        for ch in "áàâãéêíóôõúüçÁÀÂÃÉÊÍÓÔÕÚÇ—…«»“”":
            self.assertIsNot(font.glyph(ch), font.FALLBACK, ch)
        self.assertIs(font.glyph("☃"), font.FALLBACK)

    def test_width_wrap_and_draw(self):
        self.assertEqual(font.text_width("Ab"), 5 + 1 + 5)
        self.assertEqual(font.text_width("a b", 2), (5 + 1 + 3 + 1 + 5) * 2)
        lines = font.wrap("uma frase com várias palavras", 40)
        self.assertGreater(len(lines), 1)
        self.assertTrue(all(font.text_width(l) <= 40 for l in lines))
        canvas = np.zeros((14, 10, 3), np.uint8)
        font.draw_text(canvas, 1, 3, "Á", (255, 255, 255))
        self.assertTrue(canvas[1:3].any())                      # acento acima da maiúscula
        self.assertTrue(canvas[3:10].any())


class DialogTests(unittest.TestCase):
    def setUp(self):
        self.root = setup_folder()

    def test_pages_and_timing(self):
        line = Line(text="palavra " * 40, where="x", speed=20, pause=0.5, hold=1.0)
        plan = plan_line(line, (320, 180), None)
        self.assertGreater(len(plan.pages), 1)
        first = plan.pages[0]
        self.assertAlmostEqual(first.typed, first.chars / 20)
        self.assertAlmostEqual(plan.pages[1].start, first.typed + 0.5)
        self.assertAlmostEqual(plan.total, plan.pages[-1].typed + 1.0)

    def test_shot_duration_typewriter_and_talking(self):
        tl = make({"atores": {"h": {"sprite": "heroi", "pos": [10, 15]}},
                   "planos": [{"dialogo": {"ator": "h", "texto": "Olá, mundo!", "velocidade": 10}}]},
                  self.root, resolution=(160, 90))
        self.assertEqual(tl.frame_count, round((11 / 10 + 1.5) * 10))
        self.assertEqual(tl.frames[5].dialog.visible, 5)
        self.assertEqual(tl.frames[5].actors[0].anim, "falar")
        self.assertEqual(tl.frames[20].actors[0].anim, "parado")    # texto pronto: para de falar
        self.assertEqual(tl.frames[5].dialog.plan.line.label, "H")
        frame = render_frame(tl, tl.frames[12])
        self.assertTrue(np.all(frame[-5, 5:-5] == BORDER, axis=-1).all())   # borda de baixo da caixa (sem os cantos)
        self.assertEqual(tuple(frame[2, 80]), (0, 0, 0))                   # topo livre (fundo)

    def test_portrait_and_top_position(self):
        pixels = np.zeros((12, 12, 4), np.uint8)
        pixels[:] = (0, 255, 0, 255)
        Image.fromarray(pixels, "RGBA").save(self.root / "rosto.png")
        tl = make({"planos": [{"dur": 2, "dialogo": [
            {"texto": "Primeira.", "retrato": "rosto", "posicao": "cima", "nome": "Ana"},
            {"texto": "Segunda.", "inicio": 1.5}]}]}, self.root, resolution=(160, 90))
        top = render_frame(tl, tl.frames[3])
        self.assertTrue(np.all(top[:30] == GREEN, axis=-1).any())          # retrato no alto
        self.assertEqual(tl.frames[16].dialog.plan.line.text, "Segunda.")

    def test_dialog_validation(self):
        with self.assertRaisesRegex(SceneError, "dialogo.texto: obrigatório"):
            parse_scene({"cenario": "x", "planos": [{"dialogo": {"ator": None}}]})
        with self.assertRaisesRegex(SceneError, "plano 1, dur: obrigatório"):
            parse_scene({"cenario": "x", "planos": [{}]})


class EffectTests(unittest.TestCase):
    def setUp(self):
        self.root = tmpdir()
        pixels = np.zeros((90, 160, 4), np.uint8)
        pixels[:] = (100, 120, 140, 255)
        Image.fromarray(pixels, "RGBA").save(self.root / "fundo.png")

    def frames(self, effect: dict, times=(0.0, 0.5)) -> list[np.ndarray]:
        tl = make({"planos": [{"dur": 1, "efeitos": [effect]}]}, self.root, resolution=(160, 90))
        return [render_frame(tl, tl.at(t)) for t in times]

    def test_every_effect_changes_the_frame_deterministically(self):
        plain = np.full((90, 160, 3), (100, 120, 140), np.uint8)
        for effect in ({"tipo": "chuva", "intensidade": 1}, {"tipo": "neblina"},
                       {"tipo": "particulas", "estilo": "neve", "quantidade": 40},
                       {"tipo": "particulas", "estilo": "brasas"}, {"tipo": "particulas", "estilo": "folhas"},
                       {"tipo": "particulas", "estilo": "vagalumes"}, {"tipo": "particulas", "estilo": "poeira"},
                       {"tipo": "tinta", "modo": "sepia"}, {"tipo": "luz", "pos": [80, 45]},
                       {"tipo": "flash"}, {"tipo": "vinheta"}):
            with self.subTest(effect=effect["tipo"] + effect.get("estilo", "")):
                first, _ = self.frames(effect)
                self.assertFalse(np.array_equal(first, plain))
                self.assertTrue(np.array_equal(first, self.frames(effect)[0]))

    def test_moving_effects_change_over_time(self):
        for effect in ({"tipo": "chuva"}, {"tipo": "particulas", "estilo": "neve"}):
            a, b = self.frames(effect)
            self.assertFalse(np.array_equal(a, b))

    def test_effect_semantics(self):
        night, = self.frames({"tipo": "tinta", "modo": "noite"}, (0,))
        self.assertLess(int(night[45, 80].sum()), 360)
        light, = self.frames({"tipo": "luz", "pos": [80, 45], "raio": 10, "piscar": 0}, (0,))
        self.assertGreater(int(light[45, 80].sum()), 360)
        self.assertEqual(tuple(light[5, 5]), (100, 120, 140))
        flash = self.frames({"tipo": "flash", "dur": 0.3}, (0, 0.5))
        self.assertEqual(tuple(flash[0][0, 0]), (255, 255, 255))
        self.assertEqual(tuple(flash[1][0, 0]), (100, 120, 140))
        vignette, = self.frames({"tipo": "vinheta", "intensidade": 1}, (0,))
        self.assertLess(int(vignette[0, 0].sum()), int(vignette[45, 80].sum()))
        late = self.frames({"tipo": "flash", "inicio": 0.5}, (0.2,))[0]
        self.assertEqual(tuple(late[0, 0]), (100, 120, 140))

    def test_scene_level_effects_and_validation(self):
        tl = make({"efeitos": [{"tipo": "tinta", "modo": "noite"}], "planos": [{"dur": 0.5}, {"dur": 0.5}]},
                  self.root, resolution=(160, 90))
        self.assertTrue(all(len(f.effects) == 1 for f in tl.frames))
        with self.assertRaisesRegex(SceneError, "plano 1, efeitos\\[1\\].tipo: 'tornado'"):
            parse_scene({"cenario": "x", "planos": [{"dur": 1, "efeitos": [{"tipo": "tornado"}]}]})
        with self.assertRaisesRegex(SceneError, "luz precisa de 'pos'"):
            parse_scene({"cenario": "x", "planos": [{"dur": 1, "efeitos": [{"tipo": "luz"}]}]})
        with self.assertRaisesRegex(SceneError, "intensidade: esperado número entre 0 e 1"):
            parse_scene({"cenario": "x", "efeitos": [{"tipo": "chuva", "intensidade": 3}], "planos": [{"dur": 1}]})
        with self.assertRaisesRegex(SceneError, "campo 'raio' desconhecido.*chuva"):
            parse_scene({"cenario": "x", "efeitos": [{"tipo": "chuva", "raio": 3}], "planos": [{"dur": 1}]})


class CurtainTests(unittest.TestCase):
    def test_curtain_closes_from_the_sides(self):
        root = tmpdir()
        pixels = np.zeros((90, 160, 4), np.uint8)
        pixels[:] = (100, 120, 140, 255)
        Image.fromarray(pixels, "RGBA").save(root / "fundo.png")
        tl = make({"planos": [{"dur": 1}, {"dur": 1, "transicao": {"tipo": "cortina", "cor": "#102030"}}]},
                  root, resolution=(160, 90))
        mid = tl.frames[7]
        self.assertEqual(mid.transition, "cortina")
        frame = render_frame(tl, mid)
        self.assertEqual(tuple(frame[45, 0]), (16, 32, 48))
        self.assertEqual(tuple(frame[45, 159]), (16, 32, 48))
        self.assertEqual(tuple(frame[45, 80]), (100, 120, 140))
        closed = render_frame(tl, tl.frames[9])
        self.assertTrue(np.all(closed == (16, 32, 48)))


if __name__ == "__main__":
    unittest.main()
