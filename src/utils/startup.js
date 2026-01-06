import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { loadConfig } from "./config.js";
import { initializeTemplatesStorage } from "./templates.js";
import {
  ensureBoolean,
  ensureInList,
  ensureNonEmptyString,
  ensurePlainObject
} from "./validation.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const DEFAULT_APP_ROOT = path.resolve(__dirname, "..", "..");
const STATUS_LEVELS = ["info", "success", "warning", "error"];

const ensureLogger = (logger) => {
  const target = ensurePlainObject(logger, "logger");
  ["info", "warn", "error", "debug"].forEach((key) => {
    if (typeof target[key] !== "function") {
      throw new Error(`logger.${key} muss eine Funktion sein.`);
    }
  });
  return target;
};

const ensureReporter = (reporter) => {
  if (typeof reporter !== "function") {
    throw new Error("reportStatus muss eine Funktion sein.");
  }
  return reporter;
};

const ensureOptionalString = (value, label) => {
  if (value === undefined || value === null || value === "") {
    return null;
  }
  return ensureNonEmptyString(value, label);
};

const ensureArray = (value, label) => {
  if (!Array.isArray(value)) {
    throw new Error(`${label} muss eine Liste sein.`);
  }
  return value;
};

const ensureDirectoryExists = (directoryPath) => {
  const resolvedPath = ensureNonEmptyString(directoryPath, "directoryPath");
  const existed = fs.existsSync(resolvedPath);
  if (!existed) {
    fs.mkdirSync(resolvedPath, { recursive: true });
  }
  if (!fs.statSync(resolvedPath).isDirectory()) {
    throw new Error("directoryPath muss ein Ordner sein.");
  }
  return {
    path: resolvedPath,
    created: !existed
  };
};

const writeJsonFile = (filePath, payload) => {
  const resolvedPath = ensureNonEmptyString(filePath, "filePath");
  if (payload === null || typeof payload !== "object") {
    throw new Error("payload muss ein Objekt sein.");
  }
  fs.writeFileSync(resolvedPath, JSON.stringify(payload, null, 2));
  return fs.existsSync(resolvedPath);
};

const buildStatusPayload = ({ level, message, suggestion, step }) => {
  const safeLevel = ensureInList(
    ensureNonEmptyString(level ?? "info", "level"),
    STATUS_LEVELS,
    "level"
  );
  const safeMessage = ensureNonEmptyString(message, "message");
  const safeSuggestion = ensureOptionalString(suggestion, "suggestion");
  const safeStep = ensureOptionalString(step, "step");
  const timestamp = ensureNonEmptyString(new Date().toISOString(), "timestamp");

  const payload = {
    level: safeLevel,
    message: safeMessage,
    timestamp
  };

  if (safeSuggestion) {
    payload.suggestion = safeSuggestion;
  }
  if (safeStep) {
    payload.step = safeStep;
  }

  return payload;
};

const reportStatus = (reporter, payload) => {
  const safeReporter = ensureReporter(reporter);
  const safePayload = buildStatusPayload(payload);
  safeReporter(safePayload);
  return safePayload;
};

const buildDefaultConfig = () => ({
  appName: "2026 Git Tool",
  debugEnabled: true,
  loggingEnabled: true,
  theme: "theme-high-contrast-dark",
  availableThemes: [
    "theme-high-contrast-dark",
    "theme-high-contrast-light",
    "theme-high-contrast-ocean",
    "theme-high-contrast-sand"
  ]
});

const buildDefaultSeed = (nowIso) => ({
  meta: {
    version: "2.0",
    created: nowIso,
    description: "Automatisch erzeugtes Start-Seed für Templates (Fallback)."
  },
  templates: []
});

const buildDefaultStatsSchema = () => ({
  version: "1.0",
  description: "Schema für Template-Statistiken (minimaler Fallback).",
  requiredFields: ["meta", "totals", "topTemplates", "categoryStats"]
});

