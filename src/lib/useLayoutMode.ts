import { useCallback, useEffect, useRef, useState } from "react";

export type LayoutMode = "normal" | "viewport" | "fiche";

/** Narrow window, touch tablet, or Capacitor WebView — stacked / compact chrome. */
const COMPACT_QUERY = "(max-width: 1024px), (pointer: coarse)";

function isCapacitorNative(): boolean {
  if (typeof window === "undefined") return false;
  const cap = (window as Window & { Capacitor?: { isNativePlatform?: () => boolean } }).Capacitor;
  return Boolean(cap?.isNativePlatform?.());
}

export function useCompactLayout(): boolean {
  const [compact, setCompact] = useState(() => {
    if (typeof window === "undefined") return false;
    return isCapacitorNative() || window.matchMedia(COMPACT_QUERY).matches;
  });

  useEffect(() => {
    const mq = window.matchMedia(COMPACT_QUERY);
    const update = () => setCompact(isCapacitorNative() || mq.matches);
    update();
    mq.addEventListener("change", update);
    return () => mq.removeEventListener("change", update);
  }, []);

  return compact;
}

function pushFs(next: Exclude<LayoutMode, "normal">) {
  history.pushState({ anatomyFs: next }, "");
}

function replaceFs(next: Exclude<LayoutMode, "normal">) {
  if (history.state?.anatomyFs) history.replaceState({ anatomyFs: next }, "");
  else pushFs(next);
}

/**
 * App-chrome fullscreen (not the browser Fullscreen API): expand the 3D viewport
 * or the anatomical fiche over the window. Escape / history.back() / Réduire exit.
 */
export function useLayoutMode() {
  const [mode, setMode] = useState<LayoutMode>("normal");
  const modeRef = useRef(mode);
  const exitingRef = useRef(false);
  modeRef.current = mode;

  const enter = useCallback((next: Exclude<LayoutMode, "normal">) => {
    const prev = modeRef.current;
    if (prev === next || exitingRef.current) return;
    if (prev === "normal") pushFs(next);
    else replaceFs(next);
    setMode(next);
  }, []);

  const exit = useCallback(() => {
    if (modeRef.current === "normal" || exitingRef.current) return;
    if (history.state?.anatomyFs) {
      exitingRef.current = true;
      history.back();
      return;
    }
    setMode("normal");
  }, []);

  const toggle = useCallback(
    (next: Exclude<LayoutMode, "normal">) => {
      if (modeRef.current === next) exit();
      else enter(next);
    },
    [enter, exit],
  );

  useEffect(() => {
    const onPop = () => {
      exitingRef.current = false;
      setMode("normal");
    };
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      if (modeRef.current === "normal") return;
      event.preventDefault();
      if (exitingRef.current) return;
      if (history.state?.anatomyFs) {
        exitingRef.current = true;
        history.back();
      } else {
        setMode("normal");
      }
    };
    window.addEventListener("popstate", onPop);
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("popstate", onPop);
      window.removeEventListener("keydown", onKey);
    };
  }, []);

  return { mode, enter, exit, toggle };
}
