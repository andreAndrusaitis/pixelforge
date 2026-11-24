"""Testes do motor de arte: paleta, sombra, lint, animação, personagem, tiles, Aseprite.

Rodar: python -m unittest discover -s tests
"""

from __future__ import annotations

import io
import json
import struct
import tempfile
import unittest
import zlib
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import numpy as np
from PIL import Image

from pixelforge import Art, Canvas, Sprite, load_spec, save_spec
from pixelforge import animate, aseprite, character, lint, recolor, shading, tiles
from pixelforge.cli import main
from pixelforge.color import srgb_to_oklab

RED, BLUE, BLACK, WHITE = (255, 0, 0, 255), (0, 0, 255, 255), (0, 0, 0, 255), (255, 255, 255, 255)
GREEN = (56, 183, 100, 255)


def tmpdir() -> Path:
    d = tempfile.TemporaryDirectory()
    unittest.addModuleCleanup(d.cleanup)
    return Path(d.name)


def L(color) -> float:
    return float(srgb_to_oklab(np.array(color[:3]))[0])


def run_cli(*argv) -> tuple[int, str]:
    out = io.StringIO()
    with redirect_stdout(out):
        code = main([str(a) for a in argv])
    return code, out.getvalue()


def square(size=12, color=GREEN, pad=2) -> Sprite:
    s = Sprite.blank(size + 2 * pad)
    s.pixels[pad:pad + size, pad:pad + size] = color
    return s


MODEL = {
    "tipo": "personagem", "name": "teste",
    "camadas": {"cabelo": {"estilo": "rabo", "franja": "lado"}, "roupa": {"estilo": "casaco", "mangas": "longas"},
                "acessorios": ["cachecol"]},
    "paletas": {"azul": {"roupa": "#3b5dc9"}},
    "variantes": {"cicatriz": {"camadas": {"marcas": ["cicatriz"]}}, "idosa": {"idade": "idoso"}},
}


# --------------------------------------------------------------------------


class RecolorTests(unittest.TestCase):
    def test_shade_changes_lightness_and_hue(self):
        base = (180, 60, 60, 255)
        self.assertGreater(L(recolor.shade(base, 1)), L(base))
        self.assertLess(L(recolor.shade(base, -1)), L(base))
        self.assertEqual(recolor.shade(base, 0), base)
        # sombra puxa o matiz para frio (azul/roxo)
        _, _, h0 = recolor.to_lch(base)
        _, _, h1 = recolor.to_lch(recolor.shade(base, -2))
        self.assertNotAlmostEqual(h0, h1, places=0)

    def test_ramp_is_light_to_dark(self):
        r = recolor.ramp("#38b764")
        self.assertEqual(len(r), 4)
        self.assertEqual(r[1], (56, 183, 100, 255))
        lums = [L(c) for c in r]
        self.assertEqual(lums, sorted(lums, reverse=True))

    def test_swap_family_moves_whole_ramp(self):
        base = (177, 62, 83, 255)
        r = recolor.ramp(base)
        s = Sprite.blank(4, 1)
        for i, c in enumerate(r):
            s.pixels[0, i] = c
        out = recolor.recolor_sprite(s, swaps=[(base, BLUE)])
        self.assertEqual(tuple(out.pixels[0, 1]), BLUE)
        for i in (0, 2, 3):  # tons da rampa também mudaram, para azulados
            self.assertNotEqual(tuple(out.pixels[0, i]), r[i])
            self.assertGreater(out.pixels[0, i, 2], out.pixels[0, i, 0])
        # luminosidade relativa preservada
        self.assertGreater(L(out.pixels[0, 0]), L(out.pixels[0, 1]))
        self.assertLess(L(out.pixels[0, 3]), L(out.pixels[0, 2]))
        exact = recolor.recolor_sprite(s, swaps=[(base, BLUE)], keep_ramps=False)
        self.assertEqual(tuple(exact.pixels[0, 0]), r[0])

    def test_tints(self):
        s = square()
        night = recolor.apply_tint(s, "noite")
        self.assertLess(L(night.pixels[5, 5]), L(s.pixels[5, 5]))
        ghost = recolor.apply_tint(s, "fantasma")
        self.assertLess(ghost.pixels[5, 5, 3], 255)
        self.assertEqual(ghost.pixels[0, 0, 3], 0)  # transparente continua transparente
        with self.assertRaises(KeyError):
            recolor.apply_tint(s, "nada")

    def test_maps_file_and_swaps(self):
        d = tmpdir()
        path = d / "mapas.json"
        path.write_text(json.dumps({"mapas": {"azul": {"#ff0000": "#0000ff"}}}), encoding="utf-8")
        maps = recolor.load_maps(path)
        self.assertEqual(recolor.parse_swaps(maps["azul"]), [(RED, BLUE)])
        self.assertEqual(recolor.parse_swaps(["#f00:#00f"]), [(RED, BLUE)])
        with self.assertRaises(ValueError):
            recolor.parse_swaps(["#f00"])

    def test_to_palette_and_merge_close(self):
        s = Sprite.blank(2, 1)
        s.pixels[0, 0] = (250, 10, 10, 255)
        s.pixels[0, 1] = (10, 10, 240, 255)
        out = recolor.to_palette(s, [RED, BLUE])
        self.assertEqual([tuple(p) for p in out.pixels[0]], [RED, BLUE])
        a = Sprite.blank(3, 1)
        a.pixels[0, :2] = (100, 100, 100, 255)
        a.pixels[0, 2] = (101, 100, 100, 255)
        merged = recolor.merge_close([a])[0]
        self.assertEqual(len(merged.colors()), 1)


