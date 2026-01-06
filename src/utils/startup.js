import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { loadConfig } from "./config.js";
import { initializeTemplatesStorage } from "./templates.js";
import {
  ensureArrayOfNonEmptyStrings,
  ensureBoolean,
  ensureInList,
  ensureNonEmptyString,
  ensurePlainObject,
  ensurePositiveInteger
} from "./validation.js";
import {
  buildDefaultQualityConfig,
  buildDefaultQualityManifest
} from "./quality.js";
import { buildDefaultManifest, loadManifest } from "./manifestLoader.js";

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

const resolveManifestDefaults = (manifest) => {
  const safeManifest = manifest
    ? ensurePlainObject(manifest, "manifest")
    : loadManifest({ appRoot: DEFAULT_APP_ROOT });
  const app = ensurePlainObject(safeManifest.app, "manifest.app");
  const logging = ensurePlainObject(safeManifest.logging, "manifest.logging");
  const themes = ensurePlainObject(safeManifest.themes, "manifest.themes");

  return {
    app,
    logging,
    themes
  };
};

const resolveExportDir = ({ dataDir, manifest }) => {
  const safeManifest = ensurePlainObject(manifest, "manifest");
  const exportRules = ensurePlainObject(
    safeManifest.exportRules,
    "manifest.exportRules"
  );
  const exportsSubdir = ensureNonEmptyString(
    exportRules.exportsSubdir,
    "manifest.exportRules.exportsSubdir"
  );
  const resolvedDataDir = ensureNonEmptyString(dataDir, "dataDir");
  return path.join(resolvedDataDir, exportsSubdir);
};

const formatTimestampForFilename = (value = new Date().toISOString()) =>
  ensureNonEmptyString(value, "timestamp").replace(/[:.]/g, "-");

const buildBackupPath = ({ filePath, backupDir }) => {
  const safePath = ensureNonEmptyString(filePath, "filePath");
  const safeBackupDir = ensureNonEmptyString(backupDir, "backupDir");
  const filename = path.basename(safePath);
  const timestamp = formatTimestampForFilename();
  return path.join(safeBackupDir, `${filename}.backup-${timestamp}`);
};

