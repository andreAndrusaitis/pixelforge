# Repintura por código sobre as bases da via de IA (ciclo do crítico)

Bases: `art/coletanea/veu/*_ia_final_*` (branch claude/ia-imagem-bd2583, d9ca488). Scripts em
`art/coletanea/veu/final/*_repinta.py`. Rubrica de `.claude/agents/critico-de-arte.md`, comparando lado a
lado com as refs mais próximas (1, 3, 11, 14, 18, 19, 20, 21, 22).

| Peça | Base IA (final) | Volta | Técnica | Rubrica | Final | Veredito |
|---|---|---|---|---|---|---|
| Geraldo corpo (com/sem chapéu) | 81,8 | 1 (aba, mãos, cicatriz, cabelo) | 94,9 | 81,5 | 86,9 | REFAZER |
| | | 2 (rim pontual duas temperaturas, pele parda) | 94,9 | 82,0 | **87,2** | REFAZER |
| Geraldo retrato | 83,0 | 1 (pele parda, olho sem esclera, rim) | 93,5 | 84,8 | **88,3** | REFAZER |
| Martim corpo | 80,4 | 1 (0,82×, calça, crespo, pele parda, olhos) | 95,4 | 77,0 | **84,4** | REFAZER |
| Martim retrato | 73,6 | 1 (crespo na máquina, pele parda, rim) | 91,7 | 78,8 | **83,9** | REFAZER |

Rubricas (silhueta, pose, rosto, blocos, paleta, contorno, luz, materiais, composição, não amador):
- Geraldo corpo v2: 8,5 · 7,5 · 8 · 8 · 8 · 8 · 8 · 8 · 8 · 8
- Geraldo retrato v1: 8,5 · 8,5 · 8,5 · 8,5 · 8,5 · 8 · 8,5 · 8,5 · 8,5 · 8,5
- Martim corpo v1: 8 · 8 · 7,5 · 7,5 · 8 · 7,5 · 7,5 · 7,5 · 8 · 7,5
- Martim retrato v1: 8 · 7,5 · 8 · 8 · 8 · 7,5 · 8 · 7,5 · 8 · 8

O que ainda segura abaixo de 95 (nenhum critério chegou a 9+):
1. Pose: as bases são quase frontais e paradas (Geraldo "boneco" de frente; Martim com o andar herdado da IA).
   Mudar a pose exige redesenhar o corpo, não repintar.
2. Martim corpo: a redução 0,82× por vizinho mais próximo perde a finura dos blocos (cabelo e mãos); a calça
   repintada ainda tem blocos geométricos.
3. Geraldo: o chapéu na mão (girado da base) é pequeno e pouco legível; a camisa tem textura da IA com
   ruído em vez de 2–3 dobras grandes por lado.
4. Retratos: falta a luz de cena (laranja de trás) dominando como no 22; o retrato do Geraldo não tem chapéu
   (a base veio sem).