class ShadingTests(unittest.TestCase):
    def test_label_regions(self):
        s = Sprite.blank(5, 1)
        s.pixels[0, 0] = s.pixels[0, 1] = RED
        s.pixels[0, 3] = RED
        labels = shading.label_regions(s.pixels)
        self.assertEqual(labels.max(), 1)
        self.assertEqual(labels[0, 2], -1)

    def test_auto_shade_follows_light(self):
        s = square()
        out = shading.auto_shade(s, "cima-esquerda")
        top_left, bottom_right, center = out.pixels[3, 3], out.pixels[12, 12], out.pixels[7, 7]
        self.assertGreater(L(top_left), L(center))
        self.assertLess(L(bottom_right), L(center))
        flipped = shading.auto_shade(s, "baixo-direita")
        self.assertLess(L(flipped.pixels[3, 3]), L(flipped.pixels[7, 7]))
        self.assertTrue(np.array_equal(out.pixels[..., 3], s.pixels[..., 3]))

    def test_keep_colors_untouched(self):
        s = square()
        s.pixels[8, 8] = RED
        out = shading.auto_shade(s, keep=["#ff0000"])
        self.assertEqual(tuple(out.pixels[8, 8]), RED)

    def test_selout_and_outline_modes(self):
        s = square(4, GREEN, 1)
        sel = shading.outline(s, "selout")
        edge = tuple(sel.pixels[0, 2])
        self.assertEqual(edge[3], 255)
        self.assertLess(L(edge), L(GREEN))
        solid = shading.outline(s, "#000000")
        self.assertEqual(tuple(solid.pixels[0, 2]), BLACK)
        self.assertTrue(np.array_equal(shading.outline(s, "nenhum").pixels, s.pixels))

    def test_parse_light(self):
        self.assertEqual(shading.parse_light("cima-esquerda"), (-1, -1))
        self.assertEqual(shading.parse_light([3, 0]), (1, 0))
        with self.assertRaises(ValueError):
            shading.parse_light("lua")


class LintTests(unittest.TestCase):
    def test_orphan(self):
        s = square(6, GREEN, 1)
        s.pixels[3, 3] = (60, 180, 104, 255)  # quase igual ao verde
        issues = lint.check_orphans(s)
        self.assertEqual([(i.x, i.y) for i in issues], [(3, 3)])
        s.pixels[3, 3] = BLACK  # alto contraste: detalhe intencional (olho)
        self.assertEqual(lint.check_orphans(s), [])

    def test_broken_outline(self):
        s = square(8, GREEN, 2)
        outlined = shading.outline(s, "#000000")
        self.assertEqual(lint.check_outline(outlined), [])
        outlined.pixels[1, 5] = GREEN  # buraco no contorno, pintado de verde
        issues = lint.check_outline(outlined)
        self.assertEqual([(i.x, i.y) for i in issues], [(5, 1)])

    def test_too_many_colors(self):
        s = Sprite.blank(16, 2)
        for i in range(16):
            s.pixels[0, i] = (i * 15, 0, 255 - i * 15, 255)
            s.pixels[1, i] = (0, i * 15, 100, 255)
        issues = lint.check_colors(s, limit=16)
        self.assertTrue(any("32 cores" in i.message for i in issues))

    def test_jaggies(self):
        c = Canvas(12, 12)
        # borda esquerda com degraus 3-1-3
        lefts = [6, 6, 6, 5, 4, 4, 4]
        for y, x in enumerate(lefts):
            c.rect(x, y + 2, 12 - x, 1, "#38b764")
        issues = lint.check_jaggies(c.sprite)
        self.assertTrue(any(i.y == 5 and "3-1-3" in i.message for i in issues))

    def test_banding(self):
        s = Sprite.blank(12, 8)
        dark, mid, light = (40, 40, 40, 255), (120, 120, 120, 255), (220, 220, 220, 255)
        for y in range(8):
            s.pixels[y, :] = light
            s.pixels[y, : 2 + y] = dark
            s.pixels[y, 2 + y] = mid  # faixa de 1 px que acompanha a borda em diagonal
        issues = lint.check_banding(s)
        self.assertTrue(issues)

    def test_contrast_and_report(self):
        gray = square(6, (128, 128, 128, 255), 1)
        issues = lint.check_contrast(gray)
        self.assertEqual(len(issues), 1)
        self.assertEqual(lint.check_contrast(shading.outline(gray, "#000000")), [])
        text = lint.lint_report(issues)
        self.assertIn("contraste: 1", text)
        self.assertIn("(", text)
        self.assertEqual(lint.lint_report([]), "nenhum problema encontrado")
        with self.assertRaises(ValueError):
            lint.lint_sprite(gray, ["nada"])

    def test_lint_art_reports_repeated_issue_once(self):
        gray = square(6, (128, 128, 128, 255), 1)
        issues = lint.lint_art(Art("a", [gray, gray.copy()]), ["contraste"])
        self.assertEqual(len(issues), 1)


