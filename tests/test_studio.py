"""Testes do acervo e do estúdio web. Rodar: python -m unittest discover -s tests"""

from __future__ import annotations

import io
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from contextlib import redirect_stdout
from pathlib import Path

from PIL import Image

from pixelforge.cli import main
from pixelforge.config import load_config
from pixelforge.library import Library, split_version
from pixelforge.sprite import load_spec
from pixelforge.studio import make_server
from pixelforge.studio.api import merge_spec

SPEC = """{
  "name": "heroi_v1",
  "size": [3, 2],
  "acervo": {"tipo": "personagem", "tags": ["floresta"], "projeto": "coletanea"},
  "palette": {
    ".": "transparent",
    "a": "#ff0000"
  },
  "pixels": [
    "a.a",
    ".a."
  ]
}
"""

SCRIPT = '''from pixelforge import Canvas

NAME = "pocao"
ACERVO = {"tipo": "objeto", "tags": ["item"]}


def build():
    c = Canvas(4, 4)
    c.px(1, 1, "#00ff00")
    return c
'''


def make_repo() -> Path:
    tmp = tempfile.TemporaryDirectory()
    unittest.addModuleCleanup(tmp.cleanup)
    root = Path(tmp.name)
    (root / "pixelforge.toml").write_text('[output]\ndir = "out"\n', encoding="utf-8")
    art = root / "art"
    (art / "personagens").mkdir(parents=True)
    (art / "examples").mkdir()
    (art / "cenas").mkdir()
    (art / "personagens" / "heroi_v1.json").write_text(SPEC, encoding="utf-8")
    (art / "personagens" / "heroi_v2.json").write_text(SPEC.replace("heroi_v1", "heroi_v2"), encoding="utf-8")
    (art / "pocao.py").write_text(SCRIPT, encoding="utf-8")
    (art / "examples" / "slime.json").write_text(
        SPEC.replace("heroi_v1", "slime").replace('"tipo": "personagem", ', ""), encoding="utf-8")
    (art / "cenas" / "chegada.json").write_text(
        json.dumps({"name": "chegada", "fps": 10, "planos": [{"dur": 2}, {"dur": 1.5}]}), encoding="utf-8")
    Image.new("RGBA", (5, 7), (0, 0, 255, 255)).save(art / "porta.png")
    (root / "refs").mkdir()
    return root


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.root = make_repo()
        self.config = load_config(self.root / "pixelforge.toml")
        self.library = Library.from_config(self.config)

    def test_split_version(self):
        self.assertEqual(split_version("heroi_v2"), ("heroi", 2))
        self.assertEqual(split_version("heroi"), ("heroi", 1))
        self.assertEqual(split_version("retrato_128"), ("retrato_128", 1))

    def test_scan_builds_index(self):
        warnings = self.library.scan(thumbnails=True)
        self.assertEqual(warnings, [])
        entries = self.library.entries
        self.assertEqual(set(entries), {"heroi_v1", "heroi_v2", "pocao", "slime", "chegada", "porta"})
        heroi = entries["heroi_v2"]
        self.assertEqual((heroi.tipo, heroi.projeto, heroi.base, heroi.versao), ("personagem", "coletanea", "heroi", 2))
        self.assertEqual(heroi.herda, "heroi_v1")
        self.assertIn("floresta", heroi.tags)
        self.assertIn("personagens", heroi.tags)          # pasta vira tag
        self.assertEqual(heroi.tamanho, [3, 2])
        self.assertEqual(entries["pocao"].tipo, "objeto")  # lido do ACERVO sem executar
        self.assertEqual(entries["chegada"].tipo, "cena")
        self.assertEqual(entries["porta"].tamanho, [5, 7])
        thumb = self.root / heroi.miniatura
        self.assertTrue(thumb.is_file())
        self.assertTrue((self.root / entries["pocao"].miniatura).is_file())
        data = json.loads((self.root / "art" / "acervo.json").read_text(encoding="utf-8"))
        self.assertEqual(len(data["itens"]), 6)

    def test_search_and_history(self):
        self.library.scan()
        self.assertEqual([e.nome for e in self.library.search(tipo="personagem")], ["heroi_v1", "heroi_v2"])
        self.assertEqual([e.nome for e in self.library.search("item")], ["pocao"])
        self.assertEqual([e.nome for e in self.library.search(tipo="personagem", tags=["floresta"], projeto="coletanea")],
                         ["heroi_v1", "heroi_v2"])
        self.assertEqual(self.library.search(tipo="cenário"), [])
        with self.assertRaises(ValueError):
            self.library.search(tipo="nave")
        self.assertEqual([e.nome for e in self.library.history("heroi_v2")], ["heroi_v1", "heroi_v2"])
        self.assertEqual(self.library.next_version_name("heroi_v1"), "heroi_v3")

    def test_cli_tags_survive_reindex(self):
        self.library.scan()
        self.library.tag("porta", ["madeira"], tipo="cenario", projeto="jogo")
        rebuilt = Library.from_config(self.config)
        rebuilt.scan()
        porta = rebuilt.get("porta")
        self.assertIn("madeira", porta.tags)
        self.assertEqual((porta.tipo, porta.projeto), ("cenario", "jogo"))

    def test_cli_commands(self):
        cfg = str(self.root / "pixelforge.toml")
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(["--config", cfg, "acervo", "indexar", "--sem-miniaturas"]), 0)
            self.assertEqual(main(["--config", cfg, "acervo", "buscar", "heroi", "--json"]), 0)
        listed = json.loads(out.getvalue().split("\n", 1)[1])
        self.assertEqual([e["nome"] for e in listed], ["heroi_v1", "heroi_v2"])
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--config", cfg, "acervo", "tag", "pocao", "verde", "--remover", "item"]), 0)
        tags = Library.from_config(self.config).load().get("pocao").tags
        self.assertIn("verde", tags)
        self.assertNotIn("item", tags)
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(["--config", cfg, "acervo", "versoes", "heroi_v1"]), 0)
        self.assertIn("v2  heroi_v2", out.getvalue())


