import { isIos } from "../lib/pwaClient";

/** Low-end phone, Chromebook, and Android WebView heuristics — prefer not crashing over polish. */
/** Framebuffer cap. Above 1.5, a full-body Z-Anatomy view blows integrated-GPU memory. */
export const MAX_PIXEL_RATIO = 1.5;

export type DeviceProfile = {
  lowEnd: boolean;
  dpr: [number, number];
  antialias: boolean;
  shadows: boolean;
  shadowMap: number;
  contactShadows: boolean;
  physicalMaterials: boolean;
};

let cached: DeviceProfile | null = null;

function chromeOs() {
  return /CrOS|Chromebook/i.test(navigator.userAgent);
}

function androidWebView() {
  const ua = navigator.userAgent;
  return /Android/i.test(ua) && (/; wv\)/i.test(ua) || /Version\/\d+\.\d+/i.test(ua));
}

export function getDeviceProfile(): DeviceProfile {
  if (cached) return cached;
  if (typeof navigator === "undefined") {
    cached = {
      lowEnd: false,
      dpr: [1, 2],
      antialias: true,
      shadows: true,
      shadowMap: 1024,
      contactShadows: true,
      physicalMaterials: true,
    };
    return cached;
  }
  const cores = navigator.hardwareConcurrency || 4;
  const memory = Number((navigator as Navigator & { deviceMemory?: number }).deviceMemory ?? 4);
  const lowEnd = isIos() || chromeOs() || androidWebView() || cores <= 4 || memory <= 4;
  cached = {
    lowEnd,
    dpr: lowEnd ? [1, 1] : [1, MAX_PIXEL_RATIO],
    antialias: !lowEnd,
    shadows: !lowEnd,
    shadowMap: lowEnd ? 512 : 1024,
    contactShadows: !lowEnd,
    physicalMaterials: !lowEnd,
  };
  return cached;
}