class AnimateTests(unittest.TestCase):
    def figure(self) -> Sprite:
        c = Canvas(16, 16)
        c.rect(5, 1, 6, 6, "#e8b796")    # cabeça
        c.px(7, 3, "#000000")
        c.px(9, 3, "#000000")
        c.rect(5, 7, 6, 5, "#b13e53")    # tronco
        c.rect(5, 12, 2, 4, "#333c57")   # pernas
        c.rect(9, 12, 2, 4, "#333c57")
        return c.sprite

    def test_anchor(self):
        self.assertEqual(animate.default_anchor(self.figure()), [8, 15])

    def test_generators(self):
        s = self.figure()
        up, down = animate.breathe(s, 11)
        self.assertTrue(np.array_equal(up.pixels, s.pixels))
        self.assertEqual(down.pixels[1, 5, 3], 0)       # cabeça desceu
        self.assertTrue(np.array_equal(down.pixels[15], s.pixels[15]))  # pés parados
        closed = animate.blink(s, [(7, 3), (9, 3)])
        self.assertEqual(tuple(closed.pixels[3, 7]), tuple(s.pixels[2, 7]))
        shut, opened = animate.talk(s, (7, 5, 2, 1))
        self.assertFalse(np.array_equal(shut.pixels, opened.pixels))
        frames = animate.walk(s, 12, 4)
        self.assertEqual(len(frames), 4)
        self.assertFalse(np.array_equal(frames[0].pixels, frames[2].pixels))
        self.assertEqual(len(animate.walk(s, 12, 6)), 6)
        with self.assertRaises(ValueError):
            animate.walk(s, 12, 5)

    def test_builder_dedupes_and_spec_roundtrip(self):
        s = self.figure()
        b = animate.generate(s, eyes=[(7, 3), (9, 3)], mouth=(7, 5, 2, 1), hip=12, walk_frames=4)
        art = b.art("boneco")
        animate.validate_animations(art)
        self.assertEqual(set(art.meta["animations"]), {"parado", "respirar", "piscar", "falar", "andar"})
        self.assertEqual(len(art.meta["animations"]["parado"]["frames"]), 8)
        self.assertLess(len(art.frames), 8 + 2 + 3 + 2 + 4)  # quadros repetidos reaproveitados
        path = save_spec(art, tmpdir() / "boneco.json")
        loaded = load_spec(path)
        self.assertEqual(loaded.meta["animations"], art.meta["animations"])
        self.assertEqual(loaded.meta["anchor"], [8, 15])

    def test_validate_animations(self):
        art = Art("x", [self.figure()], meta={"animations": {"a": {"frames": [0, 3], "fps": 2}}})
        with self.assertRaises(ValueError):
            animate.validate_animations(art)
        art.meta = {"anchor": [1]}
        with self.assertRaises(ValueError):
            animate.validate_animations(art)
        self.assertEqual(animate.animations_of(Art("y", [self.figure()]))["parado"]["frames"], [0])

    def test_export_animations(self):
        b = animate.generate(self.figure(), walk_frames=4)
        paths = animate.export_animations(b.art("boneco"), tmpdir())
        self.assertTrue(any(p.name == "boneco_andar.gif" for p in paths))


