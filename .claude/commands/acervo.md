---
description: Consulta e organiza o acervo de assets (buscar, listar, versões, tags, reindexar)
argument-hint: [buscar <palavras> | listar --tipo X | versoes <nome> | tag <nome> <tags> | indexar]
---

Pedido: $ARGUMENTS

Use o acervo do PixelForge (`art/acervo.json`; docs/manual.md, seção "Acervo"):

- Sem argumentos ou com palavras soltas: `python -m pixelforge acervo buscar "<palavras>"`
  (sem palavras: `acervo listar`). Mostre nome, tipo, tamanho, projeto, tags e arquivo.
- `listar`, `buscar`, `versoes`, `tag`, `indexar`: repasse para
  `python -m pixelforge acervo <ação> ...` com as opções reais (`--tipo`, `--tag`,
  `--projeto`, `--remover`, `--json`, `--sem-miniaturas`).
- Se o índice parecer desatualizado (arquivo de `art/` faltando na lista), rode
  `acervo indexar` antes e avise.
- Para ver um item, abra a miniatura (`out/<nome>/<nome>_miniatura.png`) ou o preview
  com Read. Mudar tags/tipo/projeto altera o índice: confirme com o autor antes.
- Para navegar visualmente, sugira o estúdio: `python -m pixelforge studio`.
