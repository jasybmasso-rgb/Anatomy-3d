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
  // Capture so preventDefault runs before other listeners. Safari will not
  // restore the context unless the lost event is cancelled.
  canvas.addEventListener("webglcontextlost", lost, true);
  canvas.addEventListener("webglcontextrestored", restored, true);
  return () => {
    canvas.removeEventListener("webglcontextlost", lost, true);
    canvas.removeEventListener("webglcontextrestored", restored, true);
  };
}