class PaintedStyleTests(unittest.TestCase):
    """Estilo "pintado" do gerador e o kit de pintura (paint.Paint / paint.Scene)."""

    def setUp(self):
        self.model = character.parse_model({**MODEL, "estilo": "pintado"})

    def test_defaults_and_validation(self):
        self.assertEqual(self.model.size, (64, 104))
        self.assertEqual(self.model.portrait, 112)
        with self.assertRaises(character.ModelError):
            character.parse_model({"name": "x", "estilo": "aquarela"})

    def test_sprite_keeps_animations_and_proportion(self):
        art, layers = character.build_sprite(self.model)
        for name in ("parado", "piscar", "falar", "andar", "parado_frente", "andar_costas"):
            self.assertIn(name, art.meta["animations"])
        animate.validate_animations(art)
        self.assertEqual(len(layers), len(art.frames))
        frame = art.frames[0].pixels
        ys = np.nonzero(frame[..., 3].any(axis=1))[0]
        self.assertGreaterEqual(ys.max() - ys.min() + 1, 90)          # corpo inteiro 90–140 px
        self.assertGreater(len(art.colors()), 24)                     # rampas ricas, não chapado

    def test_portrait_has_no_anime_eyes(self):
        art, _ = character.build_portrait(self.model)
        anims = art.meta["animations"]
        neutral = art.frames[anims["neutro"]["frames"][0]].pixels
        face = neutral[20:75]                                           # rosto (a camiseta branca fica abaixo)
        white = (face[..., :3].min(axis=-1) > 235) & (face[..., 3] > 0)
        self.assertEqual(int(white.sum()), 0)                           # sem esclera/brilho branco
        self.assertEqual(art.size, (112, 112))

    def test_paint_kit(self):
        from pixelforge.paint import Paint, Scene
        p = Paint(32, 32)
        p.hue_ramp("x", "#808090")
        self.assertEqual(len(p.ramps[0]), 6)
        m = p.ellipse(16, 16, 10, 10)
        p.cel(m, "x")
        p.painterly(m, edge=0.5, seed=1)
        p.rim_light(width=1)
        p.rim_light(dirs=((1, 0),), second=True)
        out = p.render(outline="seletivo").pixels
        self.assertTrue(out[..., 3].any())
        self.assertGreater(len({tuple(c) for c in out[out[..., 3] > 0][:, :3]}), 4)
        s = Scene(64, 36, seed=1)
        s.sky(["#203040", "#405060", "#a06050"], 0, 24)
        s.clouds(32, 10, 30, 6, "#ffffff", "#c0c0d0", "#8080a0")
        s.put(s.rect(0, 24, 63, 35), "#202028")
        s.reflect(24, 25, 36)
        s.glow(10, 20, 6, "#ffd080", core="#ffffff")
        s.foliage(50, 8, 8, ["#102010", "#204020"])
        s.frame("esquerda", "#000000")
        s.wire(0, 5, 63, 8, 4, "#000000")
        img = s.sprite().pixels
        self.assertTrue((img[..., 3] == 255).all())


