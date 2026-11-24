"""Testes do servidor MCP. Rodar: python -m unittest discover -s tests

As funções `tool_*` são testadas sempre; o servidor de verdade (stdio, cliente MCP
oficial) só com o extra [mcp] instalado.
"""

from __future__ import annotations

import asyncio
import base64
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from pixelforge.mcp_server import (ToolInputError, find_root, image_bytes, inside, safe_name, tool_acervo_buscar,
                                   tool_lint, tool_quadro, tool_render, tool_som_efeito, tool_storyboard)

REPO = Path(__file__).resolve().parent.parent
HAS_MCP = importlib.util.find_spec("mcp") is not None

FUNDO = {
    "name": "fundo",
    "size": [32, 12],
    "palette": {"a": "#29366f", "b": "#38b764"},
    "pixels": ["a" * 32] * 8 + ["b" * 32] * 4,
}
ROTEIRO = {
    "name": "mini",
    "resolucao": [16, 12],
    "escala": 2,
    "fps": 4,
    "cenario": "fundo",
    "planos": [{"dur": 1, "camera": {"de": [0, 0], "para": [16, 0]}}],
}


def make_root() -> Path:
    """Repositório mínimo: pixelforge.toml + art/ com uma arte, um cenário e um personagem."""
    root = Path(tempfile.mkdtemp(prefix="pf_mcp_")).resolve()
    (root / "pixelforge.toml").write_text('[output]\nformats = ["png"]\nscales = [1]\n', encoding="utf-8")
    art = root / "art"
    (art / "cenas").mkdir(parents=True)
    shutil.copy(REPO / "art" / "examples" / "slime.json", art / "slime.json")
    shutil.copy(REPO / "art" / "examples" / "lia.personagem.json", art / "lia.personagem.json")
    (art / "cenas" / "fundo.json").write_text(json.dumps(FUNDO), encoding="utf-8")
    (art / "cenas" / "mini.json").write_text(json.dumps(ROTEIRO), encoding="utf-8")
    return root


class PathTests(unittest.TestCase):
    def setUp(self):
        self.root = make_root()
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_inside_accepts_relative_and_absolute(self):
        self.assertEqual(inside(self.root, "art/slime.json"), self.root / "art" / "slime.json")
        self.assertEqual(inside(self.root, str(self.root / "art" / "slime.json")), self.root / "art" / "slime.json")

    def test_inside_rejects_escape(self):
        for bad in ("../fora.json", str(REPO / "README.md"), "art/../../x.json", ""):
            with self.subTest(bad=bad), self.assertRaises(ToolInputError):
                inside(self.root, bad, must_exist=False)

    def test_inside_requires_existing(self):
        with self.assertRaises(ToolInputError):
            inside(self.root, "art/nao_existe.json")

    def test_safe_name(self):
        self.assertEqual(safe_name("pulo_2"), "pulo_2")
        for bad in ("../x", "a/b", "a\\b", "", "c:x"):
            with self.subTest(bad=bad), self.assertRaises(ToolInputError):
                safe_name(bad)

    def test_find_root(self):
        self.assertEqual(find_root(self.root), self.root)
        with self.assertRaises(ToolInputError):
            find_root(self.root / "art")

    def test_image_bytes_downscales_by_integer_factor(self):
        path = self.root / "grande.png"
        Image.new("RGB", (3300, 100), "red").save(path)
        with Image.open(io.BytesIO(image_bytes(path, max_side=1600))) as small:
            self.assertEqual(small.size, (1100, 33))


class ToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = make_root()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, True)

    def test_render_lists_generated_files(self):
        result = tool_render(self.root, ["art/slime.json"])
        self.assertTrue(result.ok, result.stderr)
        self.assertIn("out/slime/slime.png", result.files)
        self.assertIn("out/slime/slime_preview.png", result.files)

    def test_render_rejects_outside(self):
        with self.assertRaises(ToolInputError):
            tool_render(self.root, [str(REPO / "art" / "examples" / "slime.json")])

    def test_storyboard_and_quadro(self):
        board = tool_storyboard(self.root, "art/cenas/mini.json")
        self.assertTrue(board.ok, board.stderr)
        self.assertEqual(board.files, ["out/mini/mini_storyboard.png"])
        frame = tool_quadro(self.root, "art/cenas/mini.json", 0.5)
        self.assertTrue(frame.ok, frame.stderr)
        self.assertEqual(frame.files, ["out/mini/mini_t0.5s.png"])
        with Image.open(self.root / frame.files[0]) as image:
            self.assertEqual(image.size, (32, 24))

    def test_scene_error_is_reported(self):
        bad = self.root / "art" / "cenas" / "ruim.json"
        bad.write_text(json.dumps({**ROTEIRO, "name": "ruim", "planos": [{"camera": {}}]}), encoding="utf-8")
        result = tool_storyboard(self.root, "art/cenas/ruim.json")
        self.assertFalse(result.ok)
        self.assertIn("erro", result.to_dict())

    def test_lint_returns_relative_keys(self):
        result, problems = tool_lint(self.root, ["art/slime.json"])
        self.assertTrue(result.ok, result.stderr)
        self.assertIn("art/slime.json", problems)
        for problem in problems["art/slime.json"]:
            self.assertIn("x", problem)

    def test_acervo_buscar(self):
        result, entries = tool_acervo_buscar(self.root, "slime")
        self.assertTrue(result.ok, result.stderr)
        self.assertEqual([e["nome"] for e in entries], ["slime"])

    def test_som_efeito(self):
        result = tool_som_efeito(self.root, "moeda", semente=1, nome="moeda_1")
        self.assertTrue(result.ok, result.stderr)
        self.assertEqual(result.files, ["out/som/moeda_1.wav"])
        with self.assertRaises(ToolInputError):
            tool_som_efeito(self.root, "moeda", nome="../fora")
        with self.assertRaises(ToolInputError):
            tool_som_efeito(self.root, "../../efeito.json")


