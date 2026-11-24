// Pedidos ao Claude: marcar pontos/retângulos sobre uma arte ou quadro e escrever o pedido.
// O servidor grava pedidos/<data>-<arte>.md + a imagem anotada; o Claude lê essa pasta.

import { $, el, fileUrl, get, notice, post } from "./api.js";
import { drawChecker, drawGrid, fitZoom, specFrames, stageWidth } from "./pixels.js";

let app;
let target = null;   // {kind: "arte"|"imagem", ...}
let marks = [];
let mode = "ponto";
let drag = null;

export function init(appRef) {
  app = appRef;
  for (const b of document.querySelectorAll("[data-marca]")) {
    b.addEventListener("click", () => {
      mode = b.dataset.marca;
      for (const o of document.querySelectorAll("[data-marca]")) o.classList.toggle("ativo", o === b);
    });
  }
  $("#p-limpar").addEventListener("click", () => { marks = []; refresh(); });
  $("#p-enviar").addEventListener("click", send);
  const canvas = $("#p-canvas");
  canvas.addEventListener("pointerdown", down);
  canvas.addEventListener("pointermove", moveDrag);
  window.addEventListener("pointerup", up);
}

export async function show(params) {
  if (params.arquivo) await openArt(params.arquivo, Number(params.quadro || 0));
  else if (params.imagem) await openImage(params);
  await list();
}

async function openArt(arquivo, frame) {
  const art = await get("/api/arte", { arquivo });
  if (!art.spec) throw new Error(art.aviso || "arte sem spec");
  const frames = specFrames(art.spec);
  const grid = frames[Math.min(frame, frames.length - 1)];
  const w = grid[0].length, h = grid.length;
  target = { kind: "arte", arquivo, frame, nome: art.nome, grid, cores: art.cores, w, h, zoom: fitZoom(w, h, Math.min(560, stageWidth("#pedidos .palco"))) };
  marks = [];
  $("#p-estado").textContent = "";
  $("#p-titulo").textContent = `Pedido · ${art.nome}${frames.length > 1 ? ` (quadro ${frame})` : ""}`;
  refresh();
}

async function openImage(params) {
  const image = new Image();
  await new Promise((resolve, reject) => {
    image.onload = resolve;
    image.onerror = () => reject(new Error(`não consegui abrir ${params.imagem}`));
    image.src = fileUrl(params.imagem);
  });
  const zoom = Math.min(1, stageWidth("#pedidos .palco", 900) / image.width);
  target = { kind: "imagem", imagem: params.imagem, nome: params.nome || "quadro", cena: params.cena,
             t: params.t, escala: Number(params.escala || 1), image, w: image.width, h: image.height, zoom };
  marks = [];
  $("#p-estado").textContent = "";
  $("#p-titulo").textContent = `Pedido · ${target.nome}`;
  refresh();
}

// Coordenada da marca: pixel da arte, ou pixel da imagem do quadro.
function pointAt(event) {
  const canvas = $("#p-canvas");
  const rect = canvas.getBoundingClientRect();
  const px = ((event.clientX - rect.left) * canvas.width) / rect.width;
  const py = ((event.clientY - rect.top) * canvas.height) / rect.height;
  return {
    x: Math.max(0, Math.min(target.w - 1, Math.floor(px / target.zoom))),
    y: Math.max(0, Math.min(target.h - 1, Math.floor(py / target.zoom))),
  };
}

function down(event) {
  if (!target) return;
  const p = pointAt(event);
  if (mode === "ponto") {
    marks.push({ tipo: "ponto", x: p.x, y: p.y, nota: "" });
    refresh();
    return;
  }
  drag = { start: p, end: p };
  $("#p-canvas").setPointerCapture(event.pointerId);
}

function moveDrag(event) {
  if (!drag) return;
  drag.end = pointAt(event);
  drawStage();
}

function up() {
  if (!drag) return;
  const { start, end } = drag;
  drag = null;
  marks.push({ tipo: "retangulo", x: Math.min(start.x, end.x), y: Math.min(start.y, end.y),
               w: Math.abs(end.x - start.x) + 1, h: Math.abs(end.y - start.y) + 1, nota: "" });
  refresh();
}

