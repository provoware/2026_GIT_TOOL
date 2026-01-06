import path from "node:path";
import { fileURLToPath } from "node:url";
import { loadManifest } from "../src/utils/manifestLoader.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const appRoot = path.resolve(__dirname, "..");

const run = () => {
  console.log("\n[Start] Manifest-Prüfung (Manifest Check) läuft...");
  console.log("[Info] Ich prüfe die zentrale Default-Datei (Manifest).");

  const manifest = loadManifest({ appRoot });

  console.log(
    `[Erfolg] Manifest ok: ${manifest.app.name} (Version ${manifest.version}).`
  );
};

try {
  run();
} catch (error) {
  const message = error instanceof Error ? error.message : "Unbekannter Fehler";
  console.error(`\n[Fehler] Manifest-Prüfung fehlgeschlagen: ${message}`);
  console.error("[Hinweis] Bitte Datei config/manifest.json prüfen.");
  process.exitCode = 1;
}
