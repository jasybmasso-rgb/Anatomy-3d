/** Public asset URL, including the Vite base used by GitHub Pages. */
export function publicUrl(path: string): string {
  const base = import.meta.env.BASE_URL || "/";
  const relative = path.replace(/^\/+/, "");
  return `${base}${relative}`;
}