class CharacterTests(unittest.TestCase):
    def setUp(self):
        self.model = character.parse_model(MODEL)

    def test_validation_messages(self):
        bad = [
            ({"camadas": {"cabelo": {"estilo": "moicano"}}}, "camadas.cabelo.estilo"),
            ({"idade": "bebe"}, "idade"),
            ({"expressoes": ["sono"]}, "expressoes"),
            ({"camadas": {"acessorios": ["coroa"]}}, "acessorios"),
            ({"andar": 5}, "andar"),
            ({"cores": {"pele": "#zz"}}, "pele"),
            ({"tamanho": [8, 8]}, "tamanho"),
            ({"proporcoes": {"cabeca": 30}}, "proporções"),
        ]
        for extra, word in bad:
            with self.subTest(extra=extra):
                with self.assertRaises(character.ModelError) as ctx:
                    m = character.parse_model({"name": "x", **extra})
                    character.render_body(m)
                self.assertIn(word, str(ctx.exception))

    def test_sprite_animations_and_anchor(self):
        art, layers = character.build_sprite(self.model)
        anims = art.meta["animations"]
        for name in ("parado", "piscar", "falar", "andar", "parado_frente", "andar_frente", "parado_costas",
                     "andar_costas"):
            self.assertIn(name, anims)
        self.assertEqual(len(anims["andar"]["frames"]), 4)
        self.assertEqual(art.meta["anchor"], [16, 31])
        self.assertEqual(art.size, (32, 32))
        animate.validate_animations(art)
        self.assertEqual(len(layers), len(art.frames))
        # pé encosta na última linha (âncora)
        self.assertTrue(art.frames[0].pixels[31, :, 3].any())
        six = character.parse_model({**MODEL, "andar": 6})
        self.assertEqual(len(character.build_sprite(six)[0].meta["animations"]["andar"]["frames"]), 6)

    def test_deterministic(self):
        a, _ = character.render_body(self.model, "frente")
        b, _ = character.render_body(character.parse_model(MODEL), "frente")
        self.assertTrue(np.array_equal(a.pixels, b.pixels))

    def test_views_differ_and_blink(self):
        right, _ = character.render_body(self.model, "direita")
        front, _ = character.render_body(self.model, "frente")
        back, _ = character.render_body(self.model, "costas")
        self.assertFalse(np.array_equal(right.pixels, front.pixels))
        self.assertFalse(np.array_equal(front.pixels, back.pixels))
        closed, _ = character.render_body(self.model, "frente", character.Pose(blink=True))
        diff = np.any(closed.pixels != front.pixels, axis=-1)
        ys, _ = np.nonzero(diff)
        self.assertTrue(diff.any())
        self.assertLess(ys.max(), 16)  # só o rosto muda

    def test_portrait_expressions_change_only_face(self):
        art, _ = character.build_portrait(self.model)
        anims = art.meta["animations"]
        for e in character.EXPRESSIONS:
            self.assertIn(e, anims)
            self.assertIn(f"{e}_falar", anims)
        neutral = art.frames[anims["neutro"]["frames"][0]]
        happy = art.frames[anims["feliz"]["frames"][0]]
        diff = np.any(neutral.pixels != happy.pixels, axis=-1)
        self.assertTrue(diff.any())
        ys, _ = np.nonzero(diff)
        self.assertGreater(ys.min(), 10)          # cabelo intacto
        self.assertLess(ys.max(), 36)             # roupa intacta
        self.assertEqual(art.size, (48, 48))

    def test_variants_and_palettes(self):
        data = character.resolve(MODEL, ["cicatriz"], "azul")
        self.assertEqual(data["camadas"]["marcas"], ["cicatriz"])
        self.assertEqual(data["cores"]["roupa"], "#3b5dc9")
        self.assertEqual(data["camadas"]["cabelo"]["estilo"], "rabo")  # o resto do modelo continua
        with self.assertRaises(character.ModelError):
            character.resolve(MODEL, ["nada"])
        with self.assertRaises(character.ModelError):
            character.resolve(MODEL, [], "nada")
        old = character.parse_model(character.resolve(MODEL, ["idosa"]))
        self.assertIn("rugas", old.marks)
        self.assertGreater(L(old.color("cabelo")), L(self.model.color("cabelo")))
        blue = character.parse_model(data)
        a, _ = character.render_body(self.model, "frente")
        b, _ = character.render_body(blue, "frente")
        self.assertFalse(np.array_equal(a.pixels, b.pixels))
        self.assertTrue(np.array_equal(a.pixels[..., 3], b.pixels[..., 3]))  # mesma silhueta

    def test_all_styles_render(self):
        for style in character.HAIR_STYLES:
            for outfit in character.OUTFITS:
                m = character.parse_model({"name": "x", "camadas": {
                    "cabelo": {"estilo": style}, "roupa": {"estilo": outfit},
                    "acessorios": list(character.ACCESSORIES), "marcas": list(character.MARKS), "barba": "cheia"}})
                for view in character.VIEWS:
                    sprite, _ = character.render_body(m, view)
                    self.assertTrue(sprite.pixels[..., 3].any())
                character.render_portrait(m, "surpreso", mouth_open=True)
        child = character.parse_model({"name": "c", "idade": "crianca"})
        self.assertTrue(character.render_body(child)[0].pixels[..., 3].any())

    def test_layers_recompose(self):
        sprite, layer_map = character.render_body(self.model, "frente")
        parts = character.split_layers(sprite, layer_map)
        self.assertIn("cabelo", parts)
        self.assertIn("contorno", parts)
        total = np.zeros_like(sprite.pixels)
        for p in parts.values():
            m = p.pixels[..., 3] > 0
            self.assertFalse(np.any(total[m, 3]))  # camadas não se sobrepõem
            total[m] = p.pixels[m]
        self.assertTrue(np.array_equal(total, sprite.pixels))

    def test_extras_grid_layer(self):
        m = character.parse_model({**MODEL, "extras": [{"nome": "broche", "vistas": ["frente"], "presa_a": "tronco",
                                                       "pos": [1, 2], "grade": ["y"], "paleta": {"y": "#ff00ff"}}]})
        sprite, _ = character.render_body(m, "frente")
        self.assertTrue(np.any(np.all(sprite.pixels == (255, 0, 255, 255), axis=-1)))
        side, _ = character.render_body(m, "direita")
        self.assertFalse(np.any(np.all(side.pixels == (255, 0, 255, 255), axis=-1)))

    def test_model_sheet(self):
        sprite, _ = character.build_sprite(self.model)
        portrait, _ = character.build_portrait(self.model)
        sheet = character.model_sheet(self.model, sprite, portrait)
        self.assertGreater(sheet.width, 5 * 48)

    def test_cli_character(self):
        d = tmpdir()
        model = d / "teste.personagem.json"
        model.write_text(json.dumps(MODEL), encoding="utf-8")
        code, out = run_cli("character", model, "--variante", "cicatriz", "--out", d / "out", "--formats", "png",
                            "--scales", "1", "--aseprite")
        self.assertEqual(code, 0, out)
        spec = load_spec(d / "teste_cicatriz.json")
        self.assertIn("andar", spec.meta["animations"])
        self.assertEqual(spec.meta["anchor"], [16, 31])
        portrait = load_spec(d / "teste_cicatriz_retrato.json")
        self.assertIn("feliz", portrait.meta["animations"])
        for name in ("teste_cicatriz_preview.png", "teste_cicatriz_andar.gif", "teste_cicatriz_retrato_feliz.gif",
                     "teste_cicatriz.aseprite"):
            self.assertTrue((d / "out" / name).is_file(), name)
        ase = aseprite.read_ase(d / "out" / "teste_cicatriz.aseprite")
        self.assertIn("cabelo", ase.meta["aseprite"]["camadas"])
        code, out = run_cli("character", model, "--paleta", "azul", "--mapa", "noite", "--no-spec",
                            "--out", d / "out2", "--formats", "png", "--scales", "1")
        self.assertEqual(code, 0)
        self.assertFalse((d / "teste_azul_noite.json").exists())


