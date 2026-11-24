"""IA de imagem local (extra `[imagem-ia]`): rascunho por IA → pixel art de verdade.

A IA (SDXL + LoRA de pixel art, na GPU do usuário) só faz o rascunho; quem
entrega a arte é `pixelforge.pixelize` (grade, paleta, limpeza) e a revisão.

  presets   presets de estilo do [ia] no pixelforge.toml (sem dependências pesadas)
  models    catálogo de pesos, pasta `models/` e download (recusa modelos restritos)
  generate  texto → imagem, imagem → imagem e referência de personagem (IP-Adapter)
  cli       subcomando `ia`: gerar, pixelizar, variar, modelos

torch/diffusers só são importados quando algo é gerado.
"""

INSTALL_HINT = (
    "pip install -e .[imagem-ia]  (PyTorch com CUDA antes: "
    "pip install torch --index-url https://download.pytorch.org/whl/cu128)"
)


class AIImageError(ValueError):
    """Dependência, modelo ou GPU indisponível para a IA de imagem."""
