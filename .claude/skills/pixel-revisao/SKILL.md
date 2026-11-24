---
name: pixel-revisao
description: Checklist de revisão visual de pixel art e cenas no PixelForge — lê previews, storyboards e quadros, roda o lint e devolve problemas com coordenadas (silhueta, leitura em tamanho real, paleta, contorno, consistência com a folha do personagem, enquadramento, ator no chão, texto, efeitos). Use antes de entregar qualquer arte/cena, quando o autor pedir "revisa", "o que está errado nesse sprite?", "confere o storyboard", ou para responder pedidos do estúdio (pedidos/*.md). Não desenha nem corrige: aponta.
---

# Revisão visual (PixelForge)

Revisar = **olhar a imagem** (Read) + **medir** (lint, quadro) + **listar problemas com
coordenadas**. Quem revisa não corrige: devolve a lista para quem desenhou (ou para a
produtora). Formato de retorno: `docs/agentes.md`.

## 1. Entrevista (curta, só se faltar)

- **O quê**: arte (`art/...json|.py`), personagem (modelo), cenário, cena (roteiro)?
- **Contra o quê**: a folha do personagem (`out/<nome>/<nome>_preview.png`), a foto de
  referência (`compare`), o pedido original ou a ficha do livro?
- **Rigor**: rascunho (só graves) · entrega (tudo).

## 2. Material

| Alvo | Gerar / abrir |
|---|---|
| Arte | `python -m pixelforge render <arte>` → Read `out/<nome>/<nome>_preview.png` (grade a cada pixel, linha forte a cada 8) e `out/<nome>/<nome>.png` (1x) |
| Personagem | `python -m pixelforge character <modelo>` → Read `out/<nome>/<nome>_preview.png` |
| Cena | `python -m pixelforge storyboard <roteiro>` → Read `out/<cena>/<cena>_storyboard.png`; dúvidas: `quadro <roteiro> --t <s> --escala 2` |
| Foto | `python -m pixelforge compare <arte.json>` (painel foto | arte | sobreposição + notas) |
| Lint | `python -m pixelforge lint <artes...>` (`--json` para coordenadas; `--bg "#hex"` com o fundo real da cena) |

Coordenadas: na arte, `(x, y)` em pixels a partir do canto superior esquerdo (conte
pela grade do preview: linha forte a cada 8 px). Na cena, pixel **lógico** (resolução
do roteiro, ex.: 320×180) + plano + instante.

## 3. Checklist — arte e personagem

1. **Silhueta**: reconhecível só pela forma (imagine tudo preto)? Pose clara?
2. **Leitura em 1x**: no PNG 1x, olhos/boca/objeto principal leem? Detalhe que só existe
   ampliado é ruído.
3. **Paleta**: número de cores adequado ao tamanho (lint `cores`); rampas com hue shifting;
   nada de dois tons quase iguais lado a lado.
4. **Luz**: uma direção (padrão cima-esquerda); sem pillow shading.
5. **Contorno**: fechado onde deve (lint `contorno`); selout tingido em 32+ px; sem cantos
   duplos ("L" grosso).
6. **Curvas e linhas**: degraus regulares (lint `jaggies`), sem banding (lint `banding`).
7. **Limpeza**: pixels órfãos (lint `orfao`) — olhos e brilhos isolados são intencionais.
8. **Contraste**: silhueta não some no fundo real (lint `contraste --bg`).
9. **Consistência com a folha**: mesmas cores, proporções, cabelo, acessórios do lado
   certo, cicatriz/sinais no mesmo lugar; retrato igual em todas as expressões.
10. **Animação**: âncora estável (pé não desliza), cabeça não treme, volume constante.

## 3b. Checklist — cena (storyboard)

1. **Enquadramento**: o assunto de cada plano está em quadro e com folga; nada
   importante cortado na borda.
2. **Chão**: ator pisa na linha do chão (nem flutua nem afunda); profundidade (y) coerente.
3. **Diálogo**: caixa não cobre o rosto/ação (senão `posicao: "cima"`); texto sem corte,
   ≤ 2 linhas por página; retrato e nome certos.
4. **Câmera e parallax**: movimento crível, sem costura nas camadas repetidas, sem área
   vazia (`fundo`) aparecendo.
5. **Transições**: quadros pretos/brancos só onde há fade/cortina.
6. **Efeitos**: na medida (não apagam a cena); luz no lugar da fonte (janela, tocha).
7. **Ritmo**: duração dos planos coerente com o que acontece; beat final com respiro.
8. **Consistência**: o mesmo personagem igual em todos os planos.

## 4. Saída

Problemas ordenados por gravidade, cada um com **onde** e **o quê** (e quem corrige):

```
- [grave] art/personagens/ana.json quadro 3, (14, 22)–(17, 22): pé descola 2 px do chão no andar → animador
- [grave] cena chegada, plano 2, t=6.0s, (210, 152): Ana afunda 3 px no chão (y 150 → 153) → diretor-de-cena
- [aviso] lint orfao (9, 4): pixel #c98a6e isolado na testa
- [aviso] storyboard plano 4: caixa de diálogo cobre o retrato do mestre → posicao "cima"
```

Feche com um veredito: **aprovado**, **aprovado com avisos** ou **refazer** (graves).

## 5. Pedidos do estúdio

`pedidos/*.md` com `estado: aberto`: leia o `.md` e a imagem anotada (Read); cada marca
numerada tem coordenadas. A revisão confirma o problema e diz onde mexer; a correção
segue a skill da peça (`pixel-art`, `pixel-personagem`, `pixel-cena`); quem corrige roda
`acervo indexar` e troca para `estado: feito`.

## 6. Armadilhas

- O lint é aviso, não regra: não "corrija" olhos, brilhos e pontos de luz intencionais.
- Preview ampliado engana: sempre olhe também o 1x.
- Storyboard mostra só início/meio/fim: ação rápida entre eles pede `quadro --t`.
- Coordenada da imagem ampliada ≠ pixel da arte: divida pela escala (o storyboard é
  reduzido; use `quadro --escala 1` para pixel lógico exato).
- Agente: o `revisor-visual` executa esta skill e não edita arquivos.

## Nível mínimo (guia visual)

Antes de desenhar, gerar ou revisar, leia `docs/estilo/guia-visual.md` e abra 2–3 referências do mesmo
tipo em `refs/estilo-referencias/` (índice por tipo e tag em `docs/estilo/referencias.json`). A entrega só
passa se cumprir o checklist do guia e "aguentar" lado a lado com as referências; arte simples, chapada
ou com olho de anime volta para ajuste.

## Ciclo do crítico (melhoria contínua)

Toda arte de entrega passa pelo `critico-de-arte`: quem cria (desenhista, cenógrafo,
animador ou a via de IA) entrega a versão N → crítico dá NOTA (0,4 × técnica de
`estilo comparar` + 0,6 × rubrica visual) e melhorias com coordenadas → quem cria aplica →
volta N+1. Aprova só com **NOTA ≥ 95 e nenhum critério < 8**. Máximo de 6 voltas; sem
aprovação, o autor recebe a melhor versão + a última crítica + o que falta. Críticas em
`out/criticas/<arte>-v<N>.md`; evolução das notas em `out/criticas/<arte>-evolucao.md`.
O `revisor-visual` é o checklist rápido entre voltas; o `critico-de-arte`, a nota final.
Antes de criar, leia a análise das referências do mesmo tipo (`docs/estilo/analises/<n>.md`)
e siga as receitas de `docs/estilo/estilo-pixelforge.md`: elas são exemplos de criação.
