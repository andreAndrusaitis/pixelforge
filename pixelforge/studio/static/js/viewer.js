// Visualizador: zoom inteiro, grade, xadrez, animações (frames/fps/animations) e paleta ao vivo.

import { $, el, get, notice, post } from "./api.js";
import { animationsOf, drawGrid, fitZoom, remapColors, specFrames, stageWidth } from "./pixels.js";

let app;
let current = null;   // resposta de /api/arte
let frames = [];
let colors = {};      // cores exibidas (podem estar trocadas)
let anims = {};
let animName = "";
let step = 0;
let timer = null;

export function init(appRef) {
  app = appRef;
  const palette = $("#v-paleta");
  for (const name of app.state.paletas) palette.append(el("option", { value: name }, name));
  palette.addEventListener("change", swapPalette);
  for (const id of ["#v-zoom", "#v-grade", "#v-xadrez"]) $(id).addEventListener("input", draw);
  $("#v-anim").addEventListener("change", (e) => selectAnimation(e.target.value));
  $("#v-fps").addEventListener("change", () => timer && play(true));
  $("#v-tocar").addEventListener("click", () => (timer ? stop() : play()));
  $("#v-ant").addEventListener("click", () => { stop(); move(-1); });
  $("#v-prox").addEventListener("click", () => { stop(); move(1); });
  $("#v-retocar").addEventListener("click", () => app.go("retocar", { arquivo: current.arquivo }));
  $("#v-pedido").addEventListener("click", () => app.go("pedidos", { arquivo: current.arquivo, quadro: frameIndex() }));
  $("#v-comparar").addEventListener("click", () => {
    const entry = app.entry(current.arquivo);
    const parent = entry?.herda && app.entry(entry.herda);
    app.go("comparar", parent ? { a: parent.arquivo, b: current.arquivo } : { b: current.arquivo });
  });
  $("#v-render").addEventListener("click", renderFiles);
}

export async function show(params) {
  const section = $("#ver");
  if (!params.arquivo) {
    if (!current) return toggle(section, false);
    return;
  }
  stop();
  current = await get("/api/arte", { arquivo: params.arquivo });  // sempre fresca: pode ter sido retocada
  toggle(section, true);
  setup();
}

export function hide() {
  stop();
}

function toggle(section, full) {
  section.querySelector("[data-vazio]").hidden = full;
  section.querySelector("[data-cheio]").hidden = !full;
}

function setup() {
  $("#v-titulo").textContent = current.nome;
  const warn = $("#v-aviso");
  warn.hidden = !current.aviso;
  warn.textContent = current.aviso ? `Sem spec para visualizar: ${current.aviso}` : "";
  if (!current.spec) return;
  frames = specFrames(current.spec);
  colors = { ...current.cores };
  $("#v-paleta").value = "";
  const [w, h] = [frames[0][0].length, frames[0].length];
  $("#v-zoom").value = fitZoom(w, h, Math.min(512, stageWidth("#ver .palco")));
  $("#v-info").textContent = `${w}×${h} · ${frames.length} quadro(s) · ${current.arquivo}` +
    (current.editavel ? "" : " · (gerada a partir do script/imagem)");
  anims = animationsOf(current.spec, frames.length);
  const select = $("#v-anim");
  select.replaceChildren(...Object.keys(anims).map((n) => el("option", { value: n }, n)));
  const preferred = Object.keys(anims).find((n) => n === "parado") || Object.keys(anims)[0];
  select.value = preferred;
  selectAnimation(preferred);
  renderVersions();
  renderSwatches();
}

function selectAnimation(name) {
  animName = name;
  step = 0;
  $("#v-fps").value = anims[name].fps;
  draw();
  if (timer) play(true);
}

function frameIndex() {
  const list = anims[animName]?.frames || [0];
  return list[step % list.length] ?? 0;
}

function move(delta) {
  const n = anims[animName].frames.length;
  step = (step + delta + n) % n;
  draw();
}

function play(restart = false) {
  if (timer && !restart) return;
  clearInterval(timer);
  const fps = Math.max(1, Number($("#v-fps").value) || 8);
  timer = setInterval(() => move(1), 1000 / fps);
  $("#v-tocar").textContent = "⏸ pausar";
}

function stop() {
  clearInterval(timer);
  timer = null;
  const button = $("#v-tocar");
  if (button) button.textContent = "▶ tocar";
}

function draw() {
  if (!current?.spec) return;
  const zoom = Number($("#v-zoom").value);
  $("#v-zoom-n").textContent = `${zoom}×`;
  const grid = frames[frameIndex()] || frames[0];
  drawGrid($("#v-canvas"), grid, colors, { zoom, grid: $("#v-grade").checked, checker: $("#v-xadrez").checked });
  const list = anims[animName].frames;
  $("#v-quadro").textContent = `quadro ${frameIndex()} (${(step % list.length) + 1}/${list.length})`;
}

async function swapPalette() {
  const name = $("#v-paleta").value;
  if (!name) {
    colors = { ...current.cores };
  } else {
    const palette = await get("/api/paleta", { nome: name });
    colors = remapColors(current.cores, palette.cores);
  }
  renderSwatches();
  draw();
}

function renderSwatches() {
  const box = $("#v-cores");
  box.replaceChildren();
  for (const [key, hex] of Object.entries(colors)) {
    if (key === "." || hex.endsWith("00")) continue;
    const input = el("input", { type: "color", value: hex.slice(0, 7), hidden: true });
    input.addEventListener("input", () => {
      colors[key] = input.value + hex.slice(7);
      swatch.style.background = input.value;
      draw();
    });
    const swatch = el("span", { class: "cor", title: `${key} = ${hex}`, onclick: () => input.click() }, key);
    swatch.style.background = hex;
    box.append(swatch, input);
  }
}

function renderVersions() {
  const box = $("#v-versoes");
  box.replaceChildren();
  const entry = app.entry(current.arquivo);
  if (!entry) return;
  const family = app.catalog.filter((e) => e.base === entry.base).sort((a, b) => a.versao - b.versao);
  if (family.length < 2) return;
  box.append("Versões: ", ...family.map((e) => e.arquivo === current.arquivo
    ? el("strong", {}, `v${e.versao} `)
    : el("a", { href: `#ver?arquivo=${encodeURIComponent(e.arquivo)}` }, `v${e.versao}`)));
}

async function renderFiles() {
  try {
    const data = await post("/api/render", { arquivo: current.arquivo });
    notice(`renderizado: ${data.saidas.length} arquivo(s) em out/${data.nome}/`);
  } catch (err) {
    notice(err.message, true);
  }
}
