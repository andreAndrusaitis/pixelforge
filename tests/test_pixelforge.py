"""Testes do PixelForge. Rodar: python -m unittest discover -s tests"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import numpy as np
from PIL import Image

from pixelforge import Art, Canvas, Sprite, load_spec, save_spec
from pixelforge import palettes as pal
from pixelforge import process
from pixelforge.cli import main
from pixelforge.config import load_config
from pixelforge.convert import ConvertOptions, convert, kmeans_palette, parse_size
from pixelforge.export import ExportOptions, export, to_svg
from pixelforge.sprite import SpecError, parse_spec

RED, BLUE, BLACK = (255, 0, 0, 255), (0, 0, 255, 255), (0, 0, 0, 255)


def load(path: Path) -> Image.Image:
    """Abre e fecha o arquivo; devolve a imagem em memória (n_frames preservado em .info)."""
    with Image.open(path) as im:
        frames = getattr(im, "n_frames", 1)
        copy = im.convert("RGBA")
    copy.info["n_frames"] = frames
    return copy


def tmpdir() -> Path:
    d = tempfile.TemporaryDirectory()
    unittest.addModuleCleanup(d.cleanup)
    return Path(d.name)


class PaletteTests(unittest.TestCase):
    def test_parse_color_formats(self):
        self.assertEqual(pal.parse_color("#f00"), RED)
        self.assertEqual(pal.parse_color("ff0000"), RED)
        self.assertEqual(pal.parse_color("#ff000080"), (255, 0, 0, 128))
        self.assertEqual(pal.parse_color("transparent"), pal.TRANSPARENT)
        self.assertEqual(pal.parse_color((0, 0, 255)), BLUE)
        with self.assertRaises(ValueError):
            pal.parse_color("#12")

    def test_builtin_palettes(self):
        self.assertEqual(len(pal.get("pico8")), 16)
        self.assertEqual(len(pal.get("GameBoy")), 4)
        with self.assertRaises(KeyError):
            pal.get("nao-existe")

    def test_user_palette_overrides_builtin(self):
        d = tmpdir()
        (d / "pico8.hex").write_text("ff0000\n; comentário\n0000ff\n", encoding="utf-8")
        self.assertEqual(pal.get("pico8", [d]), [RED, BLUE])

    def test_darkest(self):
        self.assertEqual(pal.darkest([RED, BLACK, BLUE]), BLACK)


class SpecTests(unittest.TestCase):
    SPEC = {"name": "t", "size": [3, 2], "palette": {"r": "#ff0000", "b": "#0000ff"},
            "pixels": ["r.b", "bbr"]}

    def test_parse(self):
        art = parse_spec(self.SPEC)
        px = art.frames[0].pixels
        self.assertEqual(art.size, (3, 2))
        self.assertEqual(tuple(px[0, 0]), RED)
        self.assertEqual(px[0, 1, 3], 0)
        self.assertEqual(tuple(px[1, 2]), RED)

    def test_errors_point_to_location(self):
        bad = dict(self.SPEC, pixels=["r.b", "bxr"])
        with self.assertRaisesRegex(SpecError, "linha 1, coluna 1"):
            parse_spec(bad)
        with self.assertRaisesRegex(SpecError, "largura"):
            parse_spec(dict(self.SPEC, size=None, pixels=["r.b", "bb"]))
        with self.assertRaisesRegex(SpecError, "size"):
            parse_spec(dict(self.SPEC, size=[4, 4]))

    def test_roundtrip_with_frames(self):
        art = parse_spec({"palette": {"r": "#f00"}, "fps": 5, "frames": [["r.", ".r"], [".r", "r."]]})
        path = save_spec(art, tmpdir() / "x.json")
        again = load_spec(path)
        self.assertEqual(again.fps, 5)
        self.assertEqual(len(again.frames), 2)
        for a, b in zip(art.frames, again.frames):
            np.testing.assert_array_equal(a.pixels, b.pixels)
        json.loads(path.read_text(encoding="utf-8"))  # JSON válido


class CanvasTests(unittest.TestCase):
    def test_line_and_clipping(self):
        c = Canvas(4).line(0, 0, 3, 3, "#f00").px(10, 10, "#f00")
        self.assertEqual([c.get(i, i) for i in range(4)], [RED] * 4)
        self.assertEqual(int((c.pixels[..., 3] > 0).sum()), 4)

    def test_rect_ellipse_fill(self):
        c = Canvas(8)
        c.rect(0, 0, 8, 8, "#00f", fill=False)
        c.fill(4, 4, "#f00")
        self.assertEqual(c.get(0, 0), BLUE)
        self.assertEqual(c.get(4, 4), RED)
        e = Canvas(9).circle(4, 4, 3, "#f00")
        self.assertEqual(e.get(4, 4), RED)
        self.assertEqual(e.get(0, 0)[3], 0)

    def test_named_palette_and_mirror(self):
        c = Canvas(4, palette={"pele": "#f00"}).px(0, 1, "pele").mirror_x()
        self.assertEqual(c.get(3, 1), RED)

    def test_color_lock(self):
        c = Canvas(4).rect(0, 0, 2, 4, "#f00")
        with c.only("#f00"):
            c.rect(0, 0, 4, 4, "#00f")
        self.assertEqual(c.get(0, 0), BLUE)
        self.assertEqual(c.get(3, 0)[3], 0)

    def test_dither_levels(self):
        c = Canvas(4).dither(0, 0, 4, 4, "#f00", "#00f", level=0.5, pattern="checker")
        self.assertEqual(c.get(0, 0), BLUE)
        self.assertEqual(c.get(1, 0), RED)

    def test_outline(self):
        c = Canvas(5).px(2, 2, "#f00").outline("#000")
        self.assertEqual(c.get(2, 1), BLACK)
        self.assertEqual(c.get(1, 1)[3], 0)


class ProcessTests(unittest.TestCase):
    def test_cleanup_removes_orphan_but_keeps_details(self):
        c = Canvas(5).rect(0, 0, 5, 5, "#f00").px(2, 2, "#00f")
        cleaned = process.cleanup(c.sprite)
        self.assertEqual(tuple(cleaned.pixels[2, 2]), RED)
        c2 = Canvas(5).rect(0, 0, 5, 5, "#f00").px(2, 2, "#00f").px(3, 2, "#00f")
        self.assertEqual(tuple(process.cleanup(c2.sprite).pixels[2, 2]), BLUE)

    def test_trim(self):
        c = Canvas(6).rect(2, 1, 2, 3, "#f00")
        self.assertEqual((process.trim(c.sprite).width, process.trim(c.sprite).height), (2, 3))


def reference_image() -> Image.Image:
    img = Image.new("RGB", (200, 160), "white")
    px = np.array(img)
    px[30:130, 40:160] = (230, 120, 40)
    px[60:80, 70:90] = (20, 20, 30)
    return Image.fromarray(px)


class ConvertTests(unittest.TestCase):
    def test_size_and_palette_limit(self):
        art = convert(reference_image(), ConvertOptions(size=(24, 16), palette=4, cleanup=0))
        self.assertEqual(art.size, (24, 16))
        self.assertLessEqual(len(art.colors()), 4)

    def test_named_palette_only_uses_palette_colors(self):
        art = convert(reference_image(), ConvertOptions(size=(32, 32), palette="gameboy", dither="bayer4"))
        allowed = set(pal.get("gameboy"))
        self.assertTrue(set(art.colors()) <= allowed)

    def test_remove_background_and_outline(self):
        art = convert(reference_image(), ConvertOptions(size=(32, 32), remove_bg="auto", outline="#000000"))
        px = art.frames[0].pixels
        self.assertEqual(px[0, 0, 3], 0)
        self.assertIn(BLACK, art.colors())

    def test_kmeans_keeps_small_distinct_color(self):
        rgb = np.array([[230, 120, 40]] * 500 + [[20, 20, 30]] * 6 + [[240, 130, 50]] * 200)
        palette = kmeans_palette(rgb, 2)
        self.assertTrue(any(c.sum() < 100 for c in palette))

    def test_floyd_runs(self):
        art = convert(reference_image(), ConvertOptions(size=(16, 16), palette="pico8", dither="floyd"))
        self.assertEqual(art.size, (16, 16))

    def test_options_validation(self):
        with self.assertRaises(ValueError):
            ConvertOptions.from_dict({"nope": 1})
        with self.assertRaises(ValueError):
            convert(reference_image(), ConvertOptions(dither="xyz"))
        self.assertEqual(parse_size("32x48"), (32, 48))
        self.assertEqual(parse_size(16), (16, 16))


class ExportTests(unittest.TestCase):
    def art(self, frames=1) -> Art:
        return Art("t", [Canvas(4).px(i, 0, "#f00").sprite for i in range(frames)], fps=10)

    def test_all_formats(self):
        out = tmpdir()
        paths = export(self.art(), out, ExportOptions(formats=["png", "jpg", "webp", "gif", "svg"], scales=[1, 8]))
        names = {p.name for p in paths}
        self.assertTrue({"t.png", "t@8x.png", "t.jpg", "t.webp", "t.gif", "t.svg", "t_preview.png"} <= names)
        self.assertEqual(load(out / "t@8x.png").size, (32, 32))
        with Image.open(out / "t.jpg") as jpg:
            self.assertEqual(jpg.mode, "RGB")
        gif = load(out / "t.gif")
        self.assertEqual(gif.getpixel((0, 0)), RED)
        self.assertEqual(gif.getpixel((3, 3))[3], 0)

    def test_animation_and_sheet(self):
        out = tmpdir()
        export(self.art(3), out, ExportOptions(formats=["png", "gif"], scales=[1], preview=False))
        self.assertEqual(load(out / "t.png").size, (12, 4))
        self.assertEqual(load(out / "t.gif").info["n_frames"], 3)

    def test_svg_merges_runs(self):
        svg = to_svg(Canvas(4).rect(0, 0, 4, 1, "#f00").sprite)
        self.assertEqual(svg.count("<rect"), 1)
        self.assertIn('width="4"', svg)


class CliTests(unittest.TestCase):
    def run_cli(self, *args) -> tuple[int, str]:
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(list(args))
        return code, buf.getvalue()

    def setUp(self):
        self.root = tmpdir()
        (self.root / "pixelforge.toml").write_text(
            '[output]\nformats = ["png"]\nscales = [1]\npreview = false\n'
            '[presets.mini]\nsize = 8\npalette = 3\n', encoding="utf-8")
        self.cfg = str(self.root / "pixelforge.toml")

    def test_new_render_convert(self):
        code, _ = self.run_cli("--config", self.cfg, "new", "hero", "--size", "8", "--palette", "gameboy")
        self.assertEqual(code, 0)
        spec = self.root / "art" / "hero.json"
        self.assertTrue(spec.exists())

        code, out = self.run_cli("--config", self.cfg, "render", str(spec))
        self.assertEqual(code, 0, out)
        self.assertTrue((self.root / "out" / "hero" / "hero.png").exists())

        image = self.root / "ref.png"
        reference_image().save(image)
        code, out = self.run_cli("--config", self.cfg, "convert", str(image), "--preset", "mini", "--to-spec")
        self.assertEqual(code, 0, out)
        self.assertTrue((self.root / "art" / "ref.json").exists())
        self.assertEqual(load(self.root / "out" / "ref" / "ref.png").size, (8, 8))

    def test_render_python_script(self):
        script = self.root / "dot.py"
        script.write_text("from pixelforge import Canvas\nFPS = 2\n"
                          "def build():\n    return [Canvas(4).px(0, 0, '#f00'), Canvas(4).px(1, 0, '#f00')]\n",
                          encoding="utf-8")
        code, out = self.run_cli("--config", self.cfg, "render", str(script), "--formats", "gif")
        self.assertEqual(code, 0, out)
        self.assertEqual(load(self.root / "out" / "dot" / "dot.gif").info["n_frames"], 2)

    def test_errors_return_code_2(self):
        bad = self.root / "bad.json"
        bad.write_text('{"palette": {"r": "#f00"}, "pixels": ["rx"]}', encoding="utf-8")
        with redirect_stdout(io.StringIO()):
            import contextlib
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(["--config", self.cfg, "render", str(bad)]), 2)

    def test_config_defaults_merge(self):
        config = load_config(Path(self.cfg))
        self.assertEqual(config.data["output"]["jpg_quality"], 95)
        self.assertEqual(config.preset("mini")["size"], 8)


if __name__ == "__main__":
    unittest.main()


# --------------------------------------------------------------------------
# Motor fiel à foto: cor perceptual, filtros, detail, limpeza, máscara, compare
# --------------------------------------------------------------------------

from pixelforge.color import kmeans_palette as kmeans_lab, oklab_to_srgb, srgb_to_oklab  # noqa: E402
from pixelforge.compare import cleanliness, reference_grid, similarity  # noqa: E402
from pixelforge.convert import crop_box, detail_downscale  # noqa: E402
from pixelforge.filters import blocks, kuwahara, sobel  # noqa: E402
from pixelforge.masks import build_mask  # noqa: E402


class ColorTests(unittest.TestCase):
    def test_oklab_roundtrip(self):
        rgb = np.array([[0, 0, 0], [255, 255, 255], [255, 0, 0], [30, 140, 200], [128, 128, 128]])
        np.testing.assert_allclose(oklab_to_srgb(srgb_to_oklab(rgb)), rgb, atol=1)
        self.assertAlmostEqual(float(srgb_to_oklab(np.array([255, 255, 255]))[0]), 1.0, places=3)

    def test_kmeans_weights_favor_focus(self):
        rgb = np.array([[200, 150, 120]] * 50 + [[205, 145, 125]] * 50 + [[40, 90, 200]] * 400)
        weights = np.array([10.0] * 100 + [1.0] * 400)
        palette = kmeans_lab(rgb, 3, weights)
        skin = [c for c in palette if c[0] > 150]
        self.assertGreaterEqual(len(skin), 2)


class FilterTests(unittest.TestCase):
    def test_kuwahara_flattens_noise_and_keeps_edge(self):
        rng = np.random.default_rng(0)
        img = np.zeros((32, 32, 3)) + 60
        img[:, 16:] = 200
        noisy = np.clip(img + rng.normal(0, 12, img.shape), 0, 255)
        out = kuwahara(noisy, 3)
        self.assertLess(out[:, 2:13].std(), noisy[:, 2:13].std() / 2)
        self.assertLess(out[:, 13].mean(), 100)
        self.assertGreater(out[:, 18].mean(), 160)

    def test_sobel_and_blocks(self):
        lum = np.zeros((8, 8))
        lum[:, 4:] = 1
        self.assertGreater(sobel(lum)[:, 3:5].min(), 0)
        self.assertEqual(blocks(np.arange(16).reshape(4, 4), 2).shape, (2, 2, 4))

    def test_crop_box(self):
        self.assertEqual(crop_box((0.5, 0, 0.5, 1), (100, 50)), (50, 0, 100, 50))
        self.assertEqual(crop_box((10, 10, 20, 20), (100, 100)), (10, 10, 30, 30))


class DetailTests(unittest.TestCase):
    def test_detail_keeps_thin_dark_line_that_box_loses(self):
        img = np.full((64, 64, 3), 230, dtype=np.uint8)
        img[27:29, :] = 20  # linha escura de 2px, dentro de um bloco de 8
        source = Image.fromarray(img)
        base = dict(size=(8, 8), palette=4, cleanup=0, trim=False)
        box = convert(source, ConvertOptions(**base, resample="box"))
        detail = convert(source, ConvertOptions(**base, resample="detail", detail=2.0))
        lum = lambda art: art.frames[0].pixels[3, :, :3].astype(int).sum(axis=1).mean() / 3
        self.assertGreater(lum(box), 120)
        self.assertLess(lum(detail), 60)

    def test_smooth_blocks_use_mean(self):
        labels = np.zeros((4, 4), dtype=int)
        lab = np.zeros((4, 4, 3))
        lab[..., 0] = 0.5
        colors_lab = np.array([[0.5, 0, 0], [0.2, 0, 0]])
        idx, opaque = detail_downscale(labels, np.ones((4, 4), bool), lab, colors_lab, 2, 1.0)
        self.assertTrue((idx == 0).all() and opaque.all())


class CleanupTests(unittest.TestCase):
    def test_merge_shades_merges_only_close_colors(self):
        c = Canvas(5).rect(0, 0, 5, 5, "#c08060").px(2, 2, "#c28262")
        self.assertEqual(tuple(process.merge_shades(c.sprite).pixels[2, 2]), (192, 128, 96, 255))
        c2 = Canvas(5).rect(0, 0, 5, 5, "#c08060").px(2, 2, "#202020")
        self.assertEqual(tuple(process.merge_shades(c2.sprite).pixels[2, 2]), (32, 32, 32, 255))

    def test_defringe_replaces_foreign_edge_pixels(self):
        c = Canvas(7).rect(1, 1, 5, 5, "#503020").px(3, 1, "#70a040")
        out = process.defringe(c.sprite)
        self.assertEqual(tuple(out.pixels[1, 3]), (80, 48, 32, 255))

    def test_cleanliness(self):
        flat = Canvas(4).rect(0, 0, 4, 4, "#f00").sprite
        self.assertEqual(cleanliness(flat), 100.0)
        checker = Canvas(4).dither(0, 0, 4, 4, "#f00", "#00f", 0.5, "checker").sprite
        self.assertEqual(cleanliness(checker), 0.0)


class PhotoPipelineTests(unittest.TestCase):
    def test_mask_crop_background_and_metadata(self):
        d = tmpdir()
        img = reference_image()
        img.save(d / "ref.png")
        build_mask(img.size, ["0.2,0.15 0.8,0.15 0.8,0.85 0.2,0.85"], []).save(d / "mask.png")
        opts = ConvertOptions(size=(16, 16), palette=6, mask=str(d / "mask.png"), smooth="kuwahara",
                              resample="detail", merge=0.05, defringe=1, background="#102030")
        art = convert(d / "ref.png", opts)
        self.assertEqual(tuple(art.frames[0].pixels[0, 0]), (16, 32, 48, 255))
        self.assertIn("source", art.meta)
        path = save_spec(art, d / "a.json")
        again = load_spec(path)
        self.assertEqual(again.meta["convert"]["resample"], "detail")

    def test_compare_prefers_matching_art(self):
        img = reference_image()
        opts = ConvertOptions(size=(16, 16), palette=8, cleanup=0)
        good = convert(img, opts).frames[0]
        bad = Sprite(good.pixels[::-1].copy())
        ref = reference_grid(img, opts)
        self.assertGreater(similarity(ref, good).total, similarity(ref, bad).total)

    def test_cli_mask_and_compare(self):
        root = tmpdir()
        (root / "pixelforge.toml").write_text('[output]\nformats = ["png"]\nscales = [1]\npreview = false\n',
                                              encoding="utf-8")
        cfg = str(root / "pixelforge.toml")
        reference_image().save(root / "ref.png")
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(main(["--config", cfg, "mask", str(root / "ref.png"),
                                   "--polygon", "0.1,0.1 0.9,0.1 0.9,0.9 0.1,0.9",
                                   "--out", str(root / "m.png")]), 0)
            self.assertEqual(main(["--config", cfg, "convert", str(root / "ref.png"), "--size", "16",
                                   "--mask", str(root / "m.png"), "--resample", "detail",
                                   "--smooth", "kuwahara", "--to-spec"]), 0)
            self.assertEqual(main(["--config", cfg, "compare", str(root / "art" / "ref.json")]), 0)
        self.assertIn("semelhança", buf.getvalue())
        self.assertTrue((root / "out" / "ref" / "ref_compare.png").exists())