class TileTests(unittest.TestCase):
    def test_blob47_masks(self):
        self.assertEqual(len(tiles.BLOB47), 47)
        self.assertEqual(tiles.reduce_mask(tiles.NE), 0)          # canto sem os lados não conta
        self.assertEqual(tiles.reduce_mask(tiles.N | tiles.E | tiles.NE), tiles.N | tiles.E | tiles.NE)
        self.assertEqual(tiles.tile_index(255, "blob47"), 46)
        self.assertEqual(tiles.tile_index(tiles.N | tiles.S, "blob16"), 5)
        self.assertEqual(tiles.tile_index(0, "cheio"), 0)

    def test_autotile_shapes(self):
        base = np.zeros((16, 16, 4), np.uint8)
        base[:] = GREEN
        full = tiles.autotile(base, 255, BLACK)
        self.assertTrue(np.array_equal(full, base))
        alone = tiles.autotile(base, 0, BLACK)
        self.assertEqual(alone[0, 0, 3], 0)                       # canto externo arredondado
        self.assertEqual(tuple(alone[0, 8]), BLACK)               # borda
        self.assertEqual(tuple(alone[8, 8]), GREEN)
        inner = tiles.autotile(base, 255 & ~tiles.NE, BLACK)      # só falta a diagonal: canto interno
        self.assertEqual(tuple(inner[0, 15]), BLACK)
        self.assertEqual(tuple(inner[8, 8]), GREEN)
        t16 = tiles.Terrain("agua", GREEN, BLACK, mode="blob16")
        interior = tiles.generate_tiles(t16, 16)[15]
        self.assertTrue(np.all(interior.pixels[..., 3] == 255))   # blob16 sem entalhes

    def test_texture_deterministic(self):
        a = tiles.texture(16, GREEN, "grama", 3)
        self.assertTrue(np.array_equal(a, tiles.texture(16, GREEN, "grama", 3)))
        with self.assertRaises(ValueError):
            tiles.texture(16, GREEN, "lava")

    def write_tileset(self, d: Path) -> Path:
        path = d / "campo.tileset.json"
        path.write_text(json.dumps({"name": "campo", "tile": 8, "terrenos": {
            "terra": {"cor": "#a46422", "modo": "cheio"},
            "grama": {"cor": "#38b764", "textura": "grama"},
            "agua": {"cor": "#3b5dc9", "modo": "blob16"}}}), encoding="utf-8")
        return path

    def test_tileset_sheet_and_map(self):
        d = tmpdir()
        ts = tiles.load_tileset(self.write_tileset(d))
        sheet, index = tiles.tileset_sheet(ts)
        self.assertEqual(sheet.width, 8 * 8)
        self.assertEqual(len(index["terrenos"]["grama"]["tiles"]), 47)
        tm = tiles.parse_map({"tileset": "campo.tileset.json", "base": "terra", "legenda": {".": "terra", "g": "grama",
                                                                                            "~": "agua"},
                              "grade": ["gg..", "g~~.", "...."]}, d)
        img = tiles.render_map(tm)
        self.assertEqual((img.width, img.height), (32, 24))
        self.assertTrue(np.all(img.pixels[..., 3] == 255))
        # tile de terra puro no canto inferior direito
        self.assertTrue(np.array_equal(img.pixels[16:24, 24:32], ts.terrains["terra"].tiles[0].pixels))

    def test_map_errors(self):
        d = tmpdir()
        self.write_tileset(d)
        with self.assertRaises(ValueError) as ctx:
            tiles.parse_map({"tileset": "campo.tileset.json", "legenda": {".": "terra"}, "grade": [".x"]}, d)
        self.assertIn("coluna 1", str(ctx.exception))
        with self.assertRaises(ValueError):
            tiles.parse_map({"tileset": "campo.tileset.json", "legenda": {".": "lava"}, "grade": ["."]}, d)
        with self.assertRaises(ValueError):
            tiles.parse_tileset({"terrenos": {"x": {"modo": "blob99", "cor": "#fff"}}})

    def test_cli_tileset_and_tilemap(self):
        d = tmpdir()
        ts = self.write_tileset(d)
        code, _ = run_cli("tileset", ts, "--out", d / "o", "--formats", "png", "--scales", "1")
        self.assertEqual(code, 0)
        index = json.loads((d / "o" / "campo_tiles.json").read_text(encoding="utf-8"))
        self.assertEqual(index["terrenos"]["agua"]["modo"], "blob16")
        mp = d / "vila.mapa.json"
        mp.write_text(json.dumps({"name": "vila", "tileset": "campo.tileset.json", "base": "terra",
                                  "legenda": {".": "terra", "g": "grama"}, "grade": ["g.", ".g"]}), encoding="utf-8")
        code, _ = run_cli("tilemap", mp, "--out", d / "m", "--formats", "png", "--scales", "1")
        self.assertEqual(code, 0)
        self.assertTrue((d / "m" / "vila.png").is_file())


