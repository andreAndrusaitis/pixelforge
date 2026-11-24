"""Testes do motor de cena, etapa 5 e acabamento: som na cena, títulos, legendas,
câmera "cinema" (folga, enquadramentos, close no diálogo) e testes golden.
Rodar: python -m unittest discover -s tests"""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from pixelforge.audio.wavio import read_wav, write_wav
from pixelforge.cli import main
from pixelforge.config import load_config
from pixelforge.scene import Library, SceneError, Timeline, has_mp4, parse_scene, render_frame
from pixelforge.scene import golden, text
from pixelforge.scene.sound import BIP_EVERY, SceneSound, has_sound, render_scene_audio, typewriter
from pixelforge.scene.timeline import follow

ROOT = Path(__file__).resolve().parent.parent
SKY = (0, 0, 80)


def tmpdir() -> Path:
    d = tempfile.TemporaryDirectory()
    unittest.addModuleCleanup(d.cleanup)
    return Path(d.name)


def setup_folder() -> Path:
    """Fundo 400x90 azul, sprite 'heroi' 4x8 vermelho (pé em [1, 7]) e retrato 'rosto' 12x12 verde."""
    root = tmpdir()
    pixels = np.zeros((90, 400, 4), np.uint8)
    pixels[:] = (*SKY, 255)
    Image.fromarray(pixels, "RGBA").save(root / "fundo.png")
    spec = {"name": "heroi", "size": [4, 8], "anchor": [1, 7], "palette": {".": "transparent", "r": "#ff0000"},
            "frames": [["rrrr"] * 8, ["rrrr"] * 8], "animations": {"parado": [0], "andar": {"frames": [1, 0], "fps": 4}}}
    (root / "heroi.json").write_text(json.dumps(spec), encoding="utf-8")
    face = {"name": "rosto", "size": [12, 12], "palette": {"g": "#00ff00"}, "frames": [["g" * 12] * 12]}
    (root / "rosto.json").write_text(json.dumps(face), encoding="utf-8")
    return root


def make(data: dict, folder: Path, resolution=(160, 90), fps: int = 10) -> Timeline:
    data = {"cenario": "fundo", "atores": {"h": {"sprite": "heroi", "pos": [40, 80]}}, **data}
    return Timeline(parse_scene(data, folder / "roteiro.json"), Library(), resolution, fps)


class AudioScriptTests(unittest.TestCase):
    def test_audio_block_is_parsed(self):
        scene = parse_scene({"cenario": "x", "planos": [{"dur": 2}], "audio": {
            "trilha": {"musica": "tema.json", "volume": 0.5},
            "ambiente": "explosao",
            "eventos": [{"inicio": 1, "efeito": "porta", "pan": -0.5}, {"plano": 1, "t": 0.5, "efeito": "sino"}],
            "falas": {"modo": "bip", "voz": "pm_alex"}, "abafar": 0.3}})
        audio = scene.audio
        self.assertTrue(audio.track.loop)
        self.assertEqual(audio.track.kind, "musica")
        self.assertTrue(audio.ambience[0].loop)
        self.assertEqual([(e.start, e.shot, e.pan) for e in audio.events], [(1.0, None, -0.5), (0.5, 1, 0.0)])
        self.assertEqual((audio.voices.mode, audio.voices.voice, audio.duck), ("bip", "pm_alex", 0.3))

    def test_audio_errors(self):
        cases = [
            ({"trilha": {"volume": 1}}, "audio.trilha: informe exatamente uma fonte"),
            ({"trilha": {"efeito": "a", "arquivo": "b"}}, "exatamente uma fonte"),
            ({"eventos": [{"efeito": "porta", "plano": 3}]}, r"eventos\[1\]\.plano: esperado inteiro entre 1 e 1"),
            ({"falas": {"modo": "robo"}}, "falas.modo: 'robo' inválido"),
            ({"abafar": 2}, "abafar: esperado número entre 0 e 1"),
            ({"musica": "x"}, "campo 'musica' desconhecido em audio"),
        ]
        for audio, message in cases:
            with self.subTest(audio=audio), self.assertRaisesRegex(SceneError, message):
                parse_scene({"cenario": "x", "planos": [{"dur": 1}], "audio": audio})
        with self.assertRaisesRegex(SceneError, r"plano 1, acao 1\.som\.repetir: só vale com 'ate'"):
            parse_scene({"cenario": "x", "atores": {"h": {"sprite": "s", "pos": [0, 0]}},
                         "planos": [{"dur": 1, "acoes": [{"ator": "h", "anim": "a", "som": {"efeito": "passo",
                                                                                           "repetir": 0.3}}]}]})
        with self.assertRaisesRegex(SceneError, r"plano 1, sons\[1\]\.plano: só vale em audio.eventos"):
            parse_scene({"cenario": "x", "planos": [{"dur": 1, "sons": [{"efeito": "porta", "plano": 1}]}]})


