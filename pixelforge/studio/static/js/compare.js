// Comparador antes/depois (versões do acervo) e com a foto de referência (painel do compare).

import { $, el, fileUrl, get, notice } from "./api.js";
import { drawGrid, specFrames } from "./pixels.js";

let app;
let blink = null;
const arts = { a: null, b: null };

export function init(appRef) {
  app = appRef;
  $("#c-a").addEventListener("change", () => load("a"));
  $("#c-b").addEventListener("change", () => load("b"));
  $("#c-modo").addEventListener("change", render);
  $("#c-zoom").addEventListener("input", render);
  $("#c-foto").addEventListener("click", photo);
}

export async function show(params) {
  const options = app.catalog.filter((e) => e.tipo !== "cena" && e.tipo !== "som");
  for (const side of ["a", "b"]) {
    const select = $(`#c-${side}`);
    const keep = params[side] || select.value;
    select.replaceChildren(el("option", { value: "" }, "—"),
      ...options.map((e) => el("option", { value: e.arquivo }, `${e.nome} (v${e.versao})`)));
    select.value = keep || "";
  }
  if (!params.a && params.b) {
    const entry = app.entry(params.b);
    const parent = entry?.herda && app.entry(entry.herda);
    if (parent) $("#c-a").value = parent.arquivo;
  }
  $("#c-foto-res").replaceChildren();
  await Promise.all([load("a", false), load("b", false)]);
  render();
}

export function hide() {
  clearInterval(blink);
}

async function load(side, redraw = true) {
  const arquivo = $(`#c-${side}`).value;
  arts[side] = null;
  if (arquivo) {
    try {
      arts[side] = await get("/api/arte", { arquivo });
    } catch (err) {
      notice(err.message, true);
    }
  }
  if (redraw) render();
}

function canvasFor(art, zoom) {
  const canvas = el("canvas");
  if (art?.spec) drawGrid(canvas, specFrames(art.spec)[0], art.cores, { zoom, grid: false });
  return canvas;
}

function render() {
  clearInterval(blink);
  const stage = $("#c-palco");
  stage.replaceChildren();
  const zoom = Number($("#c-zoom").value);
  const { a, b } = arts;
  if (!a && !b) {
    stage.append(el("p", { class: "vazio" }, "Escolha as versões “antes” e “depois” (a galeria tem atalho em cada família)."));
    return;
  }
  const mode = $("#c-modo").value;
  if (mode === "lado" || !a || !b) {
    for (const [label, art] of [["antes", a], ["depois", b]]) {
      if (!art) continue;
      stage.append(el("figure", {}, el("div", { class: "xadrez" }, canvasFor(art, zoom)),
        el("figcaption", {}, `${label}: ${art.nome}`)));
    }
    return;
  }
  const before = canvasFor(a, zoom);
  const after = canvasFor(b, zoom);
  after.classList.add("depois");
  const box = el("div", { class: "cortina xadrez" }, before, after);
  if (mode === "cortina") {
    const slider = el("input", { type: "range", min: 0, max: 100, value: 50 });
    const clip = () => (after.style.clipPath = `inset(0 0 0 ${slider.value}%)`);
    slider.addEventListener("input", clip);
    clip();
    stage.append(el("figure", {}, box, slider, el("figcaption", {}, `← ${a.nome} | ${b.nome} →`)));
  } else {
    const caption = el("figcaption", {}, b.nome);
    let showingAfter = true;
    blink = setInterval(() => {
      showingAfter = !showingAfter;
      after.style.visibility = showingAfter ? "visible" : "hidden";
      caption.textContent = showingAfter ? `depois: ${b.nome}` : `antes: ${a.nome}`;
    }, 700);
    stage.append(el("figure", {}, box, caption));
  }
}

async function photo() {
  const arquivo = $("#c-b").value || $("#c-a").value;
  const box = $("#c-foto-res");
  if (!arquivo) return notice("escolha uma arte", true);
  box.replaceChildren(el("p", { class: "sutil" }, "comparando com a foto…"));
  try {
    const data = await get("/api/comparar", { arquivo });
    box.replaceChildren(el("p", {}, `Foto: ${data.foto} · ${data.nota}`), el("img", { src: fileUrl(data.painel), alt: "painel compare" }));
  } catch (err) {
    box.replaceChildren(el("p", { class: "alerta" }, err.message));
  }
}
