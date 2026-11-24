---
name: pixel-cenario
description: Cenários de pixel art no PixelForge — cenário em camadas com parallax (céu, fundos, chão, primeiro plano) para cenas, e tilesets com autotile + mapas montados por grade. Use para "faz o cenário da floresta", "um vale ao entardecer para a cena", "tileset de grama/água/muro", "monta o mapa da vila", troca de hora do dia de um cenário (noite, pôr do sol). Para a cena animada (câmera, atores, diálogo) use pixel-cena; para um objeto ou arte avulsa, pixel-art.
---

# Cenários e tilesets (PixelForge)

Dois jeitos de fazer cenário, combináveis:

- **Camadas com parallax** (para cenas): cada camada é uma arte `.py`/`.json` e o
  cenário `cenario.json` diz a ordem, o `parallax` e a posição. Exemplo completo:
  `art/examples/cena-demo/` (`cenario.json`, `ceu.py`, `montanhas_*.py`, `chao.py`, `frente.py`).
- **Tileset + mapa** (para chão/paredes/água grandes e regulares): `*.tileset.json`
  gera os tiles com autotile; `*.mapa.json` monta o mapa por uma grade de caracteres.
  Exemplos: `art/examples/campo.tileset.json`, `art/examples/vila.mapa.json`.

Referência: docs/manual.md, "Cenário em camadas" e "Tilesets e mapas".

## 1. Entrevista

Com `AskUserQuestion`, só o que não foi dito:

| Pergunta | Opções típicas |
|---|---|
| **Uso** | Fundo de cena com câmera (camadas) · Mapa de jogo visto de cima (tiles) · Ilustração parada |
| **Lugar e clima** | floresta, vila, interior, cidade, praia… · dia, entardecer, noite, chuva, neblina |
| **Resolução da cena** | `hd` 320×180 (padrão) · `gba` 240×160 · `snes` 256×224 · `hd2` 480×270 · `hd3` 640×360 |
| **Movimento de câmera** | parada · panorâmica horizontal (mundo mais largo) · tilt vertical (mundo mais alto) |
| **Paleta** | pico8, endesga32, sweetie16… · cores próprias (4–32) |

O tamanho do **mundo** sai da resposta: tela 320×180 com panorâmica de 2 telas →
`size` 640×180; com tilt → altura maior.

## 2. Passos — camadas

1. Pasta `art/cenarios/<lugar>/` (ou `art/<cena>/` junto do roteiro).
2. Uma arte por camada, de trás para a frente, por script `.py` (`Canvas`; veja a
   skill `pixel-art`, seção 2):
   - **céu** (parallax ~0.1, pode ter 2+ frames para estrelas piscando);
   - **fundos** (0.3–0.6) com `repetir: "x"` → a arte precisa **emendar** (coluna 0 =
     continuação da última);
   - **chão** (1.0) = o mundo onde os atores pisam; largura = `size` do mundo;
   - **primeiro plano** (> 1, `frente: true`) desenhado por cima dos atores (capim, galhos).
3. Renderize e revise **cada camada** como arte comum:
   `python -m pixelforge render art/cenarios/<lugar>/chao.py` → Read do `_preview.png`.
4. `cenario.json`:
   ```json
   { "name": "vale", "size": [640, 240],
     "camadas": [
       { "arte": "ceu", "parallax": 0.1 },
       { "arte": "montanhas", "parallax": 0.4, "pos": [0, 18], "repetir": "x" },
       { "arte": "chao", "pos": [0, 60] },
       { "arte": "capim", "parallax": 1.3, "pos": [0, 232], "repetir": "x", "frente": true }
     ] }
   ```
   Na tela, a camada fica em `pos − câmera × parallax`. `fps` por camada anima artes
   com frames.