const mapErrorToHint = (error, fallbackMessage) => {
  const rawMessage = error instanceof Error ? error.message : "Unbekannter Fehler";
  const message = ensureNonEmptyString(fallbackMessage, "fallbackMessage");

  if (rawMessage.includes("Konfigurationsdatei fehlt")) {
    return {
      message: "Konfiguration fehlt. Ich habe eine Standard-Datei angelegt.",
      suggestion: "Bitte prüfen Sie die Einstellungen (Config) und speichern Sie erneut."
    };
  }

  if (rawMessage.includes("Vorlage für templates.json fehlt")) {
    return {
      message: "Template-Vorlage fehlt. Ich habe eine leere Vorlage erstellt.",
      suggestion: "Falls nötig, importieren Sie Ihre Templates erneut."
    };
  }

  if (rawMessage.includes("JSON")) {
    return {
      message: "Eine Datei hat ungültiges JSON (Datenformat).",
      suggestion: "Bitte Datei öffnen und reparieren oder neu anlegen."
    };
  }

  return {
    message,
    suggestion: "Bitte prüfen Sie die Datei und starten Sie erneut."
  };
};

const ensureFileWithDefaults = ({
  filePath,
  buildDefault,
  description,
  logger,
  reporter,
  step
}) => {
  const safePath = ensureNonEmptyString(filePath, "filePath");
  const safeDescription = ensureNonEmptyString(description, "description");
  const safeLogger = ensureLogger(logger);
  const safeReporter = ensureReporter(reporter);
  const safeStep = ensureNonEmptyString(step, "step");

  if (!fs.existsSync(safePath)) {
    const created = writeJsonFile(safePath, buildDefault());
    if (created) {
      safeLogger.info(`${safeDescription} wurde automatisch erstellt.`);
      reportStatus(safeReporter, {
        level: "warning",
        message: `${safeDescription} fehlte und wurde erstellt.`,
        suggestion: "Bitte Inhalt kurz prüfen (Sicherheits-Check).",
        step: safeStep
      });
      return true;
    }
    throw new Error(`${safeDescription} konnte nicht erstellt werden.`);
  }

  reportStatus(safeReporter, {
    level: "success",
    message: `${safeDescription} gefunden.`,
    step: safeStep
  });
  return true;
};

const buildStartupResult = ({ ok, configPath, dataDir, pluginsDir, steps }) => {
  const safeOk = ensureBoolean(ok, "ok");
  const safeConfigPath = ensureNonEmptyString(configPath, "configPath");
  const safeDataDir = ensureNonEmptyString(dataDir, "dataDir");
  const safePluginsDir = ensureNonEmptyString(pluginsDir, "pluginsDir");
  const safeSteps = ensureArray(steps, "steps");

  return {
    ok: safeOk,
    configPath: safeConfigPath,
    dataDir: safeDataDir,
    pluginsDir: safePluginsDir,
    steps: safeSteps
  };
};