const backupFile = ({ filePath, backupDir, logger, label }) => {
  const safeLogger = ensureLogger(logger);
  const safeLabel = ensureNonEmptyString(label, "label");
  const safePath = ensureNonEmptyString(filePath, "filePath");
  const { path: resolvedBackupDir } = ensureDirectoryExists(backupDir);

  if (!fs.existsSync(safePath)) {
    safeLogger.warn(`${safeLabel} konnte nicht gesichert werden: Datei fehlt.`);
    return null;
  }

  const backupPath = buildBackupPath({ filePath: safePath, backupDir: resolvedBackupDir });
  fs.copyFileSync(safePath, backupPath);
  safeLogger.warn(`${safeLabel} gesichert: ${backupPath}`);
  return ensureOptionalString(backupPath, "backupPath");
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

const buildRepairResult = ({ ok, backupPath }) => {
  const safeOk = ensureBoolean(ok, "ok");
  const safeBackupPath = ensureOptionalString(backupPath, "backupPath");
  return {
    ok: safeOk,
    backupPath: safeBackupPath
  };
};

const repairConfigFile = ({ configPath, backupDir, logger, reporter, manifest }) => {
  const safeLogger = ensureLogger(logger);
  const safeReporter = ensureReporter(reporter);
  const safeConfigPath = ensureNonEmptyString(configPath, "configPath");
  const safeBackupDir = ensureNonEmptyString(backupDir, "backupDir");

  const backupPath = backupFile({
    filePath: safeConfigPath,
    backupDir: safeBackupDir,
    logger: safeLogger,
    label: "Konfiguration"
  });

  const written = writeJsonFile(safeConfigPath, buildDefaultConfig(manifest));
  if (!written) {
    throw new Error("Konfiguration konnte nicht repariert werden.");
  }

  reportStatus(safeReporter, {
    level: "warning",
    message: "Konfiguration wurde automatisch repariert.",
    suggestion: "Bitte Einstellungen prüfen (Config) und speichern.",
    step: "config-repair"
  });

  return buildRepairResult({ ok: true, backupPath });
};

const repairTemplatesStorage = ({ dataDir, seedPath, logger, reporter }) => {
  const safeLogger = ensureLogger(logger);
  const safeReporter = ensureReporter(reporter);
  const safeSeedPath = ensureNonEmptyString(seedPath, "seedPath");
  const resolvedDir = ensureDirectoryExists(dataDir).path;
  const templatesPath = path.join(resolvedDir, "templates.json");

  const backupPath = backupFile({
    filePath: templatesPath,
    backupDir: path.join(resolvedDir, "backups"),
    logger: safeLogger,
    label: "Templates-Daten"
  });

  if (fs.existsSync(templatesPath)) {
    fs.rmSync(templatesPath, { force: true });
  }

  const { templatesCount } = initializeTemplatesStorage({
    dataDir: resolvedDir,
    seedPath: safeSeedPath,
    logger: safeLogger
  });

  reportStatus(safeReporter, {
    level: "warning",
    message: "Templates wurden automatisch repariert.",
    suggestion: "Bitte prüfen, ob alle Vorlagen vorhanden sind.",
    step: "templates-repair"
  });

  return buildRepairResult({ ok: templatesCount >= 0, backupPath });
};

const buildDefaultConfig = (manifest) => {
  const defaults = resolveManifestDefaults(manifest);
  const availableThemes = ensureArrayOfNonEmptyStrings(
    defaults.themes.available,
    "manifest.themes.available"
  );
  const theme = ensureNonEmptyString(
    defaults.themes.default,
    "manifest.themes.default"
  );

  return {
    appName: ensureNonEmptyString(defaults.app.name, "manifest.app.name"),
    debugEnabled: ensureBoolean(
      defaults.logging.defaultDebugEnabled,
      "manifest.logging.defaultDebugEnabled"
    ),
    loggingEnabled: ensureBoolean(
      defaults.logging.defaultLoggingEnabled,
      "manifest.logging.defaultLoggingEnabled"
    ),
    logToFile: ensureBoolean(
      defaults.logging.defaultLogToFile,
      "manifest.logging.defaultLogToFile"
    ),
    logLevel: ensureNonEmptyString(
      defaults.logging.defaultLevel,
      "manifest.logging.defaultLevel"
    ),
    logFilePath: ensureNonEmptyString(
      defaults.logging.defaultLogFilePath,
      "manifest.logging.defaultLogFilePath"
    ),
    logRotateDaily: ensureBoolean(
      defaults.logging.defaultRotateDaily,
      "manifest.logging.defaultRotateDaily"
    ),
    logMaxSizeBytes: ensurePositiveInteger(
      defaults.logging.defaultMaxSizeBytes,
      "manifest.logging.defaultMaxSizeBytes"
    ),
    theme,
    availableThemes
  };
};

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

const buildStartupResult = ({
  ok,
  configPath,
  dataDir,
  pluginsDir,
  steps,
  manifest
}) => {
  const safeOk = ensureBoolean(ok, "ok");
  const safeConfigPath = ensureNonEmptyString(configPath, "configPath");
  const safeDataDir = ensureNonEmptyString(dataDir, "dataDir");
  const safePluginsDir = ensureNonEmptyString(pluginsDir, "pluginsDir");
  const safeSteps = ensureArray(steps, "steps");
  const safeManifest = ensurePlainObject(manifest, "manifest");

  return {
    ok: safeOk,
    configPath: safeConfigPath,
    dataDir: safeDataDir,
    pluginsDir: safePluginsDir,
    steps: safeSteps,
    manifest: safeManifest
  };
};

export const runStartupRoutine = (options = {}) => {
  const settings = ensurePlainObject(options, "options");
  const logger = ensureLogger(settings.logger);
  const reporter = ensureReporter(settings.reportStatus ?? (() => {}));
  const appRoot = ensureNonEmptyString(settings.appRoot ?? DEFAULT_APP_ROOT, "appRoot");
  const { path: configRoot } = ensureDirectoryExists(path.join(appRoot, "config"));
  const manifestPath = ensureNonEmptyString(
    settings.manifestPath ?? path.join(configRoot, "manifest.json"),
    "manifestPath"
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

  ensureFileWithDefaults({
    filePath: manifestPath,
    buildDefault: buildDefaultManifest,
    description: "Manifest (App-Defaults)",
    logger,
    reporter,
    step: "manifest"
  });

  const manifest = loadManifest({ appRoot, manifestPath, logger });
  const configPath = ensureNonEmptyString(
    settings.configPath ?? manifest.paths.userConfig,
    "configPath"
  );
  const dataDir = ensureNonEmptyString(
    settings.dataDir ?? manifest.paths.dataDir,
    "dataDir"
  );
  const pluginsDir = ensureNonEmptyString(
    settings.pluginsDir ?? manifest.paths.pluginsDir,
    "pluginsDir"
  );
  const { path: systemDir } = ensureDirectoryExists(
    path.dirname(manifest.paths.qualityManifest)
  );
  const { path: configDir } = ensureDirectoryExists(path.dirname(configPath));
  const { path: resolvedDataDir } = ensureDirectoryExists(dataDir);
  const { path: resolvedPluginsDir } = ensureDirectoryExists(pluginsDir);
  const exportDirPath = resolveExportDir({ dataDir: resolvedDataDir, manifest });
  const { path: exportDir } = ensureDirectoryExists(exportDirPath);

  logger.debug(
    `Ordner geprüft: system=${systemDir}, config=${configDir}, data=${resolvedDataDir}, plugins=${resolvedPluginsDir}, exports=${exportDir}`
  );

  pushStep({
    level: "success",
    message: "Ordnerstruktur geprüft (System/Config/Data/Plugins).",
    step: "directories"
  });

  ensureFileWithDefaults({
    filePath: manifest.paths.standardsManifest,
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
    filePath: manifest.paths.qualityManifest,
    buildDefault: buildDefaultQualityManifest,
    description: "Qualitäts-Manifest (Quality Manifest)",
    logger,
    reporter,
    step: "quality-manifest"
  });

  ensureFileWithDefaults({
    filePath: configPath,
    buildDefault: () => buildDefaultConfig(manifest),
    description: "Konfiguration (Config)",
    logger,
    reporter,
    step: "config"
  });

  ensureFileWithDefaults({
    filePath: manifest.paths.qualityConfig,
    buildDefault: buildDefaultQualityConfig,
    description: "Qualitäts-Konfiguration (Quality Config)",
    logger,
    reporter,
    step: "quality-config"
  });

  const seedPath = manifest.paths.templatesSeed;
  const statsSchemaPath = manifest.paths.templatesStatsSchema;

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
    config = loadConfig({ configPath, manifest });
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

    try {
      const repairResult = repairConfigFile({
        configPath,
        backupDir: path.join(configDir, "backups"),
        logger,
        reporter,
        manifest
      });
      if (!repairResult.ok) {
        throw new Error("Konfiguration konnte nicht repariert werden.");
      }
      config = loadConfig({ configPath, manifest });
    } catch (repairError) {
      void repairError;
      logger.error("Konfiguration konnte nicht repariert werden.");
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
        steps,
        manifest
      });
    }
  }

  logger.debug(`Start-Config geladen: ${config.appName}`);

  try {
    const { templatesCount } = initializeTemplatesStorage({
      dataDir: resolvedDataDir,
      logger,
      manifest
    });
    pushStep({
      level: "success",
      message: `Templates geprüft (${templatesCount} vorhanden).`,
      step: "templates"
    });
  } catch (error) {
    const hint = mapErrorToHint(error, "Templates konnten nicht vorbereitet werden.");
    logger.warn(hint.message);
    pushStep({
      level: "warning",
      message: hint.message,
      suggestion: hint.suggestion,
      step: "templates"
    });

    try {
      const repairResult = repairTemplatesStorage({
        dataDir: resolvedDataDir,
        seedPath,
        logger,
        reporter
      });
      if (!repairResult.ok) {
        throw new Error("Templates konnten nicht repariert werden.");
      }
      pushStep({
        level: "success",
        message: "Templates nach Reparatur bereit.",
        step: "templates"
      });
    } catch (repairError) {
      void repairError;
      logger.error("Templates konnten nicht repariert werden.");
      pushStep({
        level: "error",
        message: "Templates konnten nicht repariert werden.",
        suggestion: "Bitte Backups prüfen oder neu importieren.",
        step: "templates"
      });
      return buildStartupResult({
        ok: false,
        configPath,
        dataDir: resolvedDataDir,
        pluginsDir: resolvedPluginsDir,
        steps,
        manifest
      });
    }
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
    steps,
    manifest
  });
};