class SoundTests(unittest.TestCase):
    def setUp(self):
        self.root = setup_folder()

    def test_cues_from_shots_actions_and_steps(self):
        tl = make({"planos": [
            {"dur": 1, "sons": [{"efeito": "porta", "inicio": 0.5}]},
            {"dur": 2, "acoes": [{"ator": "h", "ate": [80, 80], "vel": 40, "som": {"efeito": "passo", "repetir": 0.25}},
                                 {"ator": "h", "inicio": 1.5, "anim": "parado", "som": "sino"}]}]}, self.root)
        times = [(round(c.time, 2), c.sound.source.get("efeito"), c.repeat) for c in tl.cues]
        self.assertIn((0.5, "porta", 0), times)
        steps = [t for t, name, _ in times if name == "passo"]
        self.assertEqual(steps, [1.0, 1.25, 1.5, 1.75])          # 40 px a 40 px/s = 1 s andando
        self.assertIn((2.5, "sino", 0), times)

    def test_mix_is_procedural_deterministic_and_aligned(self):
        data = {"audio": {"eventos": [{"inicio": 1.0, "efeito": "porta"}], "falas": "nenhum"},
                "planos": [{"dur": 2}]}
        a = render_scene_audio(make(data, self.root), use_ai=False)
        b = render_scene_audio(make(data, self.root), use_ai=False)
        self.assertEqual(a.samples.shape, (2 * a.rate, 2))
        np.testing.assert_array_equal(a.samples, b.samples)
        loud = np.flatnonzero(np.abs(a.samples).max(axis=1) > 1e-3)
        self.assertAlmostEqual(loud[0] / a.rate, 1.0, places=2)
        self.assertEqual(a.warnings, [])

    def test_event_relative_to_shot_and_wav_file(self):
        write_wav(self.root / "clique.wav", np.ones(441, np.float32) * 0.5, 44100)
        tl = make({"audio": {"eventos": [{"plano": 2, "inicio": 0.5, "arquivo": "clique.wav"}]},
                   "planos": [{"dur": 1}, {"dur": 1}]}, self.root)
        report = render_scene_audio(tl, use_ai=False)
        loud = np.flatnonzero(np.abs(report.samples).max(axis=1) > 1e-3)
        self.assertAlmostEqual(loud[0] / report.rate, 1.5, places=2)
        with self.assertRaisesRegex(SceneError, "arquivo 'nada.wav' não encontrado"):
            render_scene_audio(make({"audio": {"eventos": [{"arquivo": "nada.wav"}]}, "planos": [{"dur": 1}]},
                                    self.root), use_ai=False)

    def test_dialog_without_ai_becomes_typewriter_bips_with_warning(self):
        tl = make({"audio": {"falas": {"modo": "auto"}},
                   "planos": [{"dialogo": {"ator": "h", "texto": "Olá, mundo"}}]}, self.root)
        report = render_scene_audio(tl, use_ai=False)
        self.assertTrue(any("bipes" in w for w in report.warnings))
        self.assertGreater(np.abs(report.samples).max(), 0.01)
        spoken = tl.spoken[0]
        track = typewriter(spoken, 520.0, 8000)
        onsets = np.flatnonzero((np.abs(track[1:]) > 1e-4) & (np.abs(track[:-1]) <= 1e-4))
        letters = sum(1 for i, ch in enumerate("Olá, mundo") if ch.isalnum() and i % BIP_EVERY == 0)
        self.assertEqual(len(onsets), letters)
        silent = render_scene_audio(make({"audio": {"falas": "bip"}, "planos": [
            {"dialogo": {"ator": "h", "texto": "Oi"}}]}, self.root), use_ai=False)
        self.assertEqual(silent.warnings, [])

    def test_ai_sources_are_skipped_with_warning(self):
        tl = make({"audio": {"trilha": {"descricao": "calm harp"}, "ambiente": {"descricao": "rain"},
                             "eventos": [{"inicio": 0.2, "efeito": "menu"}]},
                   "planos": [{"dur": 1, "legenda": {"texto": "Era uma vez", "narrar": True}}]}, self.root)
        sound = SceneSound(tl, use_ai=False)
        report = sound.render()
        self.assertEqual(report.clips, 1)
        joined = " ".join(report.warnings)
        self.assertIn("trilha por IA", joined)
        self.assertIn("ambiente por IA", joined)
        self.assertIn("legendas narradas ficam em silêncio", joined)

    def test_track_fades_follow_scene_transitions(self):
        tone = np.full(4410, 0.5, np.float32)
        write_wav(self.root / "tom.wav", tone, 44100)
        tl = make({"transicoes": {"entrada": "fade", "saida": {"tipo": "fade", "dur": 1}},
                   "audio": {"trilha": {"arquivo": "tom.wav"}}, "planos": [{"dur": 3}]}, self.root)
        report = render_scene_audio(tl, use_ai=False)
        level = np.abs(report.samples[:, 0])
        rate = report.rate
        self.assertLess(level[int(0.1 * rate)], level[int(1.5 * rate)])     # entrando
        self.assertLess(level[int(2.9 * rate)], level[int(1.5 * rate)])     # saindo
        self.assertGreater(level[int(1.5 * rate)], 0.1)                     # loop cobre a cena toda

    def test_has_sound(self):
        self.assertFalse(has_sound(make({"planos": [{"dur": 1}]}, self.root)))
        self.assertTrue(has_sound(make({"planos": [{"dur": 1, "sons": ["porta"]}]}, self.root)))


