import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  ensureBoolean,
  ensureInList,
  ensureNonEmptyString
} from "./validation.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const configPath = path.resolve(__dirname, "..", "..", "config", "app.config.json");

export const loadConfig = () => {
  if (!fs.existsSync(configPath)) {
    throw new Error("Konfigurationsdatei fehlt.");
  }

  const raw = fs.readFileSync(configPath, "utf-8");
  const parsed = JSON.parse(raw);

  const appName = ensureNonEmptyString(parsed.appName, "appName");
  const debugEnabled = ensureBoolean(parsed.debugEnabled, "debugEnabled");
  const loggingEnabled = ensureBoolean(parsed.loggingEnabled, "loggingEnabled");
  const availableThemes = Array.isArray(parsed.availableThemes)
    ? parsed.availableThemes
    : [];
  const theme = ensureInList(parsed.theme, availableThemes, "theme");

  return {
    appName,
    debugEnabled,
    loggingEnabled,
    availableThemes,
    theme
  };
};
