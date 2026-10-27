/** iPhone, iPod, and iPad (including iPadOS desktop user agents). */
export function isIos(): boolean {
  if (typeof navigator === "undefined") return false;
  const ua = navigator.userAgent || "";
  if (/iPad|iPhone|iPod/i.test(ua)) return true;
  return navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1;
}

export function isIphone(): boolean {
  if (typeof navigator === "undefined") return false;
  return /iPhone|iPod/i.test(navigator.userAgent || "");
}

export function isStandaloneDisplay(): boolean {
  if (typeof window === "undefined") return false;
  const nav = navigator as Navigator & { standalone?: boolean };
  if (nav.standalone) return true;
  return window.matchMedia("(display-mode: standalone)").matches;
}

export function registerServiceWorker(): void {
  if (!import.meta.env.PROD) return;
  if (typeof navigator === "undefined" || !("serviceWorker" in navigator)) return;
  window.addEventListener("load", () => {
    const url = `${import.meta.env.BASE_URL}sw.js`;
    navigator.serviceWorker.register(url).catch(() => {
      /* Private mode and some embedded browsers refuse the worker. The app still loads online. */
    });
  });
}