class TitleAndCaptionTests(unittest.TestCase):
    def setUp(self):
        self.root = setup_folder()

    def test_title_card_fades_in_steps(self):
        tl = make({"planos": [{"titulo": {"texto": "Capítulo 7", "subtitulo": "A vila", "fade": 0.4}},
                              {"dur": 1}]}, self.root)
        self.assertEqual(tl.durations[0], 3.5)                       # plano só com título
        first, middle = render_frame(tl, tl.frames[0]), render_frame(tl, tl.at(1.5))
        self.assertTrue((first == 0).all())                          # cartela preta, texto ainda invisível
        self.assertTrue((middle == 255).all(axis=2).sum() > 50)      # texto branco
        self.assertIsNone(tl.at(3.6).title)
        lit = [int((render_frame(tl, tl.frames[i]) == 255).all(axis=2).sum()) for i in range(5)]
        self.assertEqual(lit, sorted(lit))                           # aparece em degraus
        self.assertLess(lit[1], lit[4])

    def test_title_over_scene_keeps_background(self):
        tl = make({"planos": [{"dur": 1, "titulo": {"texto": "Fim", "fundo": None, "fade": 0}}]}, self.root)
        frame = render_frame(tl, tl.frames[0])
        self.assertEqual(tuple(frame[2, 2]), SKY)
        self.assertTrue((frame == 255).all(axis=2).any())

    def test_captions_sequence_and_dodge_dialog(self):
        tl = make({"planos": [{"dur": 6, "legenda": [{"texto": "Um"}, {"texto": "Dois", "dur": 1}]}]}, self.root)
        self.assertEqual([c.text for c in tl.at(0.5).captions], ["Um"])
        self.assertEqual([c.text for c in tl.at(1.6).captions], ["Dois"])     # "Um" dura 1,5 s
        self.assertEqual(tl.at(2.6).captions, [])
        frame = render_frame(tl, tl.at(0.5))
        rows = np.flatnonzero((frame == 255).all(axis=2).any(axis=1))
        self.assertGreater(rows.min(), 60)                                   # embaixo
        canvas = np.zeros((90, 160, 3), np.uint8)
        text.draw_captions(canvas, tl.at(0.5).captions, dialog_side="baixo")
        rows = np.flatnonzero((canvas == 255).all(axis=2).any(axis=1))
        self.assertLess(rows.max(), 30)                                      # sobe por causa da caixa


