"""Testes do pacote de estilo (decomposição e nota técnica)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from pixelforge.style.analyze import analyze_array, components, detect_grid, merge_palette, to_native
from pixelforge.style.compare import Reference, score


def sprite(seed: int = 0, w: int = 24, h: int = 32) -> np.ndarray:
    rng = np.random.default_rng(seed)
    img = np.zeros((h, w, 4), np.uint8)
    img[..., :3] = (230, 220, 200)
    img[..., 3] = 255
    pal = rng.integers(20, 230, size=(6, 3))
    for _ in range(18):
        x, y = rng.integers(2, w - 6), rng.integers(2, h - 6)
        img[y:y + rng.integers(2, 5), x:x + rng.integers(2, 5), :3] = pal[rng.integers(0, 6)]
    return img


class GridTests(unittest.TestCase):
    def test_detects_integer_scale_and_recovers_native(self):
        native = sprite()
        big = np.kron(native, np.ones((6, 6, 1), np.uint8))
        grid = detect_grid(big[..., :3])
        self.assertAlmostEqual(grid["escala"], 6.0, delta=0.11)
        back = to_native(big, grid)
        self.assertEqual(back.shape[:2], native.shape[:2])
        self.assertTrue((back == native).mean() > 0.97)

    def test_native_image_has_no_grid(self):
        rng = np.random.default_rng(1)
        noise = rng.integers(0, 255, size=(40, 40, 3)).astype(np.uint8)
        self.assertEqual(detect_grid(noise)["escala_x"], detect_grid(noise)["escala_y"])


class PaletteTests(unittest.TestCase):
    def test_merges_near_tones(self):
        rgb = np.array([[[100, 100, 100], [101, 100, 100], [200, 30, 30]]], np.uint8)
        pal = merge_palette(rgb, np.ones((1, 3), bool))
        self.assertEqual(len(pal.counts), 2)

    def test_components(self):
        labels = np.array([[0, 0, 1], [1, 1, 1], [2, 0, 0]])
        _, sizes = components(labels)
        self.assertEqual(sorted(sizes.tolist()), [1, 2, 2, 4])


class AnalyzeTests(unittest.TestCase):
    def test_metrics_shape(self):
        m, extras = analyze_array(sprite(), native=True)
        for key in ("paleta", "valor", "clusters", "luz", "composicao"):
            self.assertIn(key, m)
        self.assertEqual(m["mascara"], "fundo-liso")
        self.assertIn("figura", m)
        self.assertEqual(extras["native"].shape[:2], (32, 24))


class ScoreTests(unittest.TestCase):
    def test_reference_like_scores_high_and_outlier_low(self):
        refs = []
        for i in range(6):
            m, _ = analyze_array(sprite(seed=i), native=True)
            refs.append(Reference(i, f"{i}.png", "personagem", m))
        same, _ = analyze_array(sprite(seed=2), native=True)
        flat = np.zeros((32, 24, 4), np.uint8)
        flat[..., :3] = (230, 220, 200)
        flat[..., 3] = 255
        flat[8:24, 6:18, :3] = (40, 40, 200)
        odd, _ = analyze_array(flat, native=True)
        self.assertGreater(score(same, refs, "personagem").nota, score(odd, refs, "personagem").nota)

    def test_cli_analisar_and_comparar(self):
        from pixelforge.cli import main

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "pixelforge.toml").write_text("", encoding="utf-8")
            refs = root / "refs" / "estilo-referencias"
            refs.mkdir(parents=True)
            items = []
            for i in range(6):
                Image.fromarray(np.kron(sprite(seed=i), np.ones((4, 4, 1), np.uint8))).save(refs / f"{i}.png")
                items.append({"n": i, "arquivo": f"{i}.png", "tipo": "personagem", "tags": []})
            (root / "docs" / "estilo").mkdir(parents=True)
            (root / "docs" / "estilo" / "referencias.json").write_text(json.dumps({"itens": items}), encoding="utf-8")
            cfg = str(root / "pixelforge.toml")
            self.assertEqual(main(["--config", cfg, "estilo", "analisar", "--refs", "--out", str(root / "o")]), 0)
            self.assertTrue((root / "docs" / "estilo" / "analises" / "3.json").is_file())
            art = root / "arte.png"
            Image.fromarray(sprite(seed=9)).save(art)
            self.assertEqual(main(["--config", cfg, "estilo", "comparar", str(art), "--tipo", "personagem",
                                   "--nativa", "--out", str(root / "o")]), 0)
            self.assertTrue((root / "o" / "arte_comparar.png").is_file())


if __name__ == "__main__":
    unittest.main()
