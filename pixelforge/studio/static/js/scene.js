// Linha do tempo de cena: vídeo, storyboard, planos como blocos e scrub por quadro.
// O quadro exato vem do motor de cena (pixelforge/scene/) quando ele existe.

import { $, el, fileUrl, get, notice } from "./api.js";

let app;
let info = null;
let media = null;       // <video> (scrub de verdade) ou <img> (GIF/WebP)
let playTimer = null;
let exactTimer = null;
let lastFrame = null;   // resposta de /api/quadro

export function init(appRef) {
  app = appRef;
  $("#s-lista").addEventListener("change", (e) => app.go("cena", { nome: e.target.value }));
  $("#s-scrub").addEventListener("input", () => seek(Number($("#s-scrub").value), true));
  $("#s-tocar").addEventListener("click", togglePlay);
  $("#s-exato").addEventListener("click", () => exact());
  $("#s-pedido").addEventListener("click", request);
}

export async function show(params) {
  const data = await get("/api/cenas");
  $("#s-motor").textContent = data.motor
    ? "motor de cena: disponível (quadro exato ligado)"
    : "motor de cena ainda não instalado: scrub usa o vídeo";
  const select = $("#s-lista");
  select.replaceChildren(...data.cenas.map((c) => el("option", { value: c.nome }, c.nome)));
  const empty = $("#s-vazio");
  if (!data.cenas.length) {
    empty.hidden = false;
    empty.textContent = "Nenhuma cena ainda. Crie um roteiro em art/cenas/<nome>.json e rode " +
      "“python -m pixelforge cena art/cenas/<nome>.json”; o vídeo e o storyboard em out/<nome>/ aparecem aqui.";
    $("#s-conteudo").hidden = true;
    return;
  }
  empty.hidden = true;
  const name = params.nome && data.cenas.some((c) => c.nome === params.nome) ? params.nome : data.cenas[0].nome;
  select.value = name;
  info = await get("/api/cena", { nome: name });
  info.motor = data.motor;
  setup();
}

export function hide() {
  stopPlay();
  media?.pause?.();
}

function setup() {
  $("#s-conteudo").hidden = false;
  lastFrame = null;
  const box = $("#s-video");
  box.replaceChildren();
  const video = info.videos.find((v) => /\.(mp4|webm)$/.test(v));
  const anim = info.videos.find((v) => /\.(gif|webp)$/.test(v));
  if (video) {
    media = el("video", { src: fileUrl(video), controls: true, preload: "auto", muted: true });
    media.addEventListener("loadedmetadata", () => {
      if (info.quadros > 0 || !isFinite(media.duration)) return;
      // sem roteiro: a duração do vídeo define o scrub
      info.duracao = media.duration;
      info.quadros = Math.round(media.duration * info.fps);
      $("#s-scrub").max = Math.max(0, info.quadros - 1);
      seek(0, false);
    });
    media.addEventListener("timeupdate", () => {
      if (!media.paused) syncFromTime(media.currentTime);
    });
    box.append(media);
  } else if (anim) {
    media = el("img", { src: fileUrl(anim), alt: info.nome });
    box.append(media, el("p", { class: "sutil" }, "GIF/WebP: o scrub mostra o quadro exato pelo motor (sem MP4 não dá para pausar o vídeo)."));
  } else {
    media = null;
    box.append(el("p", { class: "vazio" }, "Sem vídeo ainda (rode o comando cena)."));
  }
  const board = $("#s-storyboard");
  if (info.storyboard) board.src = fileUrl(info.storyboard);
  else board.removeAttribute("src");
  board.hidden = !info.storyboard;

  const frames = Math.max(1, info.quadros || 1);
  const scrub = $("#s-scrub");
  scrub.max = frames - 1;
  scrub.value = 0;
  renderShots();
  $("#s-exato").disabled = !info.motor || !info.roteiro;
  $("#s-quadro-img").removeAttribute("src");
  $("#s-quadro-info").textContent = info.erro ? `motor: ${info.erro}` :
    (info.motor ? "Arraste o cursor: o quadro exato aparece aqui." : "");
  seek(0, false);
}

