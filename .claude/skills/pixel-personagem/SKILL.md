---
name: pixel-personagem
description: Folha de personagem no PixelForge — um modelo JSON que gera retrato (expressões), sprite em 4 direções, animações (parado, piscar, falar, andar) e paleta coerentes, prontos para cenas. Use quando o pedido for um personagem recorrente ("cria a Ana para as cenas", "folha de personagem", "o protagonista com retrato e sprite", ficha de personagem de um livro), variações dele (roupa nova, cicatriz, idade, uniforme, versão noturna) ou animar um sprite desenhado à mão. Para uma arte única/avulsa ou foto → pixel art, use a skill pixel-art.
---

# Folha de personagem (PixelForge)

Um personagem recorrente **não** é desenhado pose a pose: escreve-se um **modelo**
(`*.personagem.json`) com o que não pode mudar (cores, proporções, cabelo, roupa,
acessórios) e o motor gera tudo do mesmo modelo — o rosto nunca muda entre artes.
Referência completa das chaves: docs/manual.md, "Motor de arte → Folha de personagem".
Exemplo: `art/examples/lia.personagem.json`.

Comandos a partir da raiz do repositório (`python -m pixelforge ...`; no Windows,
`.venv\Scripts\python -m pixelforge ...` se o `.venv` existir).

## 1. Entrevista (antes de escrever o modelo)

Pergunte com `AskUserQuestion` só o que o pedido e a ficha **não** dizem (até 4
perguntas por chamada). Traço que a ficha não define é perguntado, nunca inventado.

| Pergunta | Opções típicas |
|---|---|
| **Uso** | Cenas (sprite + retrato de diálogo) · Só retrato · Só sprite de jogo |
| **Tamanho do sprite** | 32×32 (padrão de cena hd) · 24×32 · 48×48 · 64×64 |
| **Idade / corpo** | criança (cabeça maior) · adulto · idoso (grisalho, rugas) |
| **Cabelo** | estilo (curto, longo, rabo, coque, espetado, cacheado, careca) + franja + cor |
| **Roupa** | camisa, casaco, vestido, manto · mangas · pernas (calça, short, saia) + cores |
| **Acessórios / marcas** | óculos, chapéu, cachecol, capa, cinto · cicatriz, sardas · barba |
| **Contorno e luz** | selout (padrão) · escuro `#hex` · nenhum; luz cima-esquerda (padrão) |
| **Variações** | uniforme/casa (`paletas`), roupa nova/cicatriz/idade (`variantes`), noite (`--mapa`) |

Se houver ficha (ex.: coletânea: `coletanea/universos/<u>/biblia/personagens/<p>.md`),
leia-a primeiro e mostre ao autor o que extraiu antes de perguntar o resto. Foto de
pessoa real → pergunte *personagem* × *fiel à foto* e siga a skill `pixel-art` (Fluxo C)
para medir traços e cores; depois traga as cores medidas para o modelo.

## 2. Passos

1. **Onde**: `art/personagens/<nome>.personagem.json` (ou `art/coletanea/<universo>/`).
   Comece copiando a estrutura de `art/examples/lia.personagem.json`.
2. **Modelo**: `tamanho`, `retrato` (40–128, 48 padrão), `idade`, `proporcoes`
   (só se fugir do padrão da idade), `cores` por material (pele, cabelo, olhos, roupa,
   roupa2, calca, sapato, acessorio, boca; `capa`/`chapeu`/`oculos` opcionais),
   `camadas` (cabelo, roupa, pernas, acessorios, marcas, barba), `contorno`, `luz`,
   `expressoes`, `andar` (4 ou 6), `paletas`, `variantes`, `extras` (detalhe desenhado à
   mão preso à `cabeca`/`tronco`/`tela`, com `grade` + `paleta`).
3. **Gerar**:
   ```bash
   python -m pixelforge character art/personagens/<nome>.personagem.json
   ```
   Saída em `out/<nome>/`: `<nome>_preview.png` (folha: expressões, 4 direções, andar,
   rampas), `<nome>_sprite.png`, `<nome>_retrato.png`, um GIF por animação; specs
   `<nome>.json` (sprite com `animations` + `anchor`) e `<nome>_retrato.json` na pasta do
   modelo (`--spec-dir` muda; `--no-spec` não grava).