class CinemaCameraTests(unittest.TestCase):
    def setUp(self):
        self.root = setup_folder()

    def test_follow_with_slack(self):
        self.assertEqual(follow(100, 20, 160, 30), 20)       # centro 100: dentro da folga
        self.assertEqual(follow(140, 20, 160, 30), 30)       # passou 10 px da folga
        self.assertEqual(follow(40, 20, 160, 30), -10)     # o limite do cenário vem depois
        tl = make({"planos": [{"dur": 4, "camera": {"seguir": "h", "folga": 20, "pos": [0, 0]},
                               "acoes": [{"ator": "h", "ate": [200, 80], "vel": 40}]}]}, self.root)
        xs = [f.camera[0] for f in tl.frames]
        self.assertEqual(xs[0], 0)
        self.assertEqual(xs, sorted(xs))
        last = tl.frames[-1]
        self.assertEqual(last.actors[0].x - (last.camera[0] + 80), 20)        # ator na borda da folga

    def test_framings(self):
        tl = make({"planos": [{"dur": 0.5, "camera": {"enquadrar": "geral", "em": "h"}},
                              {"dur": 0.5, "camera": {"enquadrar": "medio", "em": "h"}},
                              {"dur": 0.5, "camera": {"enquadrar": "close", "em": "h"}},
                              {"dur": 0.5}]}, self.root)
        zooms = [tl.frames[i].zoom for i in (0, 5, 10, 15)]
        self.assertEqual(zooms, [1, 2, 3, 3])                                 # zoom persiste
        geral, medio, close = (tl.frames[i].camera for i in (0, 5, 10))
        self.assertEqual(medio, (0, 90 - 45))                                # centro do ator, limitado ao cenário
        self.assertEqual(close[0], 40 - 26)
        frame = render_frame(tl, tl.frames[10])
        self.assertGreater((frame == (255, 0, 0)).all(axis=2).sum(), 4 * 8 * 3)   # ator ampliado
        with self.assertRaisesRegex(SceneError, "enquadrar \"close\": diga em quem"):
            make({"planos": [{"dur": 1, "camera": {"enquadrar": "close"}}]}, self.root)
        with self.assertRaisesRegex(SceneError, "não combina com 'pos'"):
            make({"planos": [{"dur": 1, "camera": {"enquadrar": "geral", "pos": [0, 0]}}]}, self.root)

    def test_closeup_on_actor_during_line_only(self):
        tl = make({"planos": [{"dur": 1, "camera": {"pos": [0, 0]}},
                              {"dialogo": {"ator": "h", "texto": "Oi", "close": "ator", "fim": 0.5}},
                              {"dur": 0.5}]}, self.root)
        talking = tl.frames[tl.shot_ranges[1][0]]
        self.assertEqual(talking.zoom, 3)
        after = tl.frames[tl.shot_ranges[2][0]]
        self.assertEqual((after.zoom, after.camera), (1, (0, 0)))           # volta ao plano normal

    def test_closeup_portrait_is_big_and_dims_scene(self):
        tl = make({"planos": [{"dialogo": {"ator": "h", "retrato": "rosto", "close": "retrato", "texto": "Oi"}}]},
                  self.root, resolution=(320, 180))
        frame = render_frame(tl, tl.frames[-1])
        green = (frame == (0, 255, 0)).all(axis=2)
        self.assertGreater(green.sum(), 12 * 12)                            # retrato ampliado
        self.assertTrue((frame[:20, :20] != SKY).any())                     # cena escurecida
        with self.assertRaisesRegex(SceneError, "close: \"retrato\" precisa de 'retrato'"):
            make({"planos": [{"dialogo": {"ator": "h", "texto": "x", "close": "retrato"}}]}, self.root)