class AsepriteTests(unittest.TestCase):
    def art(self) -> Art:
        frames = []
        for i in range(3):
            s = Sprite.blank(8, 8)
            s.pixels[2:6, 1 + i:5 + i] = (200, 50 * i, 30, 255)
            frames.append(s)
        return Art("bola", frames, 8, {"anchor": [4, 7], "animations": {
            "parado": {"frames": [0], "fps": 2}, "rolar": {"frames": [0, 1, 2, 1], "fps": 10}}})

    def test_ase_roundtrip_with_layers_and_tags(self):
        d = tmpdir()
        art = self.art()
        bg = [Sprite(np.zeros((8, 8, 4), np.uint8)) for _ in range(3)]
        for s in bg:
            s.pixels[7, :] = (10, 20, 30, 255)
        path = aseprite.write_ase(d / "a.aseprite", [("chao", bg), ("bola", art.frames)], [100, 100, 50],
                                  [("rolar", 0, 2)])
        back = aseprite.read_ase(path)
        self.assertEqual(back.meta["aseprite"]["camadas"], ["chao", "bola"])
        self.assertEqual(back.meta["animations"]["rolar"]["frames"], [0, 1, 2])
        for i in range(3):
            expected = bg[i].pixels.copy()
            m = art.frames[i].pixels[..., 3] > 0
            expected[m] = art.frames[i].pixels[m]
            self.assertTrue(np.array_equal(back.frames[i].pixels, expected))

    def test_art_to_ase_unrolls_animations(self):
        d = tmpdir()
        back = aseprite.read_ase(aseprite.art_to_ase(self.art(), d / "b.ase"))
        self.assertEqual(back.meta["animations"]["rolar"]["frames"], [0, 1, 2, 1])
        self.assertEqual(back.meta["animations"]["rolar"]["fps"], 10)
        self.assertEqual(len(back.frames), 3)  # quadros repetidos reaproveitados

    def test_indexed_ase(self):
        """Arquivo indexado (8 bits) escrito à mão: paleta, cel bruto, índice transparente."""
        pal = struct.pack("<III", 3, 0, 2) + bytes(8)
        for rgba in ((0, 0, 0, 0), (255, 0, 0, 255), (0, 0, 255, 255)):
            pal += struct.pack("<HBBBB", 0, *rgba)
        layer = struct.pack("<HHHHHHB", 1, 0, 0, 0, 0, 0, 255) + bytes(3) + struct.pack("<H", 1) + b"L"
        cel = struct.pack("<HhhBHh", 0, 1, 1, 255, 0, 0) + bytes(5) + struct.pack("<HH", 2, 2) + bytes([1, 2, 0, 1])
        chunks = [aseprite._chunk(aseprite.CHUNK_PALETTE, pal), aseprite._chunk(aseprite.CHUNK_LAYER, layer),
                  aseprite._chunk(aseprite.CHUNK_CEL, cel)]
        content = b"".join(chunks)
        frame = struct.pack("<IHHH", 16 + len(content), 0xF1FA, 3, 100) + bytes(2) + struct.pack("<I", 3) + content
        header = struct.pack("<IHHHHHIH", 128 + len(frame), 0xA5E0, 1, 4, 4, 8, 1, 100) + bytes(8) + bytes([0])
        header += bytes(128 - len(header))
        path = tmpdir() / "idx.ase"
        path.write_bytes(header + frame)
        art = aseprite.read_ase(path)
        px = art.frames[0].pixels
        self.assertEqual(tuple(px[1, 1]), RED)
        self.assertEqual(tuple(px[1, 2]), BLUE)
        self.assertEqual(px[2, 1, 3], 0)
        self.assertEqual(tuple(px[2, 2]), RED)

    def test_bad_file(self):
        path = tmpdir() / "x.ase"
        path.write_bytes(b"\0" * 200)
        with self.assertRaises(aseprite.AseError):
            aseprite.read_ase(path)

    def test_sheet_json_roundtrip(self):
        d = tmpdir()
        png, js = aseprite.export_sheet(self.art(), d, scale=2)
        data = json.loads(js.read_text(encoding="utf-8"))
        self.assertEqual([t["name"] for t in data["meta"]["frameTags"]], ["parado", "rolar"])
        self.assertEqual(data["meta"]["frameTags"][1], {"name": "rolar", "from": 1, "to": 4,
                                                        "direction": "forward", "color": "#000000ff"})
        self.assertEqual(data["frames"][1]["frame"], {"x": 0, "y": 16, "w": 16, "h": 16})
        self.assertEqual(data["frames"][1]["duration"], 100)
        self.assertEqual(data["meta"]["slices"][0]["keys"][0]["pivot"], {"x": 8, "y": 14})
        with Image.open(png) as im:
            self.assertEqual(im.size, (4 * 16, 2 * 16))
        back = aseprite.read_sheet_json(js)
        self.assertEqual(back.meta["anchor"], [4, 7])
        self.assertEqual(back.size, (8, 8))
        self.assertEqual(back.meta["animations"]["rolar"]["frames"], [0, 1, 2, 1])

    def test_cli_aseprite(self):
        d = tmpdir()
        spec = save_spec(self.art(), d / "bola.json")
        code, _ = run_cli("aseprite", "export", spec, "--out", d / "o", "--ase")
        self.assertEqual(code, 0)
        code, out = run_cli("aseprite", "import", d / "o" / "bola.aseprite", "--to-spec", d / "bola2.json",
                            "--out", d / "i")
        self.assertEqual(code, 0, out)
        self.assertIn("rolar", load_spec(d / "bola2.json").meta["animations"])