5. **Ver o cenário montado** sem atores: um roteiro mínimo de revisão
   (`art/cenarios/<lugar>/_teste.json`) com `"cenario": "cenario"` e um plano que
   percorre o mundo (`"camera": {"de": [0, 0], "para": [320, 0], "curva": "suave"}`), e
   ```bash
   python -m pixelforge storyboard art/cenarios/<lugar>/_teste.json
   python -m pixelforge quadro art/cenarios/<lugar>/_teste.json --t 2 --escala 2
   ```
6. **Hora do dia**: `python -m pixelforge recolor art/cenarios/<lugar>/chao.py --map noite --to-spec art/cenarios/<lugar>/chao_noite.json`
   (tintas: dia, noite, por-do-sol, fantasma, sepia) ou, na cena, o efeito `tinta`.

## 2b. Passos — tileset e mapa

1. `art/cenarios/<lugar>.tileset.json`: `tile` (px) e `terrenos` com `cor`, `borda`,
   `textura` (liso, pontos, grama, ondas, tijolo), `modo` (`blob47` cantos internos,
   `blob16` 4 vizinhos, `cheio`), `recuo`, `espessura`; ou `imagem` (folha desenhada à
   mão, 8 colunas na ordem da folha gerada).
2. `python -m pixelforge tileset art/cenarios/<lugar>.tileset.json` → folha +
   `<nome>_tiles.json` (máscara de cada tile). Read do preview.
3. `art/cenarios/<lugar>.mapa.json`: `tileset`, `base`, `legenda` (caractere → terreno),
   `grade` (linhas de mesma largura), `ordem` opcional.
4. `python -m pixelforge tilemap art/cenarios/<lugar>.mapa.json` → mapa em `out/<nome>/`.
   O PNG do mapa pode virar a camada `chao` de um cenário.
5. Para Godot/Unity: `python -m pixelforge aseprite export <arte> --layout linhas`.

## 3. Ciclo desenhar → pré-visualizar → ajustar

Read de cada `_preview.png` e do storyboard de teste. Confira:

- profundidade: quanto mais longe, menos contraste e mais frio/claro (perspectiva
  atmosférica); o chão tem o maior contraste;
- emendas: nenhuma costura visível nas camadas `repetir` (olhe o storyboard no meio da
  panorâmica);
- horizonte coerente entre camadas (as montanhas não "flutuam" sobre o chão);
- espaço para atores: faixa do chão livre e legível, com contraste para um sprite de
  ~32 px; caixa de diálogo (embaixo) não esconde o que importa;
- sem buracos: nenhuma área do `fundo` aparecendo onde não devia ao mover a câmera;
- `lint` nas camadas (`python -m pixelforge lint art/cenarios/<lugar>/*.json`) — em
  cenário, `cores` e `banding` costumam ser os relevantes.

## 4. Pronto quando

- cada camada revisada; storyboard de teste sem costura, buraco ou horizonte quebrado;
- `cenario.json` com `size` do mundo e camadas na ordem certa;
- autor aprovou (uma versão por vez); `acervo indexar` rodado (camadas viram `cenario`).

## 5. Armadilhas

- `.py` de camada grande: use `rect`/`polygon`/`gradient`, não pixel a pixel; mantenha
  posições inteiras.
- Arte de `repetir: "x"` com largura diferente do padrão que se repete gera costura.
- Parallax > 1 sem `frente: true` fica atrás dos atores.
- Sem `size`, o mundo é a extensão das camadas de parallax 1 — a câmera pode parar cedo.
- Gradiente de céu: `gradient` com poucos tons + dithering; muitos tons = banding.
- Agente: o `cenografo` executa esta skill.

## Nível mínimo (guia visual)

Antes de desenhar, gerar ou revisar, leia `docs/estilo/guia-visual.md` e abra 2–3 referências do mesmo
tipo em `refs/estilo-referencias/` (índice por tipo e tag em `docs/estilo/referencias.json`). A entrega só
passa se cumprir o checklist do guia e "aguentar" lado a lado com as referências; arte simples, chapada
ou com olho de anime volta para ajuste.
