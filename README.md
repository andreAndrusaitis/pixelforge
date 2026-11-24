<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/vitrine/capa-escuro.svg">
  <img alt="pixelforge: pixel art gerada por código, de PNG a GIF animado" src="docs/vitrine/capa-claro.svg">
</picture>

Um motor de pixel art em Python. Descreva uma arte em dados ou em código, ou entregue uma foto, e ele desenha, anima, monta cenas com câmera e trilha sonora e exporta em PNG, WebP, GIF, SVG e MP4. Foi projetado para trabalhar junto com o Claude Code, que escreve os roteiros e revisa o resultado.

<p align="center">
  <img src="docs/vitrine/cena.gif" width="640" alt="Cena animada: um viajante atravessa um vale ao anoitecer até chegar a uma cabana iluminada">
</p>

<p align="center"><sub>Cena de 29 segundos gerada a partir de um <a href="art/examples/cena-demo/cena-demo.json">roteiro JSON</a>: cenário em camadas, atores, diálogo, títulos e som.</sub></p>

## O que ele faz

| | |
|---|---|
| **Desenha** | A arte é uma grade de caracteres em JSON ou um script Python com primitivas de desenho. |
| **Converte fotos** | Encaixe na grade, redução de cores em OKLab, dithering, remoção de fundo e contorno. |
| **Cria personagens** | De uma ficha saem o sprite, o retrato, as expressões e as animações. |
| **Monta mapas** | Tilesets com autotile e mapas a partir de texto. |
| **Dirige cenas** | Parallax, câmera, atores, diálogo, efeitos, transições e legendas. |
| **Faz o som** | Efeitos chiptune, música por código e mixagem direto no vídeo. |
| **Revisa** | Um lint de pixel art que aponta problemas com coordenadas. |

## Galeria

<table align="center">
  <tr>
    <td align="center"><img src="docs/vitrine/slime.gif" height="110" alt="Slime pulando"></td>
    <td align="center"><img src="docs/vitrine/lia-andar.gif" height="110" alt="Personagem Lia andando"></td>
    <td align="center"><img src="docs/vitrine/lia-fala.gif" height="110" alt="Retrato da Lia falando"></td>
    <td align="center"><img src="docs/vitrine/pocao.png" height="110" alt="Poção"></td>
    <td align="center"><img src="docs/vitrine/viajante.png" height="110" alt="Retrato do viajante"></td>
  </tr>
  <tr>
    <td align="center">spec JSON</td>
    <td align="center">animação</td>
    <td align="center">expressões</td>
    <td align="center">script Python</td>
    <td align="center">retrato</td>
  </tr>
</table>

<p align="center"><img src="docs/vitrine/mapa.png" width="520" alt="Mapa de vila montado a partir de texto"></p>
<p align="center"><sub>Mapa montado a partir de uma <a href="art/examples/vila.mapa.json">grade de caracteres</a>, com bordas escolhidas pelo autotile.</sub></p>

## Estúdio

Uma interface web local para ver o acervo, tocar animações, retocar pixels e comparar versões. Usa só a biblioteca padrão do Python e funciona sem internet.

<p align="center"><img src="docs/vitrine/estudio.png" width="820" alt="Galeria do estúdio com as artes do acervo"></p>

## Como é por dentro

```mermaid
flowchart LR
  A[Spec JSON] --> M
  B[Script Python] --> M
  C[Foto de referência] --> Q[Conversão] --> M
  M[Motor de arte] --> S[Sprites e mapas]
  S --> K[Motor de cena]
  R[Roteiro JSON] --> K
  N[Som por código] --> K
  K --> V[GIF, WebP e MP4]
  M --> P[PNG, SVG e GIF]
```

- **Arte como dados.** Uma arte é texto: dá para versionar, comparar e gerar por programa.
- **Resultado reproduzível.** Cenas são comparadas com imagens de referência a cada mudança.
- **Poucas dependências.** O núcleo usa só Pillow e numpy. Vídeo, som e imagem por IA são extras opcionais.
- **Testado.** 267 testes passando, do desenho ao áudio.

## Saiba mais

- [Manual completo](docs/manual.md): comandos, formatos e opções
- [Desenho do motor de cena](docs/specs/2026-10-21-pixelforge-cena-design.md)
- [Guia visual](docs/estilo/guia-visual.md)

## Licença

Código visível apenas para leitura. Todos os direitos reservados: não é permitido usar, copiar ou distribuir sem autorização. Veja [LICENSE](LICENSE).
