import { createHash } from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import type { Plugin } from "vite";

const BANNED = ["zanatomy.html"];

function walk(dir: string, out: string[] = []): string[] {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full, out);
    else out.push(full);
  }
  return out;
}

function shellUrl(base: string, dist: string, file: string): string | null {
  const rel = path.relative(dist, file).split(path.sep).join("/");
  if (rel === "sw.js" || rel.endsWith(".glb") || rel.endsWith(".map")) return null;
  if (BANNED.includes(rel) || rel.endsWith("zanatomy-nerves.meta.json")) return null;
  if (rel.includes("full-original") || rel.includes("zanatomy-full-original")) return null;
  return `${base}${rel}`;
}

/** Precache the app shell. GLBs stay out of the precache and are stored on first fetch. */
export function anatomyPwa(): Plugin {
  return {
    name: "anatomy-pwa",
    apply: "build",
    closeBundle() {
      const dist = path.resolve("dist");
      const base = (process.env.VITE_BASE || "/").replace(/\/?$/, "/");
      for (const name of BANNED) {
        const banned = path.join(dist, name);
        if (fs.existsSync(banned)) fs.rmSync(banned);
      }
      const strayMeta = path.join(dist, "models", "zanatomy-nerves.meta.json");
      if (fs.existsSync(strayMeta)) fs.rmSync(strayMeta);
      const files = walk(dist)
        .map((file) => shellUrl(base, dist, file))
        .filter((url): url is string => Boolean(url))
        .sort();
      const indexHtml = path.join(dist, "index.html");
      const html = fs.readFileSync(indexHtml, "utf8");
      if (html.includes("zanatomy.html")) {
        throw new Error("The public build still links zanatomy.html.");
      }
      const hash = createHash("sha256").update(files.join("\n")).digest("hex").slice(0, 12);
      const indexUrl = `${base}index.html`;
      const source = `/* Anatomy-3d app shell. GLBs are cached on first successful fetch. */
const SHELL = ${JSON.stringify(`anatomy3d-shell-${hash}`)};
const GLB = "anatomy3d-glb-v1";
const PRECACHE = ${JSON.stringify(files)};
const INDEX = ${JSON.stringify(indexUrl)};

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(SHELL).then((cache) => cache.addAll(PRECACHE)).then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(keys.filter((key) => key !== SHELL && key !== GLB).map((key) => caches.delete(key))),
      )
      .then(() => self.clients.claim()),
  );
});

function sameOrigin(url) {
  return url.origin === self.location.origin;
}

async function cacheGlb(request) {
  const cache = await caches.open(GLB);
  const cached = await cache.match(request);
  const refresh = fetch(request)
    .then((response) => {
      if (response && response.ok) cache.put(request, response.clone()).catch(() => {});
      return response;
    })
    .catch(() => cached);
  return cached || refresh;
}

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  if (!sameOrigin(url)) return;
  if (url.pathname.endsWith(".glb")) {
    event.respondWith(cacheGlb(request));
    return;
  }
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const copy = response.clone();
          caches.open(SHELL).then((cache) => cache.put(request, copy)).catch(() => {});
          return response;
        })
        .catch(async () => (await caches.match(request)) || (await caches.match(INDEX)) || Response.error()),
    );
    return;
  }
  event.respondWith(caches.match(request).then((cached) => cached || fetch(request)));
});
`;
      fs.writeFileSync(path.join(dist, "sw.js"), source);
    },
  };
}
