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
import { loadManifest } from "./manifestLoader.js";

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
  const { configPath = defaultConfigPath, manifest } = options;
  const resolvedConfigPath = ensureNonEmptyString(configPath, "configPath");
  const resolvedManifest =
    manifest === undefined
      ? loadManifest({ appRoot: options.appRoot, manifestPath: options.manifestPath })
      : ensurePlainObject(manifest, "manifest");
  const manifestApp = ensurePlainObject(resolvedManifest.app, "manifest.app");
  const manifestLogging = ensurePlainObject(
    resolvedManifest.logging,
    "manifest.logging"
  );
  const manifestThemes = ensurePlainObject(resolvedManifest.themes, "manifest.themes");
  const manifestLogLevels = ensureArrayOfNonEmptyStrings(
    manifestLogging.levels,
    "manifest.logging.levels"
  );

  if (!fs.existsSync(resolvedConfigPath)) {
    throw new Error("Konfigurationsdatei fehlt.");
  }

  const raw = fs.readFileSync(resolvedConfigPath, "utf-8");
  const parsed = JSON.parse(raw);

  const appName = ensureNonEmptyString(
    parsed.appName ?? manifestApp.name,
    "appName"
  );
  const debugEnabled = ensureBoolean(
    parsed.debugEnabled ?? manifestLogging.defaultDebugEnabled,
    "debugEnabled"
  );
  const loggingEnabled = ensureBoolean(
    parsed.loggingEnabled ?? manifestLogging.defaultLoggingEnabled,
    "loggingEnabled"
  );
  const logToFile = ensureBoolean(
    parsed.logToFile ?? manifestLogging.defaultLogToFile,
    "logToFile"
  );
  const logLevel = ensureInList(
    ensureNonEmptyString(parsed.logLevel ?? manifestLogging.defaultLevel, "logLevel"),
    manifestLogLevels,
    "logLevel"
  );
  const logFilePath = ensureNonEmptyString(
    parsed.logFilePath ?? manifestLogging.defaultLogFilePath,
    "logFilePath"
  );
  const logRotateDaily = ensureBoolean(
    parsed.logRotateDaily ?? manifestLogging.defaultRotateDaily,
    "logRotateDaily"
  );
  const logMaxSizeBytes = ensurePositiveInteger(
    parsed.logMaxSizeBytes ?? manifestLogging.defaultMaxSizeBytes,
    "logMaxSizeBytes"
  );
  const availableThemes = ensureArrayOfNonEmptyStrings(
    parsed.availableThemes ?? manifestThemes.available,
    "availableThemes"
  );
  const theme = ensureInList(
    ensureNonEmptyString(parsed.theme ?? manifestThemes.default, "theme"),
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
