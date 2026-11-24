"""Som por IA local (extra `[audio-ia]`). Cada backend importa suas dependências
só quando é chamado e explica o que falta se não estiverem instaladas.

  voice    Kokoro TTS (português do Brasil) → fala
  music    ACE-Step 1.5 (ambiente próprio, via subprocesso) → trilha
  ambient  Stable Audio Open (se liberado no Hugging Face) ou AudioLDM2 → ambientes/efeitos
"""
