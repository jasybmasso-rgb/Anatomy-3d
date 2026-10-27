import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "ca.anatomy3d.app",
  appName: "Anatomy-3d",
  webDir: "dist",
  android: {
    allowMixedContent: false,
    webContentsDebuggingEnabled: true,
  },
  server: {
    androidScheme: "https",
  },
};

export default config;
