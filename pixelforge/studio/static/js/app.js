// Roteador por hash (#aba?param=...) e estado compartilhado.

import { get, notice } from "./api.js";
import * as gallery from "./gallery.js";
import * as viewer from "./viewer.js";
import * as editor from "./editor.js";
import * as compare from "./compare.js";
import * as scene from "./scene.js";
import * as requests from "./requests.js";

const VIEWS = { galeria: gallery, ver: viewer, retocar: editor, comparar: compare, cena: scene, pedidos: requests };

export const app = {
  state: null,      // /api/estado
  catalog: [],      // itens do acervo
  async loadCatalog() {
    const data = await get("/api/acervo");
    this.catalog = data.itens;
    return this.catalog;
  },
  entry(arquivoOrName) {
    return this.catalog.find((e) => e.arquivo === arquivoOrName || e.nome === arquivoOrName);
  },
  go(tab, params = {}) {
    const query = new URLSearchParams(params).toString();
    location.hash = `#${tab}${query ? `?${query}` : ""}`;
  },
};

function route() {
  const [tab, query = ""] = location.hash.slice(1).split("?");
  const name = VIEWS[tab] ? tab : "galeria";
  const params = Object.fromEntries(new URLSearchParams(query));
  for (const section of document.querySelectorAll("section.aba")) section.hidden = section.id !== name;
  for (const link of document.querySelectorAll("#abas a")) link.classList.toggle("ativo", link.dataset.aba === name);
  for (const [key, view] of Object.entries(VIEWS)) if (key !== name && view.hide) view.hide();
  Promise.resolve(VIEWS[name].show(params)).catch((err) => notice(err.message, true));
}

window.addEventListener("beforeunload", (event) => {
  if (editor.isDirty()) event.preventDefault();
});

async function start() {
  try {
    app.state = await get("/api/estado");
    await app.loadCatalog();
  } catch (err) {
    notice(`não consegui falar com o servidor: ${err.message}`, true);
    return;
  }
  for (const view of Object.values(VIEWS)) view.init?.(app);
  window.addEventListener("hashchange", route);
  route();
}

start();
