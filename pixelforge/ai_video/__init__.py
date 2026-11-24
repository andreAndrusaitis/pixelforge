"""Vídeo e animação por IA local → pixel art estável (extra `[video-ia]`).

  wan       Wan 2.2 TI2V-5B (Apache-2.0): imagem + descrição do movimento → clipe (8 GB de VRAM)
  pixelize  pixelização temporal: grade fixa, paleta travada, histerese, mediana, órfãos, fps baixo
  clips     cache por hash + nota técnica (`estilo comparar`) com novas sementes se < 85
  sprite    ciclos parado/andar/falar de um sprite, gravados na spec (animations + anchor)

Só `pixelize` roda sem o extra; o resto importa torch/diffusers sob demanda.
"""
