---
name: pixel-cena
description: Diretor de cenas em pixel art no PixelForge — transforma um momento ("a Ana chega à academia atrasada e o mestre a repreende") em planos, roteiro JSON, storyboard revisado e vídeo GIF/MP4 com câmera, atores, diálogo, efeitos e transições. Use para cutscene, cena animada, "filma esse momento", trailer curto, cena de capítulo de livro, ou para ajustar um roteiro de cena existente. Para só o cenário use pixel-cenario; para só um personagem, pixel-personagem.
---

# Diretor de cena (PixelForge)

Você é o diretor: o motor só executa o roteiro. Ciclo:
**momento → planos → roteiro → storyboard → revisão → vídeo.**
Referência do roteiro: docs/manual.md, seção "Cenas" (campos, atores, diálogo, efeitos);
design: `docs/specs/2026-10-21-pixelforge-cena-design.md`; exemplo completo:
`art/examples/cena-demo/`. Equipe e contrato de retorno: `docs/agentes.md`.

## 1. Entrevista

Com `AskUserQuestion`, só o que o pedido não diz (até 4 por chamada):

| Pergunta | Opções típicas |
|---|---|
| **Momento** | o que acontece, em 1–3 frases; quem está; como termina (o "beat" final) |
| **Duração** | 10–20 s (padrão) · 20–40 s · curta 5–8 s (loop/GIF) |
| **Clima / hora** | dia · entardecer · noite (`tinta` + `luz`) · chuva · neblina |
| **Resolução / saída** | `hd` 320×180 ×6 = 1080p (padrão) · `gba` · `snes` · `hd2`/`hd3`; GIF + MP4 (padrão) · só GIF |
| **Som** | sem som · efeitos chiptune · trilha · voz por IA (ver `pixel-som`) |
| **Fonte** | trecho de livro/ficha (leia antes e resuma o que entendeu) · descrição livre |

Projeto externo (ex.: coletânea): leia a ficha/capítulo indicado; traço ou fato que a
fonte não define é perguntado, nunca inventado.

## 2. Planejar (decupagem)

Escreva para o autor, curto, antes de qualquer arte:

1. **Planos** (3–6 para 15 s): para cada um, enquadramento (geral → médio → close no
   retrato do diálogo), o que acontece, duração, câmera (`pos` parada, `de`→`para`
   panorâmica/tilt com `curva: "suave"`, `seguir` ator, `zoom` 1–4, `tremor`), transição
   de entrada (`corte`, `fade`, `fade-branco`, `cortina`).
2. **Ritmo**: plano de abertura de 2–3 s parado (respira), ação no meio, beat final com
   1–2 s de sobra antes do fade de saída. Fala: ~30 letras/s + 1,5 s de leitura no fim.
3. **Inventário**: o que já existe (`python -m pixelforge acervo buscar "<palavras>"`,
   `acervo listar --tipo personagem`) e o que falta — personagens (skill
   `pixel-personagem`), cenário (`pixel-cenario`), sons (`pixel-som`).

Mostre o plano e confirme antes de produzir o que falta.

## 3. Produzir o que falta

Uma arte por vez, cada uma revisada pelo preview. Em paralelo, quando a sessão usa
agentes: `desenhista` (personagens), `cenografo` (cenário), `sonoplasta` (som) — com
briefings que não se cruzam; depois o `animador` (animações e `acoes`).

## 4. Roteiro

`art/cenas/<cena>/<cena>.json` (caminhos de arte procurados na pasta do roteiro e
depois em `art/`, extensão opcional):

