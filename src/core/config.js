import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  ensureArrayOfNonEmptyStrings,
  ensureBoolean,
  ensureInList,
  ensureNonEmptyString,
  ensurePlainObject,
  ensurePositiveInteger
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
    throw new Error(
      `Konfigurationsdatei fehlt: ${resolvedConfigPath}. Bitte Startroutine ausführen oder Datei anlegen.`
    );
  }

  const raw = fs.readFileSync(resolvedConfigPath, "utf-8");
  const parsed = JSON.parse(raw);

  const allowedLogLevels = ["DEBUG", "INFO", "WARN", "ERROR"];
  const appName = ensureNonEmptyString(parsed.appName, "appName");
  const debugEnabled = ensureBoolean(parsed.debugEnabled, "debugEnabled");
  const loggingEnabled = ensureBoolean(parsed.loggingEnabled, "loggingEnabled");
  const logToFile = ensureBoolean(parsed.logToFile ?? false, "logToFile");
  const logLevel = ensureInList(
    ensureNonEmptyString(parsed.logLevel ?? "INFO", "logLevel"),
    allowedLogLevels,
    "logLevel"
  );
  const logFilePath = ensureNonEmptyString(
    parsed.logFilePath ?? "data/logs/app.log",
    "logFilePath"
  );
  const logRotateDaily = ensureBoolean(
    parsed.logRotateDaily ?? true,
    "logRotateDaily"
  );
  const logMaxSizeBytes = ensurePositiveInteger(
    parsed.logMaxSizeBytes ?? 5_242_880,
    "logMaxSizeBytes"
  );
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
    logToFile,
    logLevel,
    logFilePath,
    logRotateDaily,
    logMaxSizeBytes,
    availableThemes,
    theme
  };
};