function renderShots() {
  const box = $("#s-planos");
  box.replaceChildren();
  const total = info.duracao || 1;
  for (const shot of info.planos) {
    const block = el("div", {
      class: "plano", title: `plano ${shot.plano}: ${fmt(shot.inicio)} – ${fmt(shot.inicio + shot.dur)}`,
      onclick: () => seek(Math.round(shot.inicio * info.fps), true),
    }, `${shot.plano} · ${fmt(shot.dur)}`);
    block.style.flex = `${Math.max(shot.dur, 0.05) / total} 0 0`;
    block.dataset.plano = shot.plano;
    box.append(block);
  }
  if (!info.planos.length) box.append(el("div", { class: "plano", style: "flex:1" }, "sem roteiro: planos desconhecidos"));
}

function fmt(seconds) {
  return `${seconds.toFixed(2).replace(".", ",")} s`;
}

function seek(index, fromUser) {
  const t = index / info.fps;
  $("#s-scrub").value = index;
  $("#s-tempo").textContent = `${fmt(t)} · quadro ${index}/${Math.max(0, info.quadros - 1)}`;
  for (const block of document.querySelectorAll("#s-planos .plano[data-plano]")) {
    const shot = info.planos[Number(block.dataset.plano) - 1];
    block.classList.toggle("atual", t >= shot.inicio && t < shot.inicio + shot.dur + 1e-9);
  }
  if (media?.tagName === "VIDEO" && fromUser) {
    media.pause();
    media.currentTime = Math.min(t + 0.5 / info.fps, media.duration || t);
  }
  if (fromUser && info.motor && info.roteiro) {
    clearTimeout(exactTimer);
    exactTimer = setTimeout(() => exact(), 150);
  }
}

function syncFromTime(t) {
  const index = Math.min(info.quadros - 1, Math.floor(t * info.fps));
  seek(index, false);
}

function togglePlay() {
  if (media?.tagName === "VIDEO") {
    if (media.paused) media.play();
    else media.pause();
    return;
  }
  if (playTimer) return stopPlay();
  $("#s-tocar").textContent = "⏸ pausar";
  playTimer = setInterval(() => {
    const next = (Number($("#s-scrub").value) + 1) % Math.max(1, info.quadros);
    seek(next, false);
  }, 1000 / info.fps);
}

function stopPlay() {
  clearInterval(playTimer);
  playTimer = null;
  $("#s-tocar").textContent = "▶ tocar";
}

async function exact() {
  if (!info.motor || !info.roteiro) return;
  // meio do quadro: evita cair no anterior por arredondamento
  const t = Math.min((Number($("#s-scrub").value) + 0.5) / info.fps, info.duracao);
  try {
    lastFrame = await get("/api/quadro", { roteiro: info.roteiro, t: t.toFixed(4), escala: 3 });
    $("#s-quadro-img").src = fileUrl(lastFrame.imagem);
    $("#s-quadro-info").textContent = `quadro ${lastFrame.indice} · plano ${lastFrame.plano} · ` +
      `t=${fmt(lastFrame.t)} · câmera ${lastFrame.camera.join(",")}`;
  } catch (err) {
    $("#s-quadro-info").textContent = err.message;
  }
}

async function request() {
  if (!info.motor || !info.roteiro) {
    return notice("pedido sobre quadro precisa do motor de cena; marque o storyboard ou a arte", true);
  }
  if (!lastFrame) await exact();
  if (!lastFrame) return;
  app.go("pedidos", { imagem: lastFrame.imagem, cena: info.nome, t: lastFrame.t, escala: lastFrame.escala,
                      nome: `${info.nome}-q${lastFrame.indice}` });
}
