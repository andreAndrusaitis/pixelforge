# Roadmap do PixelForge

Rumo: de gerador de pixel art para um **estúdio de pixel local**, operado pelo
Claude Code (skills + agentes) e por uma **interface web local**. Projeto pessoal,
roda na máquina do autor; serve para a `coletanea` e para qualquer outro projeto
(jogos, protótipos, ilustrações).

Princípio: o motor é **genérico** (não conhece livros nem universos). Quem traz o
contexto é o projeto que o usa (ex.: a skill `/filmar` da coletânea).

Legenda: ⬜ ideia · 🟨 em design · 🟩 feito

---

## 1. Motor

### Arte
- 🟩 Spec JSON, scripts Python, conversão de foto, exportações, compare.
- 🟩 **Folha de personagem**: um personagem = retrato + sprite + animações, gerados do mesmo
  "modelo" (paleta, proporções, roupa), para o rosto/corpo nunca mudar entre artes.
- 🟩 **Personagem em camadas** (corpo, cabeça, cabelo, roupa, acessório) → variações
  (roupa nova, cicatriz, idade) sem redesenhar; expressões do retrato (neutro, feliz,
  bravo, triste, surpreso) trocando só olhos/boca.
- 🟩 **Geradores de animação**: ciclo de andar 4/6 quadros a partir da pose parada,
  piscar, respirar (idle), falar; olhando para 4 direções.
- 🟩 **Troca de paleta** (palette swap): dia/noite/pôr do sol, uniforme de cada casa,
  versão "fantasma"; rampas de sombra automáticas por cor.
- 🟩 **Sombreamento e contorno automáticos** a partir de arte chapada (luz de um lado,
  selout, anti-alias manual).
- 🟩 **Tilesets e autotile** (chão, parede, água) para montar cenários grandes.
- 🟩 **Fonte bitmap com acentos** (também usada nos diálogos das cenas).
- 🟩 Importar/exportar **Aseprite** (`.ase`/`.json`) e sprite sheets para Godot/Unity.
- 🟩 **Via de IA de imagem local** (`ia gerar` / `ia pixelizar` / `ia variar`, extra `[imagem-ia]`):
  SDXL Lightning + LoRA de pixel art na GPU do autor (fp8, cabe em 8 GB) faz o rascunho
  (texto, imagem → imagem ou referência de personagem por IP-Adapter); o PixelForge
  detecta a grade do pseudo-pixel, reduz por moda/mediana, quantiza (k-means OKLab ou
  paleta da cena) e limpa → spec JSON editável. Segundo caminho, ao lado do desenho por código.
- 🟩 **Estilo do autor dentro da via de IA**: refs de estilo por preset (IP-Adapter só nas camadas
  de estilo), receitas no prompt/negativo, folha arte + 3 refs com nota técnica, LoRA de estilo
  treinado localmente nas refs (`ia treinar`) e ciclo por notas (`ia gerar --ciclo`).

### Cena (vídeo) — `docs/specs/2026-10-21-pixelforge-cena-design.md`
- 🟩 Etapa 1: roteiro, cenário com parallax, câmera, storyboard, quadro, GIF/WebP/MP4
  (`pixelforge/scene/`, demo em `art/examples/cena-demo/`).
- 🟩 Etapa 2: atores (animações, âncora, espelho, andar, ordem por profundidade).
- 🟩 Etapa 3: diálogo (caixa, retrato, máquina de escrever).
- 🟩 Etapa 4: efeitos (chuva, neblina, partículas, luz de tocha, dia/noite) e transições.
- 🟩 Etapa 5: som na cena (bloco `audio`: trilha, ambiente, efeitos em instantes/planos/ações,
  falas com voz por IA ou bipes) mixado no MP4 (`pixelforge/scene/sound.py`).
