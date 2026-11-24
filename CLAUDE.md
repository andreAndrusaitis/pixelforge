# PixelForge — instruções para o Claude

- **Nível mínimo de qualidade**: nada de arte simples. Toda arte mira as referências do autor —
  leia `docs/estilo/guia-visual.md`, abra 2–3 imagens do mesmo tipo em `refs/estilo-referencias/`
  (índice em `docs/estilo/referencias.json`) antes de começar e compare lado a lado antes de entregar.
  Sem olho de anime; sombreamento em blocos, paleta contida, contorno seletivo, luz dramática.
- **Ciclo do crítico**: toda entrega passa pelo agente `critico-de-arte` (nota técnica de
  `estilo comparar` + rubrica visual) até **NOTA ≥ 95** (máx. 6 voltas; ver `docs/agentes.md`).
  As referências são **exemplos de criação**: antes de criar, leia as análises
  (`docs/estilo/analises/<n>.md`) e as receitas de `docs/estilo/estilo-pixelforge.md`.
  `estilo analisar` decompõe imagens; `analista-de-estilo` escreve as análises.
- Pedidos de pixel art → escolha a skill (`.claude/skills/<nome>/SKILL.md`):
  `pixel-art` (arte avulsa, foto → pixel; porta de entrada), `pixel-personagem` (folha:
  retrato + sprite + animações), `pixel-cenario` (camadas, tileset, mapa), `pixel-cena`
  (momento → planos → roteiro → storyboard → vídeo), `pixel-som` (efeitos, trilha, voz,
  mixagem), `pixel-revisao` (checklist visual + lint com coordenadas).
- Comandos: `/personagem`, `/cenario`, `/cena`, `/som`, `/acervo`, `/revisar`
  (`.claude/commands/`).
- Agentes (`.claude/agents/`): `diretor-de-cena`, `desenhista`, `cenografo`, `animador`,
  `sonoplasta`, `revisor-visual` (só lê). A sessão principal entrevista e coordena; fluxo
  diretor → (desenhista ∥ cenógrafo ∥ sonoplasta) → animador → revisor → render. Agentes
  não perguntam ao autor e devolvem `STATUS / ARQUIVOS / RESUMO / PROBLEMAS`
  (`docs/agentes.md`); dois agentes nunca editam o mesmo arquivo.
- Gere arte com `python -m pixelforge`: por código (padrão) ou pela **via de IA de imagem
  local** (`ia gerar` / `ia pixelizar` / `ia variar`, extra `[imagem-ia]`). IA de imagem só
  por essa via, na GPU do autor, **sempre seguida de pixelização e revisão**
  (`out/ia/<nome>/<nome>_folha.png` com Read: arte + 3 refs + nota técnica). Prefira
  `ia gerar --ciclo` (nota técnica ≥ 90) e depois o `critico-de-arte` (≥ 95). O LoRA de estilo
  (`ia treinar`) e o dataset das refs são de uso pessoal: nunca publique nem versione.
  Uma geração ou treino por vez na GPU (8 GB divididos com as outras sessões). Nada de geradores online, apps externos
  ou imagens baixadas. Modelo restrito (licença/login no Hugging Face): não aceite; pergunte.
- Sempre abra `out/<nome>/<nome>_preview.png` com Read e revise antes de entregar.
- **Antes de gerar, entreviste o usuário** (seção 1 da skill) e entregue uma versão
  por vez; nada de variações não pedidas.
- Foto de pessoa: pergunte se é *personagem* (padrão do usuário: traduzir em personagem
  estilizado e reconhecível — Fluxo C) ou *fiel à foto* (preset `photo` + retoque).
  Fotos ficam em `refs/`.
- Artes do usuário vão em `art/`; não altere `art/examples/` sem pedido.
- Pedidos do estúdio web ficam em `pedidos/*.md` (`estado: aberto`): leia o texto, as
  marcas e a imagem anotada, aplique, rode `acervo indexar` e troque para `estado: feito`.
- Mudou código em `pixelforge/`? Rode `python -m unittest discover -s tests`.
- Dependências permitidas: stdlib, Pillow, numpy. Extras opcionais, importados sob
  demanda (sem eles o resto funciona): `[video]` (`imageio-ffmpeg`, MP4 das cenas),
  `[audio-ia]` (torch, kokoro… — voz, trilha e ambiente por IA local), `[imagem-ia]`
  (torch, diffusers — rascunho por IA de imagem local; a pixelização, `pixelforge/pixelize.py`,
  é só numpy + Pillow), `[mcp]` (SDK `mcp`,
  servidor `python -m pixelforge mcp`). Testes com `unittest` (sem pytest); testes de
  extras são pulados quando o extra não está instalado.
- Servidor MCP (`pixelforge/mcp_server.py`): ferramentas novas validam todo caminho com
  `inside()` (nada fora do repositório) e devolvem os arquivos gerados.
- Cenas (roteiro JSON → vídeo): `cena`, `quadro`, `storyboard`; sempre abra
  `out/<nome>/<nome>_storyboard.png` com Read e revise antes de entregar o vídeo.
- Textos de interface, mensagens de erro e docs em português.
