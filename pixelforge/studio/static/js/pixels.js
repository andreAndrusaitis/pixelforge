// Spec JSON ↔ grades de chaves e desenho em <canvas> com zoom inteiro, grade e xadrez.

export const TRANSPARENT = ".";

// Lista de quadros, cada um uma matriz [y][x] de chaves (1 caractere).
export function specFrames(spec) {
  const frames = spec.frames || [spec.pixels];
  return frames.map((rows) => rows.map((row) => Array.from(row)));
}

export function framesToSpec(frames) {
  const rows = frames.map((grid) => grid.map((row) => row.join("")));
  return rows.length === 1 ? { pixels: rows[0] } : { frames: rows };
}

// "#rrggbbaa" → [r, g, b, a]
export function parseHex(hex) {
  const h = hex.replace("#", "");
  const full = h.length === 6 ? h + "ff" : h.padEnd(8, "f");
  return [0, 2, 4, 6].map((i) => parseInt(full.slice(i, i + 2), 16));
}

export function toHex([r, g, b, a = 255]) {
  const hex = [r, g, b].map((v) => v.toString(16).padStart(2, "0")).join("");
  return `#${hex}${a === 255 ? "" : a.toString(16).padStart(2, "0")}`;
}

// colors: chave → "#rrggbbaa"
export function frameImage(grid, colors) {
  const h = grid.length;
  const w = grid[0].length;
  const data = new ImageData(w, h);
  const cache = {};
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const key = grid[y][x];
      const rgba = cache[key] || (cache[key] = key === TRANSPARENT || !colors[key] ? [0, 0, 0, 0] : parseHex(colors[key]));
      data.data.set(rgba, (y * w + x) * 4);
    }
  }
  return data;
}

// Desenha a grade de chaves ampliada; devolve a escala usada.
export function drawGrid(canvas, grid, colors, { zoom = 8, grid: showGrid = true, checker = true, background = null } = {}) {
  const h = grid.length;
  const w = grid[0].length;
  canvas.width = w * zoom;
  canvas.height = h * zoom;
  const ctx = canvas.getContext("2d");
  ctx.imageSmoothingEnabled = false;
  if (background) {
    ctx.fillStyle = background;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  } else if (checker) {
    drawChecker(ctx, canvas.width, canvas.height, Math.max(4, Math.floor(zoom / 2)));
  } else {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  }
  const off = document.createElement("canvas");
  off.width = w;
  off.height = h;
  off.getContext("2d").putImageData(frameImage(grid, colors), 0, 0);
  ctx.drawImage(off, 0, 0, w * zoom, h * zoom);
  if (showGrid && zoom >= 4) drawLines(ctx, w, h, zoom);
  return zoom;
}

export function drawChecker(ctx, width, height, cell) {
  for (let y = 0; y < height; y += cell) {
    for (let x = 0; x < width; x += cell) {
      ctx.fillStyle = ((x / cell + y / cell) & 1) ? "#cdcdcd" : "#f5f5f5";
      ctx.fillRect(x, y, cell, cell);
    }
  }
}

function drawLines(ctx, w, h, zoom) {
  for (let i = 0; i <= w; i++) {
    ctx.fillStyle = i % 8 === 0 ? "rgba(0,0,0,.45)" : "rgba(0,0,0,.15)";
    ctx.fillRect(Math.min(i * zoom, w * zoom - 1), 0, 1, h * zoom);
  }
  for (let j = 0; j <= h; j++) {
    ctx.fillStyle = j % 8 === 0 ? "rgba(0,0,0,.45)" : "rgba(0,0,0,.15)";
    ctx.fillRect(0, Math.min(j * zoom, h * zoom - 1), w * zoom, 1);
  }
}

// Zoom inteiro que cabe em `target` px no lado maior.
export function fitZoom(w, h, target = 512, max = 32) {
  return Math.max(1, Math.min(max, Math.floor(target / Math.max(w, h))));
}

// Largura útil de um palco (px) para escolher o zoom.
export function stageWidth(selector, fallback = 640) {
  const stage = document.querySelector(selector);
  return stage && stage.clientWidth > 64 ? stage.clientWidth - 40 : fallback;
}

// Pixel (x, y) da arte sob o evento do mouse.
export function cellAt(canvas, event, zoom) {
  const rect = canvas.getBoundingClientRect();
  const sx = canvas.width / rect.width;
  const sy = canvas.height / rect.height;
  return {
    x: Math.floor(((event.clientX - rect.left) * sx) / zoom),
    y: Math.floor(((event.clientY - rect.top) * sy) / zoom),
  };
}

// Mapeia cada cor para a mais próxima de outra paleta (distância RGB ponderada).
export function remapColors(colors, paletteHex) {
  const targets = paletteHex.map(parseHex);
  const out = {};
  for (const [key, hex] of Object.entries(colors)) {
    const [r, g, b, a] = parseHex(hex);
    if (a === 0) {
      out[key] = hex;
      continue;
    }
    let best = targets[0];
    let bestD = Infinity;
    for (const t of targets) {
      const rm = (r + t[0]) / 2;
      const d = (2 + rm / 256) * (r - t[0]) ** 2 + 4 * (g - t[1]) ** 2 + (2 + (255 - rm) / 256) * (b - t[2]) ** 2;
      if (d < bestD) {
        bestD = d;
        best = t;
      }
    }
    out[key] = toHex([best[0], best[1], best[2], a]);
  }
  return out;
}

// Animações do design: campo opcional `animations`; sem ele, todos os quadros com `fps`.
export function animationsOf(spec, frameCount) {
  const all = { frames: [...Array(frameCount).keys()], fps: spec.fps || 8 };
  const list = { "todos os quadros": all };
  for (const [name, anim] of Object.entries(spec.animations || {})) {
    if (anim && Array.isArray(anim.frames)) list[name] = { frames: anim.frames, fps: anim.fps || all.fps };
  }
  return list;
}