4. **Variações**: `--variante cicatriz` (repetível), `--paleta uniforme_vermelho`,
   `--mapa noite|por-do-sol|fantasma|sepia`, `--name <nome_saida>`, `--aseprite`
   (`.aseprite` em camadas). Mudança de história vira **versão** (`<nome>_v2.personagem.json`
   com `"acervo": {"herda": "<nome>"}`), a anterior fica.
5. **Sprite desenhado à mão** (sem modelo) que precisa animar:
   ```bash
   python -m pixelforge animate art/<sprite>.json --hip 22 --eyes "13,10 18,10" --mouth 15,13,2,1 --walk 4 --to-spec art/<sprite>.json
   ```
   Meça `--hip`/`--eyes`/`--mouth` no `_preview.png` (grade forte a cada 8 px).
6. **Acervo**: `python -m pixelforge acervo indexar` e, se for de um projeto,
   `acervo tag <nome> --tipo personagem --projeto coletanea <tags>`.

## 3. Ciclo desenhar → pré-visualizar → ajustar

Depois de cada `character`, **abra `out/<nome>/<nome>_preview.png` com Read** e confira
(2–4 voltas):

- silhueta reconhecível no sprite 1x; cabelo e roupa distinguem o personagem dos outros;
- rosto do retrato igual nas 5 expressões (só olhos/boca mudam);
- frente/lado/costas coerentes (cabelo atrás, acessórios do lado certo);
- andar sem "tremer" (cabeça estável, pé volta à âncora);
- rampas com hue shifting (sombra fria, luz quente), sem cor estourada.

Rode `python -m pixelforge lint art/personagens/<nome>.json` (sprite gerado) e use a skill
`pixel-revisao` para o checklist completo. Ajuste **o modelo**, nunca a spec gerada (ela é
sobrescrita no próximo `character`); detalhe que o modelo não expressa vai em `extras`.

## 4. Pronto quando

- preview revisado e aprovado pelo autor (uma versão por vez);
- specs `<nome>.json` e `<nome>_retrato.json` existem, com `anchor` e as animações
  `parado`, `andar`, `falar` (e `<expressão>`/`<expressão>_falar` no retrato);
- lint sem problema grave não intencional; acervo indexado;
- caminhos gerados informados ao autor.

## 5. Armadilhas

- Editar `<nome>.json` à mão e rodar `character` de novo apaga a edição — use `extras`
  ou uma `variante`.
- `variantes` **substituem** listas (`acessorios`, `marcas`): repita os itens que ficam.
- `paletas` trocam cores **antes** de sombrear; `--mapa` tinge **depois** (noite, fantasma).
- Sprites olham para a **direita**; a esquerda é espelho automático na cena.
- `tamanho` muito pequeno (< 24 px de altura) apaga olhos e boca do sprite — o retrato
  é que carrega a expressão.
- Para cenas, o pé (`anchor`) fica na última linha do sprite: o `y` do ator no roteiro
  é a linha do chão.
- Agente: o `desenhista` executa esta skill; o `animador`, a parte de `animate`.

## Nível mínimo (guia visual)

Antes de desenhar, gerar ou revisar, leia `docs/estilo/guia-visual.md` e abra 2–3 referências do mesmo
tipo em `refs/estilo-referencias/` (índice por tipo e tag em `docs/estilo/referencias.json`). A entrega só
passa se cumprir o checklist do guia e "aguentar" lado a lado com as referências; arte simples, chapada
ou com olho de anime volta para ajuste.

## Estilo "pintado" (padrão para personagens de entrega)

Ponha `"estilo": "pintado"` no modelo. O gerador passa a sair no acabamento das referências:
- sprite padrão 64×104, com ~4,4 cabeças, e retrato 112×112;
- rampas de 6 tons com hue shifting, sombra em blocos recortados por parte e pincelada nos tecidos;
- olhos discretos de 1–2 px, luz de borda dupla (quente/fria) e contorno seletivo.

O `character` imprime a nota técnica (`estilo comparar`) do sprite e do retrato.

**Regra:** toda saída "pintado" passa pelo ciclo do crítico (`docs/agentes.md`) antes de ir ao autor. O
gerador é a base; o acabamento final (pose com gesto, dobras, rosto) vem das voltas do crítico.
Referência de chegada: os personagens finais desenhados com o kit `pixelforge.paint` em
`art/coletanea/veu/final/` (scripts) e `art/coletanea/veu/*_final*.json` (specs com animações).