@unittest.skipUnless(HAS_MCP, "extra [mcp] não instalado (pip install -e .[mcp])")
class StdioServerTests(unittest.TestCase):
    """Sobe `python -m pixelforge mcp` e conversa com ele pelo cliente MCP oficial."""

    @classmethod
    def setUpClass(cls):
        cls.root = make_root()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, True)

    async def _session(self, calls):
        from mcp import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client

        params = StdioServerParameters(
            command=sys.executable, args=["-m", "pixelforge", "mcp", "--raiz", str(self.root)],
            env={"PYTHONPATH": str(REPO), "PYTHONIOENCODING": "utf-8"}, cwd=str(REPO.parent))
        with open(os.devnull, "w") as errlog:
            async with stdio_client(params, errlog=errlog) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    return await calls(session)

    def run_session(self, calls):
        return asyncio.run(self._session(calls))

    @staticmethod
    def payload(result) -> dict:
        texts = [c.text for c in result.content if getattr(c, "type", "") == "text"]
        return json.loads(texts[0])

    def test_lists_all_tools(self):
        async def calls(session):
            return await session.list_tools()

        names = {tool.name for tool in self.run_session(calls).tools}
        self.assertEqual(names, {"render", "quadro", "storyboard", "cena", "personagem", "lint",
                                 "acervo_buscar", "som_efeito"})

    def test_tools_over_stdio(self):
        async def calls(session):
            return {
                "render": await session.call_tool("render", {"arquivos": ["art/slime.json"], "ver": True}),
                "storyboard": await session.call_tool("storyboard", {"roteiro": "art/cenas/mini.json"}),
                "quadro": await session.call_tool("quadro", {"roteiro": "art/cenas/mini.json", "t": 0.25}),
                "cena": await session.call_tool("cena", {"roteiro": "art/cenas/mini.json", "formatos": "gif"}),
                "personagem": await session.call_tool("personagem", {"modelo": "art/lia.personagem.json",
                                                                     "gravar_specs": False}),
                "lint": await session.call_tool("lint", {"arquivos": ["art/slime.json"]}),
                "acervo": await session.call_tool("acervo_buscar", {"texto": "slime"}),
                "som": await session.call_tool("som_efeito", {"fonte": "pulo"}),
                "fora": await session.call_tool("render", {"arquivos": [str(REPO / "README.md")]}),
            }

        results = self.run_session(calls)
        render = results["render"]
        self.assertIn("out/slime/slime_preview.png", self.payload(render)["arquivos"])
        images = [c for c in render.content if getattr(c, "type", "") == "image"]
        self.assertEqual(len(images), 1)
        with Image.open(io.BytesIO(base64.b64decode(images[0].data))) as preview:
            self.assertGreater(preview.width, 16)

        self.assertIn("out/mini/mini_storyboard.png", self.payload(results["storyboard"])["arquivos"])
        self.assertIn("out/mini/mini_t0.25s.png", self.payload(results["quadro"])["arquivos"])
        self.assertIn("out/mini/mini.gif", self.payload(results["cena"])["arquivos"])
        self.assertIn("out/lia/lia_preview.png", self.payload(results["personagem"])["arquivos"])
        self.assertIn("art/slime.json", self.payload(results["lint"])["problemas"])
        self.assertEqual(self.payload(results["acervo"])["total"], 1)
        self.assertEqual(self.payload(results["som"])["arquivos"], ["out/som/pulo.wav"])
        fora = self.payload(results["fora"])
        self.assertFalse(fora["ok"])
        self.assertIn("fora do repositório", fora["erro"])
        for name, path in [("cena", "out/mini/mini.gif"), ("som", "out/som/pulo.wav")]:
            with self.subTest(name=name):
                self.assertTrue((self.root / path).is_file())


if __name__ == "__main__":
    unittest.main()