class ArtCliTests(unittest.TestCase):
    def test_recolor_shade_lint_animate(self):
        d = tmpdir()
        art = Art("bloco", [square(8, (177, 62, 83, 255), 2)])
        spec = save_spec(art, d / "bloco.json")
        code, _ = run_cli("recolor", spec, "--swap", "#b13e53:#3b5dc9", "--to-spec", d / "azul.json",
                          "--out", d / "r", "--formats", "png", "--scales", "1")
        self.assertEqual(code, 0)
        self.assertIn((59, 93, 201, 255), load_spec(d / "azul.json").colors())
        code, _ = run_cli("recolor", spec, "--map", "noite", "--out", d / "n", "--formats", "png", "--scales", "1")
        self.assertEqual(code, 0)
        with redirect_stderr(io.StringIO()):
            self.assertEqual(main(["recolor", str(spec)]), 2)  # nada pedido → erro
        code, _ = run_cli("recolor", spec, "--ramps")
        self.assertEqual(code, 0)
        code, _ = run_cli("shade", spec, "--to-spec", d / "sombra.json", "--out", d / "s", "--formats", "png",
                          "--scales", "1")
        self.assertEqual(code, 0)
        self.assertGreater(len(load_spec(d / "sombra.json").colors()), 1)
        code, out = run_cli("lint", spec, "--strict")
        self.assertEqual(code, 1)  # sem contorno, cor média: contraste baixo
        self.assertIn("contraste", out)
        code, out = run_cli("lint", d / "sombra.json", "--json", "--checks", "cores")
        self.assertEqual(code, 0)
        self.assertIn(str(d / "sombra.json"), json.loads(out))
        code, out = run_cli("animate", spec, "--hip", "8", "--to-spec", d / "anim.json", "--out", d / "a",
                            "--formats", "png", "--scales", "1")
        self.assertEqual(code, 0, out)
        self.assertIn("andar", load_spec(d / "anim.json").meta["animations"])


if __name__ == "__main__":
    unittest.main()