function refresh() {
  $("#p-vazio").hidden = !!target;
  $("#p-canvas").hidden = !target;
  drawStage();
  const listBox = $("#p-marcas");
  listBox.replaceChildren(...marks.map((m, i) => {
    const note = el("input", { type: "text", placeholder: "nota desta marca (opcional)", value: m.nota });
    note.addEventListener("input", () => (m.nota = note.value));
    const desc = m.tipo === "ponto" ? `ponto (${m.x}, ${m.y})` : `retângulo ${m.x},${m.y} ${m.w}×${m.h}`;
    return el("li", {}, desc, " ", el("button", { onclick: () => { marks.splice(i, 1); refresh(); } }, "×"), note);
  }));
}

function drawStage() {
  if (!target) return;
  const canvas = $("#p-canvas");
  const z = target.zoom;
  if (target.kind === "arte") {
    drawGrid(canvas, target.grid, target.cores, { zoom: z, grid: z >= 6 });
  } else {
    canvas.width = Math.round(target.w * z);
    canvas.height = Math.round(target.h * z);
    const ctx = canvas.getContext("2d");
    ctx.imageSmoothingEnabled = false;
    drawChecker(ctx, canvas.width, canvas.height, 8);
    ctx.drawImage(target.image, 0, 0, canvas.width, canvas.height);
  }
  const ctx = canvas.getContext("2d");
  ctx.lineWidth = Math.max(2, Math.round(z / 4));
  ctx.strokeStyle = "#ff00aa";
  ctx.fillStyle = "#ff00aa";
  ctx.font = "bold 13px system-ui";
  const all = drag ? [...marks, { tipo: "retangulo", x: Math.min(drag.start.x, drag.end.x), y: Math.min(drag.start.y, drag.end.y),
    w: Math.abs(drag.end.x - drag.start.x) + 1, h: Math.abs(drag.end.y - drag.start.y) + 1, rascunho: true }] : marks;
  all.forEach((m, i) => {
    const x = m.x * z, y = m.y * z;
    if (m.tipo === "ponto") {
      const r = Math.max(z, 6);
      ctx.beginPath();
      ctx.arc(x + z / 2, y + z / 2, r, 0, Math.PI * 2);
      ctx.stroke();
    } else {
      ctx.strokeRect(x, y, m.w * z, m.h * z);
    }
    if (!m.rascunho) {
      ctx.fillRect(x, Math.max(0, y - 16), 16, 15);
      ctx.fillStyle = "#fff";
      ctx.fillText(String(i + 1), x + 4, Math.max(12, y - 4));
      ctx.fillStyle = "#ff00aa";
    }
  });
}

async function send() {
  if (!target) return notice("abra uma arte ou um quadro primeiro", true);
  const texto = $("#p-texto").value.trim();
  if (!texto) return notice("escreva o que mudar", true);
  const body = { texto, marcas: marks };
  if (target.kind === "arte") Object.assign(body, { arquivo: target.arquivo, quadro: target.frame });
  else Object.assign(body, { imagem: target.imagem, nome: target.nome, cena: target.cena, t: target.t, escala: target.escala });
  try {
    const data = await post("/api/pedido", body);
    $("#p-estado").textContent = `gravado: ${data.pedido}`;
    notice(`pedido gravado em ${data.pedido}`);
    $("#p-texto").value = "";
    marks = [];
    refresh();
    await list();
  } catch (err) {
    notice(err.message, true);
  }
}

async function list() {
  const data = await get("/api/pedidos");
  const box = $("#p-lista");
  if (!data.pedidos.length) {
    box.replaceChildren(el("p", { class: "sutil" }, "Nenhum pedido ainda. O Claude lê pedidos/*.md e marca como feito."));
    return;
  }
  box.replaceChildren(...data.pedidos.map((p) => el("article", { class: "pedido" },
    el("div", { class: "linha" }, el("strong", {}, p.arte || p.pedido), el("span", { class: `estado ${p.estado}` }, p.estado)),
    el("div", { class: "sutil" }, `${p.criado || ""} · ${p.pedido}`),
    p.imagem ? el("img", { src: fileUrl(p.imagem), alt: "imagem anotada", loading: "lazy" }) : null,
    el("pre", {}, p.texto),
    el("div", { class: "linha" },
      ...["aberto", "feito", "descartado"].filter((s) => s !== p.estado).map((s) =>
        el("button", { onclick: () => setState(p.pedido, s) }, `marcar ${s}`))))));
}

async function setState(pedido, estado) {
  try {
    await post("/api/pedido/estado", { pedido, estado });
    await list();
  } catch (err) {
    notice(err.message, true);
  }
}