export const runStartupRoutine = (options = {}) => {
  const settings = ensurePlainObject(options, "options");
  const logger = ensureLogger(settings.logger);
  const reporter = ensureReporter(settings.reportStatus ?? (() => {}));
  const appRoot = ensureNonEmptyString(settings.appRoot ?? DEFAULT_APP_ROOT, "appRoot");
  const defaultConfigPath = path.join(appRoot, "config", "user", "app.config.json");
  const defaultSystemDir = path.join(appRoot, "config", "system");
  const defaultDataDir = path.join(appRoot, "data");
  const defaultPluginsDir = path.join(appRoot, "plugins");
  const configPath = ensureNonEmptyString(settings.configPath ?? defaultConfigPath, "configPath");
  const dataDir = ensureNonEmptyString(settings.dataDir ?? defaultDataDir, "dataDir");
  const pluginsDir = ensureNonEmptyString(
    settings.pluginsDir ?? defaultPluginsDir,
    "pluginsDir"
  );
  const steps = [];

  const pushStep = (payload) => {
    const step = reportStatus(reporter, payload);
    steps.push(step);
    return step;
  };

  logger.info("Startroutine gestartet.");
  pushStep({
    level: "info",
    message: "Startprüfung läuft (Auto-Check).",
    suggestion: "Bitte kurz warten, ich prüfe Dateien und Ordner.",
    step: "start"
  });

  const { path: systemDir } = ensureDirectoryExists(defaultSystemDir);
  const { path: configDir } = ensureDirectoryExists(path.dirname(configPath));
  const { path: resolvedDataDir } = ensureDirectoryExists(dataDir);
  const { path: resolvedPluginsDir } = ensureDirectoryExists(pluginsDir);
  const { path: exportDir } = ensureDirectoryExists(path.join(resolvedDataDir, "exports"));

  logger.debug(
    `Ordner geprüft: system=${systemDir}, config=${configDir}, data=${resolvedDataDir}, plugins=${resolvedPluginsDir}, exports=${exportDir}`
  );

  pushStep({
    level: "success",
    message: "Ordnerstruktur geprüft (System/Config/Data/Plugins).",
    step: "directories"
  });

  ensureFileWithDefaults({
    filePath: path.join(systemDir, "standards.manifest.json"),
    buildDefault: () => ({
      version: "1.0",
      created: new Date().toISOString(),
      description: "System-Standards für Qualitätsprüfungen (Fallback)."
    }),
    description: "System-Manifest (Standards)",
    logger,
    reporter,
    step: "system"
  });

  ensureFileWithDefaults({
    filePath: configPath,
    buildDefault: buildDefaultConfig,
    description: "Konfiguration (Config)",
    logger,
    reporter,
    step: "config"
  });

  const seedPath = path.join(resolvedDataDir, "templates_seed.json");
  const statsSchemaPath = path.join(resolvedDataDir, "templates_stats_schema.json");

  ensureFileWithDefaults({
    filePath: seedPath,
    buildDefault: () => buildDefaultSeed(new Date().toISOString()),
    description: "Template-Seed (Vorlage)",
    logger,
    reporter,
    step: "seed"
  });

  ensureFileWithDefaults({
    filePath: statsSchemaPath,
    buildDefault: buildDefaultStatsSchema,
    description: "Statistik-Schema (Schema)",
    logger,
    reporter,
    step: "stats-schema"
  });

  let config;
  try {
    config = loadConfig({ configPath });
    pushStep({
      level: "success",
      message: "Konfiguration geprüft und gültig.",
      step: "config-validate"
    });
  } catch (error) {
    const hint = mapErrorToHint(error, "Konfiguration konnte nicht geladen werden.");
    logger.warn(hint.message);
    pushStep({
      level: "warning",
      message: hint.message,
      suggestion: hint.suggestion,
      step: "config-validate"
    });

    const fallbackOk = writeJsonFile(configPath, buildDefaultConfig());
    if (!fallbackOk) {
      pushStep({
        level: "error",
        message: "Konfiguration konnte nicht repariert werden.",
        suggestion: "Bitte Datei löschen und neu starten.",
        step: "config-validate"
      });
      return buildStartupResult({
        ok: false,
        configPath,
        dataDir: resolvedDataDir,
        pluginsDir: resolvedPluginsDir,
        steps
      });
    }

    config = loadConfig({ configPath });
  }

  logger.debug(`Start-Config geladen: ${config.appName}`);

  try {
    const { templatesCount } = initializeTemplatesStorage({
      dataDir: resolvedDataDir,
      logger
    });
    pushStep({
      level: "success",
      message: `Templates geprüft (${templatesCount} vorhanden).`,
      step: "templates"
    });
  } catch (error) {
    const hint = mapErrorToHint(error, "Templates konnten nicht vorbereitet werden.");
    logger.error(hint.message);
    pushStep({
      level: "error",
      message: hint.message,
      suggestion: hint.suggestion,
      step: "templates"
    });
    return buildStartupResult({
      ok: false,
      configPath,
      dataDir: resolvedDataDir,
      pluginsDir: resolvedPluginsDir,
      steps
    });
  }

  pushStep({
    level: "success",
    message: "Startroutine abgeschlossen. Alles bereit.",
    step: "done"
  });

  return buildStartupResult({
    ok: true,
    configPath,
    dataDir: resolvedDataDir,
    pluginsDir: resolvedPluginsDir,
    steps
  });
};
