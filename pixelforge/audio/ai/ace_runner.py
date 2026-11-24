"""Roda DENTRO do ambiente do ACE-Step 1.5 (não importa o pixelforge).

Uso: <python do ACE-Step> ace_runner.py pedido.json
O pedido traz: caption, duration, seed, bpm, lyrics, out (WAV), lm (bool).
Imprime na última linha: PIXELFORGE_RESULT {"path": ..., "seconds": ...} ou {"error": ...}.
"""

import json
import os
import shutil
import sys
import time


def main(request_path: str) -> int:
    with open(request_path, encoding="utf-8") as fh:
        req = json.load(fh)
    root = os.getcwd()
    sys.path.insert(0, root)
    from acestep import gpu_config
    from acestep.handler import AceStepHandler
    from acestep.inference import GenerationConfig, GenerationParams, generate_music
    from acestep.llm_inference import LLMHandler

    cfg = gpu_config.get_gpu_config()
    t0 = time.time()
    dit = AceStepHandler()
    status, ok = dit.initialize_service(
        project_root=root, config_path=req.get("model", "acestep-v15-turbo"), device="auto",
        offload_to_cpu=cfg.offload_to_cpu_default, offload_dit_to_cpu=cfg.offload_dit_to_cpu_default,
        quantization="int8_weight_only" if cfg.quantization_default else None)
    if not ok:
        return _result({"error": f"DiT: {status}"})
    llm = None
    lm_model = req.get("lm_model") or cfg.recommended_lm_model or "acestep-5Hz-lm-0.6B"
    if req.get("lm", True):
        from pathlib import Path

        from acestep.model_downloader import ensure_lm_model
        ensure_lm_model(lm_model, Path(root) / "checkpoints")   # baixa o LM da faixa de VRAM, se faltar
        llm = LLMHandler()
        status, ok = llm.initialize(checkpoint_dir=os.path.join(root, "checkpoints"), lm_model_path=lm_model,
                                    backend="pt", device="auto", offload_to_cpu=True)
        if not ok:
            print(f"aviso: LM indisponível ({status}); seguindo só com o DiT", file=sys.stderr)
            llm = None
    load_time = time.time() - t0

    params = GenerationParams(
        task_type="text2music", thinking=llm is not None, caption=req["caption"],
        lyrics=req.get("lyrics") or "[Instrumental]", instrumental=not req.get("lyrics"),
        bpm=req.get("bpm"), duration=float(req.get("duration", 30)), inference_steps=int(req.get("steps", 8)),
        guidance_scale=1.0, seed=int(req.get("seed", 0)), shift=3.0,
        vocal_language=req.get("language", "unknown"))
    config = GenerationConfig(batch_size=1, use_random_seed=False, seeds=[int(req.get("seed", 0))], audio_format="wav")
    t1 = time.time()
    save_dir = os.path.dirname(os.path.abspath(req["out"]))
    result = generate_music(dit, llm, params, config, save_dir=os.path.join(save_dir, "_ace_tmp"))
    if not result.success or not result.audios:
        return _result({"error": str(getattr(result, "error", None) or result.status_message)})
    shutil.move(result.audios[0]["path"], req["out"])
    shutil.rmtree(os.path.join(save_dir, "_ace_tmp"), ignore_errors=True)
    return _result({"path": req["out"], "load_seconds": round(load_time, 1), "seconds": round(time.time() - t1, 1),
                    "lm": lm_model if llm else None})


def _result(data: dict) -> int:
    print("PIXELFORGE_RESULT " + json.dumps(data, ensure_ascii=False), flush=True)
    return 0 if "error" not in data else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
