# Personagens da Coletânea

Artes-fonte (`.json` / `.py`) dos personagens dos livros do projeto
`../coletanea`.

- Uma pasta por universo: `art/coletanea/<universo>/<personagem>.json`
  (ex.: `art/coletanea/veu/<personagem>.json`).
- A aparência vem da ficha em `coletanea/universos/<universo>/biblia/personagens/<personagem>.md`
  e da folha de referência em `coletanea/universos/<universo>/ilustracoes/estilo-visual.md`.
  Traço que a ficha não define é perguntado ao autor, nunca inventado.
- Renderize direto para a coletânea:

```bash
python -m pixelforge render art/coletanea/veu/<personagem>.json --out ../coletanea/universos/veu/ilustracoes/pixel/<personagem>
```

- Mudança na história (cicatriz nova, cabelo cortado) vira versão nova
  (`<personagem>_v2.json`); a anterior fica.
