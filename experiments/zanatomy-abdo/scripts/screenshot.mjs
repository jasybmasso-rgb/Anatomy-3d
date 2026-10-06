/**
 * Headless Chrome screenshots of the standalone viewer.
 * Usage: node scripts/screenshot.mjs
 * Requires the viewer on http://127.0.0.1:5179
 */
import puppeteer from "puppeteer-core";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const OUT = path.join(ROOT, "screenshots");
const BASE = process.env.VIEWER || "http://127.0.0.1:5179";

const shots = [
  { file: "01-front-grid.png", query: "shot=1&layout=grid&view=front" },
  { file: "02-close-grid.png", query: "shot=1&layout=grid&view=close" },
  { file: "03-front-original.png", query: "shot=1&layout=single&variant=original&view=front" },
  { file: "04-front-25.png", query: "shot=1&layout=single&variant=m25&view=front" },
  { file: "05-front-10.png", query: "shot=1&layout=single&variant=m10&view=front" },
  { file: "06-front-10-nm.png", query: "shot=1&layout=single&variant=m10nm&view=front" },
  { file: "07-front-05.png", query: "shot=1&layout=single&variant=m05&view=front" },
  { file: "08-front-05-nm.png", query: "shot=1&layout=single&variant=m05nm&view=front" },
  { file: "09-close-original.png", query: "shot=1&layout=single&variant=original&view=close" },
  { file: "10-close-10-nm.png", query: "shot=1&layout=single&variant=m10nm&view=close" },
  { file: "11-close-05-nm.png", query: "shot=1&layout=single&variant=m05nm&view=close" },
  { file: "12-close-decimate-10.png", query: "shot=1&layout=single&variant=d10&view=close" },
];

const browser = await puppeteer.launch({
  executablePath: process.env.CHROME || "/usr/bin/google-chrome",
  headless: "new",
  args: [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--use-gl=angle",
    "--use-angle=swiftshader",
    "--enable-unsafe-swiftshader",
    "--window-size=1600,1000",
  ],
});

const page = await browser.newPage();
await page.setViewport({ width: 1600, height: 1000, deviceScaleFactor: 1 });
page.on("pageerror", (error) => console.log("pageerror", error.message));
page.on("console", (msg) => {
  if (msg.type() === "error") console.log("console", msg.text());
});

for (const shot of shots) {
  const url = `${BASE}/?${shot.query}`;
  console.log("open", url);
  await page.goto(url, { waitUntil: "networkidle0", timeout: 60000 });
  await page.waitForFunction("window.__ready === true", { timeout: 30000 });
  await new Promise((resolve) => setTimeout(resolve, 400));
  await page.screenshot({ path: path.join(OUT, shot.file) });
  console.log("wrote", shot.file);
}

await browser.close();