- 🟩 Legenda/narração em texto sobre o vídeo; títulos de abertura ("Capítulo 7") (`scene/text.py`).
- 🟩 Câmera "cinema": seguir ator com folga, enquadramentos prontos (plano geral, médio, close),
  corte para close do retrato ou do ator durante o diálogo.

### Vídeo por IA — `docs/specs/2026-10-22-pixelforge-video-ia.md`
- 🟩 **Imagem → vídeo local**: Wan 2.2 TI2V-5B (Apache-2.0) em GGUF Q8 + UMT5 4 bits, 8 GB de VRAM
  (`pixelforge/ai_video/`, extra `[video-ia]`, `video-ia baixar|clipe`).
- 🟩 **Pixelização temporal**: grade fixa, paleta travada, mediana temporal, histerese de cor,
  limpeza de órfãos, fps 8–12, região (`video-ia pixelizar`).
- 🟩 **Animação de sprite por IA** (`video-ia sprite`): parado/andar/falar → spec com `animations` + `anchor`.
- 🟩 **"ia" no roteiro** (plano: quadro/imagem/sprite; camada do cenário), cache por hash e
  nova semente se a nota técnica (`estilo comparar`) < 85.

### Som
- 🟩 **Efeitos chiptune procedurais** (estilo sfxr: passo, pulo, magia, porta, golpe) —
  numpy puro, determinístico, combina com o pixel.
- 🟩 **Trilha por IA local**: ACE-Step 1.5 (MIT, roda com < 8 GB de VRAM) a partir de
  descrição ("tema misterioso, cravo e cordas, 90 bpm, loop").
- 🟩 **Voz por IA local**: Kokoro TTS (vozes em português) para narração/falas.
- ⬜ **Efeitos por IA** (opcional): Stable Audio Open para ambientes (chuva, multidão, floresta).
- Dependências pesadas (torch, modelos) num extra separado: `pip install -e .[audio-ia]`.

### Acervo
- 🟩 **Biblioteca de assets** com índice (`art/acervo.json`): nome, tipo (personagem,
  cenário, objeto, cena), tags, projeto de origem, versão, miniatura.
- 🟩 Busca por tag/nome (CLI e interface); reaproveitar em cenas novas.
- 🟩 Versões: `heroi_v2` herda de `heroi_v1`, histórico visível.

### Qualidade
- 🟩 **Decomposição técnica** (`estilo analisar`): grade real do pixel, paleta e rampas, valor, blocos, contorno, luz, composição, figura; 33 referências decompostas em `docs/estilo/analises/`.
- 🟩 **Crítico de arte** (`estilo comparar` + agente `critico-de-arte`): nota 0–100 contra as referências, aprova só ≥ 95; ciclo de melhoria contínua com quem cria.
- 🟩 **Guia visual / nível mínimo** (`docs/estilo/`): 33 referências do autor indexadas por tipo e tag; checklist de entrega ligado ao CLAUDE.md, às skills e aos agentes.
- 🟩 Testes de imagem de referência ("golden"): quadros de uma cena em `tests/golden/`,
  comparados pixel a pixel (`python -m pixelforge golden [--regravar]`).
- 🟩 **Lint de pixel art**: pixels órfãos, contorno quebrado, cores demais,
  banding, "jaggies" em linhas, contraste baixo da silhueta.

---

## 2. Claude Code: skills e agentes

### Skills (em `.claude/skills/`)
| Skill | Para quê |
|---|---|
| 🟩 `pixel-art` | uma arte por descrição ou foto (existe) |
| 🟩 `pixel-personagem` | folha de personagem: retrato + sprite + animações + paleta, a partir de descrição ou ficha |
| 🟩 `pixel-cenario` | cenários em camadas e tilesets |
| 🟩 `pixel-cena` | diretor: momento → planos → roteiro → storyboard → revisão → vídeo |
| 🟩 `pixel-som` | efeitos, trilha e voz para uma cena |
| 🟩 `pixel-revisao` | checklist visual (silhueta, leitura em tamanho real, paleta, consistência com a folha) |

