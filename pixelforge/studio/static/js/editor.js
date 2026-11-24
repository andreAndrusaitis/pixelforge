// Editor de retoque: lápis, borracha, conta-gotas, balde, desfazer/refazer.
// Trabalha nas chaves da spec; grava de volta pela API (formato dump_spec preservado).

import { $, el, get, notice, post } from "./api.js";
import { cellAt, drawGrid, fitZoom, framesToSpec, parseHex, specFrames, stageWidth, TRANSPARENT } from "./pixels.js";

let app;
let current = null;
let frames = [];
let palette = {};     // chave → valor como está na spec (ex.: "#ff004d", "transparent")
let colors = {};      // chave → "#rrggbbaa"
let frame = 0;
let tool = "lapis";
let key = null;
let undo = [];
let redo = [];
let dirty = false;
let stroke = null;    // {before, last}

export const isDirty = () => dirty;

export function init(appRef) {
  app = appRef;
  for (const button of document.querySelectorAll("#e-ferramentas [data-ferr]")) {
    button.addEventListener("click", () => setTool(button.dataset.ferr));
  }
  $("#e-zoom").addEventListener("input", draw);
  $("#e-grade").addEventListener("input", draw);
  $("#e-quadro").addEventListener("change", (e) => { frame = Number(e.target.value); draw(); });
  $("#e-desfazer").addEventListener("click", undoStep);
  $("#e-refazer").addEventListener("click", redoStep);
  $("#e-add-cor").addEventListener("click", addColor);
  $("#e-mudar-cor").addEventListener("click", changeColor);
  $("#e-salvar").addEventListener("click", () => save(false));
  $("#e-versao").addEventListener("click", () => save(true));

  const canvas = $("#e-canvas");
  canvas.addEventListener("pointerdown", pointerDown);
  canvas.addEventListener("pointermove", pointerMove);
  window.addEventListener("pointerup", pointerUp);
  canvas.addEventListener("contextmenu", (e) => e.preventDefault());
  document.addEventListener("keydown", shortcuts);
}

export async function show(params) {
  const section = $("#retocar");
  if (!params.arquivo) {
    section.querySelector("[data-vazio]").hidden = !!current;
    section.querySelector("[data-cheio]").hidden = !current;
    return;
  }
  if (current?.arquivo === params.arquivo && dirty) return;  // mantém o retoque em andamento
  if (dirty && !confirm("Descartar o retoque não salvo?")) return;
  await load(params.arquivo);
  section.querySelector("[data-vazio]").hidden = true;
  section.querySelector("[data-cheio]").hidden = false;
}

async function load(arquivo) {
  current = await get("/api/arte", { arquivo });
  undo = [];
  redo = [];
  setDirty(false);
  $("#e-titulo").textContent = `Retoque · ${current.nome}`;
  const warn = $("#e-aviso");
  const messages = [];
  if (!current.spec) messages.push(`Não dá para retocar: ${current.aviso}`);
  else if (!current.editavel) messages.push("Arte vem de script/imagem: o retoque é salvo como nova versão (.json).");
  else if (current.protegido) messages.push("art/examples/ é só leitura: salve como nova versão.");
  warn.hidden = !messages.length;
  warn.textContent = messages.join(" ");
  $("#e-salvar").disabled = !current.editavel || current.protegido;
  $("#e-versao").disabled = !current.spec;
  if (!current.spec) return;
  frames = specFrames(current.spec);
  palette = { ...current.spec.palette };
  colors = { ...current.cores };
  frame = 0;
  const [w, h] = [frames[0][0].length, frames[0].length];
  $("#e-zoom").value = fitZoom(w, h, Math.min(640, stageWidth("#retocar .palco")), 40);
  $("#e-info").textContent = `${w}×${h} · ${frames.length} quadro(s) · ${current.arquivo}`;
  $("#e-quadro").replaceChildren(...frames.map((_, i) => el("option", { value: i }, `quadro ${i}`)));
  key = Object.keys(colors).find((k) => k !== TRANSPARENT) || TRANSPARENT;
  setTool("lapis");
  renderSwatches();
  draw();
}

function setTool(name) {
  tool = name;
  for (const b of document.querySelectorAll("#e-ferramentas [data-ferr]")) b.classList.toggle("ativo", b.dataset.ferr === name);
}

function setDirty(value) {
  dirty = value;
  $("#e-estado").textContent = value ? "● alterações não salvas" : "";
}

function zoom() {
  return Number($("#e-zoom").value);
}

function draw() {
  if (!current?.spec) return;
  $("#e-zoom-n").textContent = `${zoom()}×`;
  drawGrid($("#e-canvas"), frames[frame], colors, { zoom: zoom(), grid: $("#e-grade").checked });
}

function renderSwatches() {
  const box = $("#e-cores");
  box.replaceChildren();
  for (const [k, hex] of Object.entries(colors)) {
    const transparent = k === TRANSPARENT || parseHex(hex)[3] === 0;
    const swatch = el("span", {
      class: `cor${k === key ? " sel" : ""}${transparent ? " vazia" : ""}`,
      title: `${k} = ${palette[k]}`,
      onclick: () => { key = k; if (tool === "borracha" || tool === "conta") setTool("lapis"); renderSwatches(); },
    }, k);
    if (!transparent) swatch.style.background = hex;
    box.append(swatch);
  }
  if (key && colors[key] && key !== TRANSPARENT) $("#e-nova-cor").value = colors[key].slice(0, 7);
}

// ----- pintura -------------------------------------------------------------

function inside(p) {
  return p.y >= 0 && p.x >= 0 && p.y < frames[frame].length && p.x < frames[frame][0].length;
}