class MergeSpecTests(unittest.TestCase):
    def test_preserves_order_and_extra_fields(self):
        raw = json.loads(SPEC)
        merged = merge_spec(raw, {"palette": {".": "transparent", "a": "#ff0000", "b": "#00ff00"},
                                  "pixels": ["bbb", ".a."]})
        self.assertEqual(list(merged), list(raw))
        self.assertEqual(merged["acervo"]["projeto"], "coletanea")
        self.assertEqual(merged["pixels"], ["bbb", ".a."])

    def test_single_to_frames(self):
        merged = merge_spec(json.loads(SPEC), {"frames": [["a.a", ".a."], ["...", "aaa"]]})
        self.assertNotIn("pixels", merged)
        self.assertEqual(len(merged["frames"]), 2)
        self.assertLess(list(merged).index("palette"), list(merged).index("frames"))


class StudioApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = make_repo()
        cls.server = make_server(load_config(cls.root / "pixelforge.toml"), 0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def request(self, path, body=None, headers=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, headers=headers or {})
        if body is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req) as res:
                raw = res.read()
                kind = res.headers.get("Content-Type", "")
                return res.status, json.loads(raw) if "json" in kind else raw
        except urllib.error.HTTPError as err:
            return err.code, json.loads(err.read())

    def test_index_page_and_static(self):
        status, html = self.request("/")
        self.assertEqual(status, 200)
        self.assertIn("Estúdio PixelForge".encode(), html)
        status, js = self.request("/static/js/app.js")
        self.assertEqual(status, 200)

    def test_state_and_catalog(self):
        status, state = self.request("/api/estado")
        self.assertEqual(status, 200)
        self.assertIn("pico8", state["paletas"])
        self.assertFalse(state["cena_disponivel"] is None)
        status, data = self.request("/api/acervo")
        self.assertEqual(status, 200)
        self.assertIn("heroi_v2", [e["nome"] for e in data["itens"]])

    def test_read_and_save_spec(self):
        status, art = self.request("/api/arte?arquivo=art/personagens/heroi_v1.json")
        self.assertEqual(status, 200)
        self.assertTrue(art["editavel"])
        self.assertEqual(art["cores"]["a"], "#ff0000ff")
        spec = {"palette": {**art["spec"]["palette"], "b": "#00ff00"}, "pixels": ["bab", ".a."]}
        status, saved = self.request("/api/arte", {"arquivo": "art/personagens/heroi_v1.json", "spec": spec})
        self.assertEqual(status, 200, saved)
        path = self.root / "art" / "personagens" / "heroi_v1.json"
        text = path.read_text(encoding="utf-8")
        self.assertIn('    "bab",\n', text)                      # formato dump_spec
        self.assertIn('"acervo": {"tipo": "personagem"', text)    # campos extras preservados
        self.assertEqual(load_spec(path).frames[0].pixels[0, 0].tolist(), [0, 255, 0, 255])
        self.assertTrue((self.root / "out" / "heroi_v1" / "heroi_v1_preview.png").is_file())

    def test_save_rejects_invalid_and_protected(self):
        status, err = self.request("/api/arte", {"arquivo": "art/personagens/heroi_v2.json",
                                                 "spec": {"pixels": ["zz?", "..."]}})
        self.assertEqual(status, 400)
        self.assertIn("spec inválida", err["erro"])
        status, err = self.request("/api/arte", {"arquivo": "art/examples/slime.json", "spec": {"pixels": ["a.a", ".a."]}})
        self.assertEqual(status, 403)

    def test_new_version_from_script(self):
        status, art = self.request("/api/arte?arquivo=art/pocao.py")
        self.assertEqual(status, 200)
        self.assertFalse(art["editavel"])
        status, saved = self.request("/api/arte/versao", {"arquivo": "art/pocao.py", "spec": art["spec"]})
        self.assertEqual(status, 200, saved)
        self.assertEqual(saved["arquivo"], "art/pocao_v2.json")
        data = json.loads((self.root / "art" / "pocao_v2.json").read_text(encoding="utf-8"))
        self.assertEqual(data["acervo"]["herda"], "pocao")
        self.assertEqual(saved["entrada"]["herda"], "pocao")

    def test_path_validation(self):
        for bad in ("../segredo.txt", "pixelforge.toml", "C:/Windows/win.ini", "/etc/passwd", "art/../../x"):
            status, err = self.request(f"/api/arte?arquivo={urllib.request.quote(bad)}")
            self.assertIn(status, (403, 404), bad)
        status, _ = self.request("/arquivo/pixelforge.toml")
        self.assertEqual(status, 403)
        status, _ = self.request("/arquivo/art/porta.png")
        self.assertEqual(status, 200)
        req = urllib.request.Request(self.base + "/arquivo/art/porta.png", headers={"Range": "bytes=0-3"})
        with urllib.request.urlopen(req) as res:   # Range: necessário para o scrub do <video>
            self.assertEqual((res.status, res.read()), (206, b"\x89PNG"))
        status, err = self.request("/api/arte", {"arquivo": "out/x.json", "spec": {}})
        self.assertEqual(status, 403)

    def test_rejects_foreign_host_and_non_json_post(self):
        status, _ = self.request("/api/estado", headers={"Host": "evil.example:80"})
        self.assertEqual(status, 403)
        req = urllib.request.Request(self.base + "/api/pedido", data=b"texto=oi",
                                     headers={"Content-Type": "application/x-www-form-urlencoded"})
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 415)

    def test_request_to_claude(self):
        body = {"arquivo": "art/personagens/heroi_v2.json", "texto": "Olho mais baixo.",
                "marcas": [{"tipo": "ponto", "x": 1, "y": 0, "nota": "olho"},
                           {"tipo": "retangulo", "x": 0, "y": 0, "w": 2, "h": 2}]}
        status, data = self.request("/api/pedido", body)
        self.assertEqual(status, 200, data)
        md = (self.root / data["pedido"]).read_text(encoding="utf-8")
        self.assertIn("estado: aberto", md)
        self.assertIn("Olho mais baixo.", md)
        self.assertIn("1. ponto em (1, 0) — olho", md)
        self.assertIn("de 0,0 até 1,1", md)
        self.assertTrue((self.root / data["imagem"]).is_file())
        status, listed = self.request("/api/pedidos")
        self.assertEqual(listed["pedidos"][0]["texto"], "Olho mais baixo.")
        status, done = self.request("/api/pedido/estado", {"pedido": data["pedido"], "estado": "feito"})
        self.assertEqual(status, 200)
        self.assertIn("estado: feito", (self.root / data["pedido"]).read_text(encoding="utf-8"))
        status, err = self.request("/api/pedido", {"arquivo": "art/porta.png", "texto": ""})
        self.assertEqual(status, 400)

    def test_scenes_degrade_without_engine(self):
        out = self.root / "out" / "chegada"
        out.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (8, 8)).save(out / "chegada_storyboard.png")
        Image.new("RGB", (8, 8)).save(out / "chegada.gif")
        status, data = self.request("/api/cenas")
        self.assertEqual(status, 200)
        scene = next(c for c in data["cenas"] if c["nome"] == "chegada")
        self.assertEqual(scene["storyboard"], "out/chegada/chegada_storyboard.png")
        status, info = self.request("/api/cena?nome=chegada")
        self.assertEqual(status, 200)
        if not data["motor"]:
            self.assertEqual([p["dur"] for p in info["planos"]], [2.0, 1.5])
            self.assertEqual(info["quadros"], 35)
            status, err = self.request("/api/quadro?roteiro=art/cenas/chegada.json&t=1")
            self.assertEqual(status, 501)

    def test_compare_without_photo(self):
        status, err = self.request("/api/comparar?arquivo=art/personagens/heroi_v2.json")
        self.assertEqual(status, 404)
        self.assertIn("foto", err["erro"])


if __name__ == "__main__":
    unittest.main()