```json
{
  "name": "chegada",
  "resolucao": "hd", "escala": 6, "fps": 12,
  "cenario": "cenario", "fundo": "#181425",
  "atores": { "ana": { "sprite": "personagens/ana", "pos": [-24, 150], "olhar": "direita", "nome": "Ana" } },
  "efeitos": [ { "tipo": "vinheta", "intensidade": 0.4 } ],
  "transicoes": { "entrada": "fade", "saida": { "tipo": "fade", "dur": 1.5 } },
  "planos": [
    { "dur": 2.5, "camera": { "pos": [0, 0] } },
    { "dur": 5, "camera": { "seguir": "ana" }, "acoes": [ { "ator": "ana", "ate": [190, 150] } ] },
    { "dialogo": [ { "ator": "ana", "retrato": "personagens/ana_retrato", "texto": "Cheguei." } ] }
  ]
}
```

- `pos` do ator = o **pé** (âncora) em px do cenário: `y` = linha do chão.
- Ações em paralelo dentro do plano, cada uma com `inicio` (s); estado persiste entre planos.
- Plano com `dialogo` e sem `dur` dura o diálogo; `posicao: "cima"` se o ator estiver embaixo.
- Campos com `_` são comentários (use `_sobre` para o resumo do momento).
- Campo desconhecido dá erro com a lista dos válidos: antes de usar algo novo (som no
  roteiro, títulos, câmera de cinema), confira no docs/manual.md se a versão atual já aceita.

## 5. Storyboard e revisão (máx. 3 voltas)

```bash
python -m pixelforge storyboard art/cenas/<cena>/<cena>.json
```

**Abra `out/<cena>/<cena>_storyboard.png` com Read** (início/meio/fim de cada plano, com
tempo e câmera) e aplique a skill `pixel-revisao` (seção cenas). Em instantes duvidosos:

```bash
python -m pixelforge quadro art/cenas/<cena>/<cena>.json --t 7.5 --escala 2
```

Erros do motor apontam plano e campo: corrija e rode de novo. Problemas visuais voltam
para quem fez a parte (cenário, sprite, ações).

## 6. Vídeo

```bash
python -m pixelforge cena art/cenas/<cena>/<cena>.json                 # storyboard + GIF + MP4
python -m pixelforge cena art/cenas/<cena>/<cena>.json --formats gif   # só GIF (rascunho rápido)
```

Saída em `out/<cena>/`: `<cena>_storyboard.png`, `<cena>.gif`, `<cena>.mp4`. Sem o
extra `[video]`, o MP4 é pulado com aviso. **Som**: se o roteiro ainda não aceitar
áudio, monte a faixa com a skill `pixel-som` (`som mix ... --video out/<cena>/<cena>.mp4`).
Depois: `python -m pixelforge acervo indexar`.

## 7. Pronto quando

- storyboard revisado sem problema grave (enquadramento, chão, texto, efeitos);
- vídeo gerado, duração dentro do pedido, fades só onde planejado;
- autor viu o storyboard e o vídeo (uma versão por vez) e aprovou;
- caminhos informados: roteiro, storyboard, GIF/MP4 (e WAV/MP4 com som).

## 8. Armadilhas

- Ator "flutuando" ou enterrado: o `y` não bate com o chão da camada de parallax 1.
- Câmera fora do mundo é limitada ao `size`: panorâmica que "não anda" = mundo estreito.
- `seguir` só centraliza na horizontal; tilt continua com `de`/`para`.
- Fala longa vira páginas (`pausa`); prefira ≤ 2 linhas por página.
- Efeitos demais (chuva + neblina + partículas) apagam a cena; um clima por vez.
- Render do MP4 de 1080p leva tempo: revise com `storyboard`/`quadro` e GIF primeiro.
- Agente: o `diretor-de-cena` executa as seções 2, 4 e 5; o `revisor-visual` revisa.

## Nível mínimo (guia visual)

Antes de desenhar, gerar ou revisar, leia `docs/estilo/guia-visual.md` e abra 2–3 referências do mesmo
tipo em `refs/estilo-referencias/` (índice por tipo e tag em `docs/estilo/referencias.json`). A entrega só
passa se cumprir o checklist do guia e "aguentar" lado a lado com as referências; arte simples, chapada
ou com olho de anime volta para ajuste.
