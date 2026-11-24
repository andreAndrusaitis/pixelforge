"""Testes do som (núcleo: stdlib + numpy). Rodar: python -m unittest discover -s tests

Os testes de IA rodam só com o extra [audio-ia] instalado; os pesados (trilha e
ambiente) também exigem PIXELFORGE_TESTES_IA=1.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import tempfile
import unittest
import wave
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import numpy as np

from pixelforge.audio import mix, music, sfx
from pixelforge.audio.ai import common
from pixelforge.audio.wavio import levels, read_wav, resample, write_wav
from pixelforge.cli import main

RATE = 22050


def tmpdir() -> Path:
    d = tempfile.TemporaryDirectory()
    unittest.addModuleCleanup(d.cleanup)
    return Path(d.name)


def has(module: str) -> bool:
    return common.available(module)


class WavTests(unittest.TestCase):
    def test_roundtrip_mono_and_stereo(self):
        d = tmpdir()
        mono = np.sin(np.linspace(0, 100, 1000)).astype(np.float32) * 0.5
        write_wav(d / "m.wav", mono, RATE)
        data, rate = read_wav(d / "m.wav")
        self.assertEqual((rate, data.shape), (RATE, (1000, 1)))
        self.assertLess(np.max(np.abs(data[:, 0] - mono)), 1e-4)
        stereo = np.stack([mono, -mono], axis=1)
        write_wav(d / "s.wav", stereo, RATE)
        with wave.open(str(d / "s.wav")) as fh:
            self.assertEqual((fh.getnchannels(), fh.getsampwidth(), fh.getnframes()), (2, 2, 1000))

    def test_clipping_and_24bit(self):
        d = tmpdir()
        write_wav(d / "c.wav", np.array([2.0, -2.0]), RATE)
        data, _ = read_wav(d / "c.wav")
        self.assertAlmostEqual(float(data.max()), 32767 / 32768, places=4)
        with wave.open(str(d / "24.wav"), "wb") as fh:
            fh.setnchannels(1), fh.setsampwidth(3), fh.setframerate(8000)
            fh.writeframes(bytes([0, 0, 0x40, 0, 0, 0xC0]))   # +0.5, -0.5
        data, _ = read_wav(d / "24.wav")
        np.testing.assert_allclose(data[:, 0], [0.5, -0.5])

    def test_float_wav(self):
        d = tmpdir()
        data = np.array([[0.25, -0.5], [0.75, 0.0]], dtype="<f4")
        fmt = (3).to_bytes(2, "little") + (2).to_bytes(2, "little") + (48000).to_bytes(4, "little")             + (48000 * 8).to_bytes(4, "little") + (8).to_bytes(2, "little") + (32).to_bytes(2, "little")
        body = b"WAVE" + b"fmt " + len(fmt).to_bytes(4, "little") + fmt             + b"data" + data.nbytes.to_bytes(4, "little") + data.tobytes()
        (d / "f.wav").write_bytes(b"RIFF" + len(body).to_bytes(4, "little") + body)
        samples, rate = read_wav(d / "f.wav")
        self.assertEqual(rate, 48000)
        np.testing.assert_array_equal(samples, data)

    def test_resample_length(self):
        x = np.zeros(44100, dtype=np.float32)
        self.assertEqual(len(resample(x, 44100, 22050)), 22050)
        self.assertEqual(resample(np.zeros((100, 2)), 100, 200).shape, (200, 2))

    def test_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            read_wav("nao-existe.wav")


class EffectTests(unittest.TestCase):
    def test_all_presets_render(self):
        for name in sfx.preset_names():
            effect = sfx.load_effect(name)
            x = sfx.synth(effect, 0, RATE)
            with self.subTest(name=name):
                self.assertEqual(len(x), round(effect.duration * RATE))
                self.assertLessEqual(float(np.max(np.abs(x))), 0.98 + 1e-6)
                self.assertGreater(levels(x)["peak"], 0.1)

    def test_deterministic_with_seed(self):
        effect = sfx.load_effect("explosao")
        np.testing.assert_array_equal(sfx.synth(effect, 3, RATE), sfx.synth(effect, 3, RATE))
        self.assertFalse(np.array_equal(sfx.synth(effect, 3, RATE), sfx.synth(effect, 4, RATE)))
        a, b = sfx.vary(effect, 0.2, 5), sfx.vary(effect, 0.2, 5)
        self.assertEqual(a, b)
        self.assertNotEqual(a, sfx.vary(effect, 0.2, 6))

    def test_names_and_json(self):
        self.assertEqual(sfx.load_effect("Explosão").name, "explosao")
        with self.assertRaises(KeyError):
            sfx.load_effect("trombone")
        with self.assertRaises(ValueError):
            sfx.load_effect({"onda": "quadrada", "frequencia": 3})
        with self.assertRaises(ValueError):
            sfx.load_effect({"onda": "flauta"})
        d = tmpdir()
        (d / "zap.json").write_text(json.dumps({"camadas": [{"onda": "serra", "freq": 800, "decaimento": 0.2,
                                                             "sustentação": 0.1}]}), encoding="utf-8")
        effect = sfx.load_effect(d / "zap.json")
        self.assertEqual((effect.name, effect.layers[0].sustentacao), ("zap", 0.1))
        patched = sfx.load_effect({"base": "pulo", "camadas": [{"freq": 500}]})
        self.assertEqual(patched.layers[0].freq, 500)
        self.assertEqual(sfx.load_effect(sfx.load_effect("magia").to_dict()), sfx.load_effect("magia"))

    def test_square_duty_and_slide(self):
        layer = sfx.Layer(onda="quadrada", freq=100, duty=0.25, decaimento=1.0, sustentacao=1, volume=1)
        x = sfx.synth(sfx.Effect("t", [layer]), 0, 10000)
        self.assertAlmostEqual(float(np.mean(x[:1000] > 0)), 0.25, delta=0.02)
        slide = sfx.Layer(freq=100, deslize=1.0)
        f = sfx.frequency_curve(slide, np.array([0.0, 1.0]))
        np.testing.assert_allclose(f, [100, 200])


class MusicTests(unittest.TestCase):
    def test_note_freq(self):
        self.assertAlmostEqual(music.note_freq("A4"), 440.0)
        self.assertAlmostEqual(music.note_freq("C4"), 261.6256, places=3)
        self.assertAlmostEqual(music.note_freq("Bb3"), music.note_freq("A#3"))
        with self.assertRaises(ValueError):
            music.note_freq("H2")

    def test_parse_notes(self):
        self.assertEqual(music.parse_notes("C4 E4:2 - . | G4", 0.5),
                         [("C4", 0.5), ("E4", 2.5), (None, 0.5), ("G4", 0.5)])
        with self.assertRaises(ValueError):
            music.parse_notes("- C4")

    def test_song_duration_and_loop(self):
        song = {"bpm": 120, "loop": 2, "canais": [
            {"onda": "quadrada", "notas": "C4 E4 G4 C5"},             # 4 tempos = 2 s
            {"bateria": True, "dur": 0.5, "notas": "k h s h"},         # 2 tempos
        ]}
        x = music.render_song(song, RATE)
        self.assertEqual(len(x), 2 * 2 * RATE)
        np.testing.assert_array_equal(x, music.render_song(song, RATE))
        self.assertGreater(levels(x)["peak"], 0.1)
        with self.assertRaises(ValueError):
            music.render_song({"canais": [{"bateria": True, "notas": "z"}]}, RATE)


class MixTests(unittest.TestCase):
    def test_clip_placement_and_duration(self):
        beep = np.ones(RATE // 10, dtype=np.float32) * 0.5
        out = mix.mix_clips([mix.Clip(beep, RATE, start=1.0)], duration=2.0, rate=RATE)
        self.assertEqual(out.shape, (2 * RATE, 2))
        self.assertEqual(float(np.abs(out[: RATE - 1]).max()), 0.0)
        self.assertGreater(float(np.abs(out[RATE + 10]).max()), 0.3)
        auto = mix.mix_clips([mix.Clip(beep, RATE, start=0.5)], rate=RATE)
        self.assertEqual(len(auto), int(0.6 * RATE))

    def test_loop_fade_and_duck(self):
        tone = np.full(RATE // 2, 0.4, dtype=np.float32)
        voice = np.full(RATE // 2, 0.1, dtype=np.float32)
        clips = [mix.Clip(tone, RATE, loop=True, fade_in=0.5),
                 mix.Clip(voice, RATE, start=2.0, speech=True)]
        out = mix.mix_clips(clips, duration=3.0, rate=RATE, duck=0.25)
        self.assertEqual(float(out[0, 0]), 0.0)                       # fade-in começa em zero
        mid_track = float(out[int(1.5 * RATE), 0])
        mid_speech = float(out[int(2.25 * RATE), 0])
        self.assertGreater(mid_track, 0.2)                            # loop preencheu
        self.assertLess(mid_speech, mid_track * 0.7)                  # trilha abafada sob a fala

    def test_limiter_and_resample(self):
        loud = np.ones(RATE, dtype=np.float32)
        out = mix.mix_clips([mix.Clip(loud, RATE), mix.Clip(loud[: RATE // 2], RATE // 2)], rate=RATE)
        self.assertLessEqual(float(np.max(np.abs(out))), 0.98 + 1e-6)
        self.assertEqual(len(out), RATE)

    def test_render_plan(self):
        d = tmpdir()
        song = {"bpm": 120, "canais": [{"onda": "triangulo", "notas": "C3 G3"}]}
        (d / "tema.json").write_text(json.dumps(song), encoding="utf-8")
        write_wav(d / "fala.wav", np.full(RATE // 2, 0.2, dtype=np.float32), RATE)
        plan = {"duracao": 3.0, "taxa": RATE, "abafar": 0.5,
                "trilha": {"musica": "tema.json", "volume": 0.5, "fade_out": 1},
                "eventos": [{"t": 0.5, "efeito": "moeda"}, {"t": 1.0, "efeito": {"onda": "ruido", "freq": 900}}],
                "falas": [{"t": 1.5, "arquivo": "fala.wav"}]}
        samples, rate = mix.render_plan(plan, d)
        self.assertEqual((rate, samples.shape), (RATE, (3 * RATE, 2)))
        np.testing.assert_array_equal(samples, mix.render_plan(plan, d)[0])
        with self.assertRaises(ValueError):
            mix.render_plan({}, d)

    def test_make_loop(self):
        x = np.linspace(0.1, 1.0, 1000, dtype=np.float32)
        self.assertEqual(len(mix.make_loop(x, 100, 1.0)), 900)
        padded = np.concatenate([x, np.zeros(500, dtype=np.float32)])
        self.assertEqual(len(mix.trim_silence(padded, 100)), 1005)
        self.assertEqual(len(mix.make_loop(padded, 100, 1.0)), 905)

    @unittest.skipUnless(has("imageio_ffmpeg"), "precisa do extra [video]")
    def test_mux_video(self):
        d = tmpdir()
        ffmpeg = mix.ffmpeg_exe()
        video = d / "v.mp4"
        subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=size=64x64:rate=12",
                        "-t", "2", "-pix_fmt", "yuv420p", str(video)], check=True)
        write_wav(d / "a.wav", sfx.synth(sfx.load_effect("sino"), 0), 44100)
        out = mix.mux_video(video, d / "a.wav", d / "out.mp4")
        probe = subprocess.run([ffmpeg, "-i", str(out)], capture_output=True, text=True).stderr
        self.assertIn("Audio: aac", probe)
        self.assertAlmostEqual(mix.video_duration(out), 2.0, delta=0.15)
        with self.assertRaises(ValueError):
            mix.mux_video(video, d / "a.wav", video)
        plan = {"name": "v", "video": "v.mp4", "eventos": [{"t": 0, "efeito": "menu"}]}
        paths = mix.render_plan_to_files(plan, d, d)
        self.assertEqual(paths[1].name, "v_som.mp4")


class CliTests(unittest.TestCase):
    def run_cli(self, *argv) -> tuple[int, str]:
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(list(argv))
        return code, buf.getvalue()

    def test_effect_and_music(self):
        d = tmpdir()
        code, text = self.run_cli("som", "efeito", "pulo", "--out", str(d), "--json")
        self.assertEqual(code, 0)
        self.assertTrue((d / "pulo.wav").is_file() and (d / "pulo.json").is_file())
        self.assertIn("44100 Hz", text)
        code, text = self.run_cli("som", "efeito", "--lista")
        self.assertIn("explosao", text)
        (d / "t.json").write_text(json.dumps({"bpm": 240, "canais": [{"notas": "C4 D4"}]}), encoding="utf-8")
        self.assertEqual(self.run_cli("som", "musica", str(d / "t.json"), "--out", str(d))[0], 0)
        _, rate = read_wav(d / "t.wav")
        self.assertEqual(rate, 44100)

    def test_mix_cli(self):
        d = tmpdir()
        (d / "r.json").write_text(json.dumps({"eventos": [{"t": 0.2, "efeito": "menu"}]}), encoding="utf-8")
        code, _ = self.run_cli("som", "mix", str(d / "r.json"), "--out", str(d))
        self.assertEqual(code, 0)
        self.assertTrue((d / "r.wav").is_file())

    def test_unknown_preset_error(self):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as err:
            self.assertEqual(main(["som", "efeito", "trombone"]), 2)
        self.assertIn("presets", err.getvalue().lower())


class AiTests(unittest.TestCase):
    def test_missing_dependency_message(self):
        with self.assertRaises(common.BackendError) as ctx:
            common.require("pacote_que_nao_existe_xyz", "voz (Kokoro)")
        self.assertIn("[audio-ia]", str(ctx.exception))

    def test_models_dir_env(self):
        d = tmpdir()
        old = os.environ.get("PIXELFORGE_MODELS")
        os.environ["PIXELFORGE_MODELS"] = str(d / "m")
        try:
            self.assertEqual(common.models_dir(), d / "m")
        finally:
            os.environ.pop("PIXELFORGE_MODELS") if old is None else os.environ.__setitem__("PIXELFORGE_MODELS", old)

    def test_ace_step_not_installed(self):
        from pixelforge.audio.ai import music as ai_music
        with self.assertRaises(common.BackendError):
            ai_music.ace_python(tmpdir())

    @unittest.skipUnless(has("kokoro") and has("torch"), "extra [audio-ia] não instalado")
    def test_voice(self):
        from pixelforge.audio.ai import voice
        samples, rate = voice.speak("Olá, mundo.")
        self.assertEqual(rate, 24000)
        self.assertTrue(0.5 < len(samples) / rate < 4.0)
        self.assertGreater(levels(samples)["peak"], 0.05)

    @unittest.skipUnless(has("diffusers") and os.environ.get("PIXELFORGE_TESTES_IA") == "1",
                         "lento: defina PIXELFORGE_TESTES_IA=1 (extra [audio-ia])")
    def test_ambient(self):
        from pixelforge.audio.ai import ambient
        samples, rate = ambient.generate("rain", seconds=2, steps=10)
        self.assertAlmostEqual(len(samples) / rate, 2.0, delta=0.2)

    @unittest.skipUnless(os.environ.get("PIXELFORGE_TESTES_IA") == "1", "lento: defina PIXELFORGE_TESTES_IA=1")
    def test_music_ai(self):
        from pixelforge.audio.ai import music as ai_music
        out = tmpdir() / "m.wav"
        ai_music.generate("chiptune, upbeat, 8-bit", seconds=10, out=out)
        samples, rate = read_wav(out)
        self.assertAlmostEqual(len(samples) / rate, 10.0, delta=1.0)


if __name__ == "__main__":
    unittest.main()
