import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  ensureArrayOfNonEmptyStrings,
  ensureBoolean,
  ensureInList,
  ensureNonEmptyString,
  ensurePlainObject
} from "./validation.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const defaultConfigPath = path.resolve(
  __dirname,
  "..",
  "..",
  "config",
  "user",
  "app.config.json"
);

export const loadConfig = (configOptions = {}) => {
  const options =
    configOptions === undefined ? {} : ensurePlainObject(configOptions, "configOptions");
  const { configPath = defaultConfigPath } = options;
  const resolvedConfigPath = ensureNonEmptyString(configPath, "configPath");

  if (!fs.existsSync(resolvedConfigPath)) {
    throw new Error("Konfigurationsdatei fehlt.");
  }

  const raw = fs.readFileSync(resolvedConfigPath, "utf-8");
  const parsed = JSON.parse(raw);

  const appName = ensureNonEmptyString(parsed.appName, "appName");
  const debugEnabled = ensureBoolean(parsed.debugEnabled, "debugEnabled");
  const loggingEnabled = ensureBoolean(parsed.loggingEnabled, "loggingEnabled");
  const availableThemes = ensureArrayOfNonEmptyStrings(
    parsed.availableThemes,
    "availableThemes"
  );
  const theme = ensureInList(
    ensureNonEmptyString(parsed.theme, "theme"),
    availableThemes,
    "theme"
  );

  return {
    appName,
    debugEnabled,
    loggingEnabled,
    availableThemes,
    theme
  };
};