### Agentes (subagentes em `.claude/agents/`)
| Agente | Papel |
|---|---|
| 🟩 `diretor-de-cena` | decide planos, ritmo, câmera; escreve o roteiro |
| 🟩 `desenhista` | sprites e retratos seguindo a folha do personagem |
| 🟩 `cenografo` | cenários, camadas, tilesets |
| 🟩 `animador` | ciclos de animação e ações dos atores |
| 🟩 `sonoplasta` | efeitos, trilha, voz |
| 🟩 `revisor-visual` | lê previews/storyboards e devolve problemas com coordenadas; não desenha |

Fluxo típico: diretor → (desenhista ∥ cenógrafo ∥ sonoplasta) → animador → revisor → render.

### Comandos
🟩 `/personagem`, `/cenario`, `/cena`, `/som`, `/acervo`, `/revisar` (`.claude/commands/`).

Equipe, fluxo e contrato de retorno (`STATUS / ARQUIVOS / RESUMO / PROBLEMAS`): `docs/agentes.md`.

### Integração
- 🟩 **Servidor MCP local** (extra `[mcp]`, `python -m pixelforge mcp`): ferramentas `render`,
  `quadro`, `storyboard`, `cena`, `personagem`, `lint`, `acervo_buscar`, `som_efeito` para
  outros projetos (ex.: coletânea) chamarem o motor sem shell; caminhos presos ao repositório.

---

## 3. Interface local (web)

Servidor local (`python -m pixelforge studio`, só stdlib `http.server` + HTML/JS
estático, sem framework) aberto no navegador / painel do Claude Code.

- 🟩 **Galeria do acervo**: miniaturas, filtros por tag/projeto, versões lado a lado.
- 🟩 **Visualizador de sprite**: zoom inteiro, grade, fundo xadrez, tocar animações,
  trocar paleta ao vivo.
- 🟩 **Editor de retoque**: lápis/borracha/conta-gotas/balde direto na spec JSON
  (o Claude desenha, o autor retoca).
- 🟩 **Linha do tempo da cena**: arrastar o cursor (scrub), ver o quadro, planos como
  blocos, tocar o vídeo, storyboard.
- 🟩 **Pedidos ao Claude**: caixa "o que mudar" que grava `pedidos/<data>.md`
  (com arte, quadro e coordenadas marcadas); o Claude lê e aplica.
- 🟩 Comparador antes/depois e com foto de referência (`compare`).

---

## 4. Ordem sugerida

1. 🟩 Cena etapa 1 (base de vídeo)
2. Interface: visualizador + galeria (ajuda a revisar tudo daqui para frente) ← **próximo**
3. Folha de personagem + `pixel-personagem` + `revisor-visual`
4. Cena etapas 2–3 (atores e diálogo) + `pixel-cena` / `diretor-de-cena`
5. Efeitos chiptune + cena etapa 4
6. Som por IA (ACE-Step, Kokoro) + etapa 5
7. Acervo, tilesets, camadas de personagem, editor de retoque, MCP

## Retomar (pausado em 2026-10-22)

1. ⬜ **Vídeo por IA da cena do portão** (`art/coletanea/veu/cenas/cap01-portao/`): a geração real com Wan 2.2 está lenta
   (vários minutos por clipe de 2 s); ajustar passos/área e rodar a prova.
2. ⬜ **Martim e Seu Geraldo ≥ 95 no crítico** (hoje 84–88): base da IA + pintura por código; foco em pose, cabelo
   crespo e volume da roupa. Specs atuais: `art/coletanea/veu/martim_final*.json`, `geraldo_final*.json`.
3. ⬜ **Renderizar a cena do cap 01** com os personagens finais e o vídeo por IA; entregar o MP4.

Cuidado: uma tarefa de GPU por vez (8 GB de VRAM, 16 GB de RAM) e pouco espaço livre no C:.