class GoldenTests(unittest.TestCase):
    """Quadros de referência em tests/golden/. Mudança visual intencional:
    python -m pixelforge golden tests/golden/golden.json --regravar"""

    def test_reference_frames_match(self):
        results = golden.run(ROOT / "tests" / "golden" / "golden.json", load_config(ROOT / "pixelforge.toml"))
        self.assertTrue(results)
        bad = [r.describe() for r in results if r.status != "ok"]
        self.assertEqual(bad, [], "quadros diferentes; se for intencional: python -m pixelforge golden --regravar")

    def test_compare_finds_changed_pixels(self):
        a = np.zeros((4, 5, 3), np.uint8)
        b = a.copy()
        b[1, 3] = 9
        self.assertEqual(golden.compare(a, a), (0, None))
        self.assertEqual(golden.compare(a, b), (1, (3, 1, 3, 1)))

    def test_record_and_cli(self):
        root = tmpdir()
        folder = setup_folder()
        (folder / "c.json").write_text(json.dumps({"name": "mini", "cenario": "fundo", "resolucao": [32, 16],
                                                   "planos": [{"dur": 1}]}), encoding="utf-8")
        manifest = root / "golden.json"
        manifest.write_text(json.dumps({"cenas": [{"roteiro": str(folder / "c.json"), "quadros": [0.5]}]}),
                            encoding="utf-8")
        cfg = str(ROOT / "pixelforge.toml")
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["--config", cfg, "golden", str(manifest), "--out", str(root / "o")]), 1)
            self.assertEqual(main(["--config", cfg, "golden", str(manifest), "--regravar"]), 0)
            self.assertTrue((root / "mini" / "t0.5.png").is_file())
            Image.new("RGB", (32, 16), (1, 2, 3)).save(root / "mini" / "t0.5.png")
            self.assertEqual(main(["--config", cfg, "golden", str(manifest), "--out", str(root / "o")]), 1)
        self.assertTrue((root / "o" / "mini_t0.5_diff.png").is_file())


class SceneSoundCliTests(unittest.TestCase):
    def setUp(self):
        self.root = setup_folder()
        (self.root / "pixelforge.toml").write_text('[cena]\nresolucao = "32x16"\nescala = 2\nfps = 10\n'
                                                   'formatos = ["gif"]\n', encoding="utf-8")
        self.script = self.root / "som.json"
        self.script.write_text(json.dumps({
            "cenario": "fundo", "atores": {"h": {"sprite": "heroi", "pos": [10, 15]}},
            "audio": {"eventos": [{"inicio": 0.2, "efeito": "porta"}]},
            "planos": [{"dur": 1, "acoes": [{"ator": "h", "ate": [30, 15], "som": "passo"}]}]}), encoding="utf-8")

    def run_cli(self, *args) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(["--config", str(self.root / "pixelforge.toml"), *args])
        return code, out.getvalue(), err.getvalue()

    def test_cena_writes_wav(self):
        code, out, err = self.run_cli("cena", str(self.script), "--sem-ia")
        self.assertEqual(code, 0, err)
        samples, rate = read_wav(self.root / "out" / "som" / "som.wav")
        self.assertAlmostEqual(len(samples) / rate, 1.0, places=2)
        self.assertIn("2 som(ns)", out)
        self.assertIn("só o MP4 leva som", err)
        code, out, err = self.run_cli("cena", str(self.script), "--sem-som", "--out", str(self.root / "mudo"))
        self.assertFalse((self.root / "mudo" / "som.wav").exists())

    @unittest.skipUnless(has_mp4(), "extra [video] (imageio-ffmpeg) não instalado")
    def test_mp4_has_audio_stream(self):
        import subprocess

        from pixelforge.audio.mix import ffmpeg_exe
        code, out, err = self.run_cli("cena", str(self.script), "--formats", "mp4", "--sem-ia")
        self.assertEqual(code, 0, err)
        self.assertIn("(com som)", out)
        mp4 = self.root / "out" / "som" / "som.mp4"
        probe = subprocess.run([ffmpeg_exe(), "-hide_banner", "-i", str(mp4)], capture_output=True, text=True,
                               encoding="utf-8", errors="replace")
        self.assertIn("Audio: aac", probe.stderr)
        self.assertIn("Video: h264", probe.stderr)
        self.assertFalse((self.root / "out" / "som" / "som_mudo.mp4").exists())


if __name__ == "__main__":
    unittest.main()
