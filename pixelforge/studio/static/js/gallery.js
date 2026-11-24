// Galeria do acervo: filtros por texto, tipo, projeto e tags; versões lado a lado.

import { $, el, fileUrl, notice, post } from "./api.js";

let app;
const filters = { text: "", tipo: "", projeto: "", tags: new Set() };
const TYPES = ["personagem", "cenario", "objeto", "cena", "som"];
const TYPE_LABEL = { personagem: "personagem", cenario: "cenário", objeto: "objeto", cena: "cena", som: "som" };

export function init(appRef) {
  app = appRef;
  const tipo = $("#g-tipo");
  for (const t of TYPES) tipo.append(el("option", { value: t }, TYPE_LABEL[t]));
  $("#g-busca").addEventListener("input", (e) => { filters.text = e.target.value; render(); });
  tipo.addEventListener("change", (e) => { filters.tipo = e.target.value; render(); });
  $("#g-projeto").addEventListener("change", (e) => { filters.projeto = e.target.value; render(); });
  $("#g-indexar").addEventListener("click", reindex);
}

export async function show() {
  await app.loadCatalog();
  fillProjects();
  render();
}

async function reindex() {
  const button = $("#g-indexar");
  button.disabled = true;
  button.textContent = "indexando…";
  try {
    const data = await post("/api/acervo/indexar");
    app.catalog = data.itens;
    notice(`acervo: ${data.itens.length} item(ns)` + (data.avisos.length ? ` · ${data.avisos.length} aviso(s)` : ""));
    for (const warning of data.avisos) console.warn(warning);
    fillProjects();
    render();
  } catch (err) {
    notice(err.message, true);
  } finally {
    button.disabled = false;
    button.textContent = "Reindexar";
  }
}

function fillProjects() {
  const select = $("#g-projeto");
  const projects = [...new Set(app.catalog.map((e) => e.projeto).filter(Boolean))].sort();
  select.replaceChildren(el("option", { value: "" }, "todos os projetos"),
    ...projects.map((p) => el("option", { value: p, selected: p === filters.projeto }, p)));
}

function matches(entry) {
  if (filters.tipo && entry.tipo !== filters.tipo) return false;
  if (filters.projeto && entry.projeto !== filters.projeto) return false;
  for (const tag of filters.tags) if (!entry.tags.includes(tag)) return false;
  if (filters.text) {
    const hay = [entry.nome, entry.tipo, entry.projeto, entry.arquivo, ...entry.tags].join(" ").toLowerCase();
    return filters.text.toLowerCase().split(/\s+/).every((w) => hay.includes(w));
  }
  return true;
}

function renderTags() {
  const all = [...new Set(app.catalog.flatMap((e) => e.tags))].sort();
  $("#g-tags").replaceChildren(...all.map((tag) => el("button", {
    class: `chip${filters.tags.has(tag) ? " ativo" : ""}`,
    onclick: () => { filters.tags.has(tag) ? filters.tags.delete(tag) : filters.tags.add(tag); render(); },
  }, `#${tag}`)));
}

function render() {
  renderTags();
  // família = todas as versões da mesma base; aparece se qualquer versão casar com o filtro
  const families = new Map();
  for (const entry of app.catalog) {
    if (!families.has(entry.base)) families.set(entry.base, []);
    families.get(entry.base).push(entry);
  }
  const list = $("#g-lista");
  list.replaceChildren();
  let shown = 0;
  for (const [base, family] of [...families].sort((a, b) => a[0].localeCompare(b[0]))) {
    if (!family.some(matches)) continue;
    family.sort((a, b) => a.versao - b.versao);
    shown++;
    const row = el("div", { class: "versoes-fila" });
    family.forEach((entry, i) => {
      if (i > 0) row.append(el("span", { class: "seta", title: `${entry.nome} herda de ${entry.herda || "—"}` }, "→"));
      row.append(card(entry, family[i - 1]));
    });
    const title = family.length > 1 ? `${base} · ${family.length} versões` : family[0].nome;
    list.append(el("article", { class: `familia${family.length > 1 ? " varias" : ""}` }, el("h3", {}, title), row));
  }
  if (!shown) {
    list.append(el("p", { class: "vazio" },
      app.catalog.length ? "Nada casa com o filtro." : "Acervo vazio: coloque artes em art/ e clique em Reindexar."));
  }
}

function card(entry, previous) {
  const thumb = entry.miniatura
    ? el("img", { src: fileUrl(entry.miniatura, false), alt: entry.nome, loading: "lazy" })
    : el("span", { class: "sutil" }, entry.tipo === "cena" ? "🎬 cena" : "sem miniatura");
  const size = entry.tamanho ? `${entry.tamanho[0]}×${entry.tamanho[1]}` : "";
  const frames = entry.quadros > 1 ? ` · ${entry.quadros} quadros` : "";
  const open = () => entry.tipo === "cena" ? app.go("cena", { nome: entry.nome }) : app.go("ver", { arquivo: entry.arquivo });
  return el("div", { class: "item" },
    el("div", { class: "mini xadrez", onclick: open, title: entry.arquivo }, thumb),
    el("div", { class: "nome" }, entry.nome),
    el("div", { class: "meta" }, `${TYPE_LABEL[entry.tipo] || entry.tipo} · v${entry.versao}${size ? " · " + size : ""}${frames}`),
    entry.projeto ? el("div", { class: "meta" }, `projeto: ${entry.projeto}`) : null,
    entry.tags.length ? el("div", { class: "tags" }, entry.tags.map((t) => `#${t}`).join(" ")) : null,
    el("div", { class: "acoes" },
      entry.tipo !== "cena" && entry.tipo !== "som"
        ? el("button", { onclick: () => app.go("retocar", { arquivo: entry.arquivo }) }, "retocar") : null,
      previous ? el("button", { onclick: () => app.go("comparar", { a: previous.arquivo, b: entry.arquivo }) }, "antes/depois") : null,
      el("button", { onclick: () => editTags(entry), title: "editar tags" }, "#")));
}

async function editTags(entry) {
  const value = prompt(`Tags de ${entry.nome} (separadas por espaço):`, entry.tags.join(" "));
  if (value === null) return;
  const wanted = value.split(/[\s,]+/).map((t) => t.replace(/^#/, "").toLowerCase()).filter(Boolean);
  try {
    await post("/api/acervo/tag", {
      nome: entry.nome,
      adicionar: wanted,
      remover: entry.tags.filter((t) => !wanted.includes(t)),
    });
    await app.loadCatalog();
    render();
  } catch (err) {
    notice(err.message, true);
  }
}