function snapshot() {
  return frames[frame].map((row) => row.slice());
}

function pointerDown(event) {
  if (!current?.spec) return;
  const p = cellAt($("#e-canvas"), event, zoom());
  if (!inside(p)) return;
  const effective = event.button === 2 ? "borracha" : tool;
  if (effective === "conta") {
    key = frames[frame][p.y][p.x];
    renderSwatches();
    setTool("lapis");
    return;
  }
  stroke = { before: snapshot(), last: p, tool: effective, changed: false };
  if (effective === "balde") {
    stroke.changed = fill(p, key);
    finishStroke();
    return;
  }
  stroke.changed = paint(p, effective) || stroke.changed;
  $("#e-canvas").setPointerCapture(event.pointerId);
  draw();
}

function pointerMove(event) {
  if (!current?.spec) return;
  const p = cellAt($("#e-canvas"), event, zoom());
  if (inside(p)) {
    const k = frames[frame][p.y][p.x];
    $("#e-pos").textContent = `x ${p.x}, y ${p.y} · chave ${k} (${palette[k] ?? "?"})`;
  }
  if (!stroke) return;
  // linha entre o último ponto e o atual (Bresenham) para não deixar falhas
  let { x: x0, y: y0 } = stroke.last;
  const { x: x1, y: y1 } = p;
  const dx = Math.abs(x1 - x0), dy = -Math.abs(y1 - y0);
  const sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1;
  let err = dx + dy;
  while (true) {
    if (inside({ x: x0, y: y0 })) stroke.changed = paint({ x: x0, y: y0 }, stroke.tool) || stroke.changed;
    if (x0 === x1 && y0 === y1) break;
    const e2 = 2 * err;
    if (e2 >= dy) { err += dy; x0 += sx; }
    if (e2 <= dx) { err += dx; y0 += sy; }
  }
  stroke.last = p;
  draw();
}

function pointerUp() {
  if (stroke) finishStroke();
}

function finishStroke() {
  if (stroke.changed) {
    undo.push({ frame, grid: stroke.before });
    if (undo.length > 200) undo.shift();
    redo = [];
    setDirty(true);
  }
  stroke = null;
  draw();
}

function paint(p, which) {
  const value = which === "borracha" ? TRANSPARENT : key;
  if (frames[frame][p.y][p.x] === value) return false;
  frames[frame][p.y][p.x] = value;
  return true;
}

function fill(start, value) {
  const grid = frames[frame];
  const target = grid[start.y][start.x];
  if (target === value) return false;
  const stack = [start];
  while (stack.length) {
    const { x, y } = stack.pop();
    if (y < 0 || x < 0 || y >= grid.length || x >= grid[0].length || grid[y][x] !== target) continue;
    grid[y][x] = value;
    stack.push({ x: x + 1, y }, { x: x - 1, y }, { x, y: y + 1 }, { x, y: y - 1 });
  }
  return true;
}

function undoStep() {
  const last = undo.pop();
  if (!last) return;
  redo.push({ frame: last.frame, grid: frames[last.frame].map((r) => r.slice()) });
  frames[last.frame] = last.grid;
  frame = last.frame;
  $("#e-quadro").value = frame;
  setDirty(true);
  draw();
}

function redoStep() {
  const next = redo.pop();
  if (!next) return;
  undo.push({ frame: next.frame, grid: frames[next.frame].map((r) => r.slice()) });
  frames[next.frame] = next.grid;
  frame = next.frame;
  $("#e-quadro").value = frame;
  setDirty(true);
  draw();
}

function shortcuts(event) {
  if ($("#retocar").hidden || event.target.matches("input, textarea, select")) return;
  const k = event.key.toLowerCase();
  if ((event.ctrlKey || event.metaKey) && k === "z") { event.preventDefault(); event.shiftKey ? redoStep() : undoStep(); }
  else if ((event.ctrlKey || event.metaKey) && k === "y") { event.preventDefault(); redoStep(); }
  else if (!event.ctrlKey && !event.metaKey) {
    const map = { b: "lapis", e: "borracha", i: "conta", g: "balde" };
    if (map[k]) setTool(map[k]);
  }
}

// ----- cores ---------------------------------------------------------------

function addColor() {
  const hex = $("#e-nova-cor").value;
  const existing = Object.entries(colors).find(([, v]) => v.slice(0, 7) === hex && v.endsWith("ff"));
  if (existing) {
    key = existing[0];
  } else {
    const free = [...app.state.chaves].find((k) => !(k in palette));
    if (!free) return notice("sem chaves livres na spec", true);
    palette[free] = hex;
    colors[free] = `${hex}ff`;
    key = free;
    setDirty(true);
  }
  setTool("lapis");
  renderSwatches();
}

function changeColor() {
  if (!key || key === TRANSPARENT) return notice("selecione uma cor (não a transparente)", true);
  const hex = $("#e-nova-cor").value;
  palette[key] = hex;
  colors[key] = `${hex}ff`;
  setDirty(true);
  renderSwatches();
  draw();
}

// ----- gravar --------------------------------------------------------------

async function save(asVersion) {
  const spec = { palette, ...framesToSpec(frames) };
  try {
    const data = asVersion
      ? await post("/api/arte/versao", { arquivo: current.arquivo, spec })
      : await post("/api/arte", { arquivo: current.arquivo, spec });
    setDirty(false);
    await app.loadCatalog();
    notice(asVersion ? `nova versão: ${data.arquivo}` : `salvo em ${data.arquivo} (preview atualizado)`);
    if (asVersion) app.go("retocar", { arquivo: data.arquivo });
  } catch (err) {
    notice(err.message, true);
  }
}
