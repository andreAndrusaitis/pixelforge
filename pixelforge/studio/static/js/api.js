// Chamadas à API local do estúdio e utilidades de interface.

export async function get(path, params = {}) {
  const query = new URLSearchParams(params).toString();
  const res = await fetch(path + (query ? `?${query}` : ""));
  return unwrap(res);
}

export async function post(path, body = {}) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return unwrap(res);
}

async function unwrap(res) {
  const data = await res.json().catch(() => ({ erro: `resposta inválida (${res.status})` }));
  if (!res.ok) {
    const error = new Error(data.erro || `erro ${res.status}`);
    error.status = res.status;
    throw error;
  }
  return data;
}

// URL de um arquivo do repositório (art/, out/, refs/, pedidos/); `fresh` evita cache.
export function fileUrl(rel, fresh = true) {
  const path = rel.split("/").map(encodeURIComponent).join("/");
  return `/arquivo/${path}${fresh ? `?v=${Date.now()}` : ""}`;
}

let noticeTimer = null;
export function notice(message, isError = false) {
  const box = document.getElementById("aviso");
  box.textContent = message;
  box.classList.toggle("erro", isError);
  box.hidden = false;
  clearTimeout(noticeTimer);
  noticeTimer = setTimeout(() => (box.hidden = true), isError ? 8000 : 3500);
}

export function $(selector, root = document) {
  return root.querySelector(selector);
}

export function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (key === "class") node.className = value;
    else if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
    else if (value !== undefined && value !== null && value !== false) node.setAttribute(key, value);
  }
  for (const child of children.flat()) {
    if (child !== null && child !== undefined) node.append(child.nodeType ? child : String(child));
  }
  return node;
}
