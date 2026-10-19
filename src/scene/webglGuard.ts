/** Recover from WebGL context loss instead of leaving a dead canvas. */

export function attachWebglGuard(
  canvas: HTMLCanvasElement,
  onLost: () => void,
  onRestored: () => void,
): () => void {
  const lost = (event: Event) => {
    event.preventDefault();
    console.warn("Anatomy-3d: contexte WebGL perdu — attente de restauration.");
    onLost();
  };
  const restored = () => {
    console.warn("Anatomy-3d: contexte WebGL restauré.");
    onRestored();
  };
  canvas.addEventListener("webglcontextlost", lost, false);
  canvas.addEventListener("webglcontextrestored", restored, false);
  return () => {
    canvas.removeEventListener("webglcontextlost", lost, false);
    canvas.removeEventListener("webglcontextrestored", restored, false);
  };
}
