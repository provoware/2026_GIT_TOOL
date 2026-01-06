import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  ensureArrayOfNonEmptyStrings,
  ensureBoolean,
  ensureNonEmptyString,
  ensurePlainObject,
  ensurePositiveInteger
} from "./validation.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const DEFAULT_APP_ROOT = path.resolve(__dirname, "..", "..");
const DEFAULT_MANIFEST_PATH = path.resolve(
  __dirname,
  "..",
  "..",
  "config",
  "manifest.json"
);

const ensureOptionalString = (value, label) => {
  if (value === undefined || value === null || value === "") {
    return null;
  }
  return ensureNonEmptyString(value, label);
};

const ensureLogger = (logger) => {
  const target = ensurePlainObject(logger, "logger");
  ["info", "warn", "error", "debug"].forEach((key) => {
    if (typeof target[key] !== "function") {
      throw new Error(`logger.${key} muss eine Funktion sein.`);
    }
  });
  return target;
};

const resolvePath = (appRoot, target) => {
  const safeRoot = ensureNonEmptyString(appRoot, "appRoot");
  const safeTarget = ensureNonEmptyString(target, "target");
  return path.isAbsolute(safeTarget) ? safeTarget : path.resolve(safeRoot, safeTarget);
};

export const buildDefaultManifest = () => ({
  version: "1.0",
  app: {
    name: "2026 Git Tool",
    description: "Zentrale Defaults für App, Export, Themes, Logging und Pfade."
  },
  logging: {
    levels: ["DEBUG", "INFO", "WARN", "ERROR"],
    defaultLevel: "INFO",
    defaultLogFilePath: "data/logs/app.log",
    defaultRotateDaily: true,
    defaultMaxSizeBytes: 5_242_880,
    defaultLoggingEnabled: true,
    defaultDebugEnabled: true,
    defaultLogToFile: true
  },
  themes: {
    available: [
      "theme-high-contrast-dark",
      "theme-high-contrast-light",
      "theme-high-contrast-ocean",
      "theme-high-contrast-sand",
      "theme-high-contrast-forest",
      "theme-high-contrast-violet"
    ],
    default: "theme-high-contrast-dark"
  },
  exportRules: {
    allowedFormats: ["txt", "json"],
    exportsSubdir: "exports"
  },
  paths: {
    dataDir: "data",
    logsDir: "data/logs",
    templatesSeed: "data/templates_seed.json",
    templatesStatsSchema: "data/templates_stats_schema.json",
    pluginsDir: "plugins",
    userConfig: "config/user/app.config.json",
    qualityConfig: "config/user/quality.config.json",
    qualityManifest: "config/system/quality.manifest.json",
    standardsManifest: "config/system/standards.manifest.json"
  },
  templates: {
    defaultCategories: [
      "ChatGPT – Universal",
      "Agenten-Prompting",
      "Linux / Bash",
      "Entwickler / Code",
      "Electron / Desktop-Apps",
      "KI-Bild-Generierung",
      "Analyse / Struktur",
      "Automatisierung / Workflows",
      "Persönlich / Eigene"
    ]
  }
});

const normalizeLogging = (payload) => {
  const logging = ensurePlainObject(payload, "logging");
  const levels = ensureArrayOfNonEmptyStrings(logging.levels, "logging.levels");
  const defaultLevel = ensureNonEmptyString(logging.defaultLevel, "logging.defaultLevel");
  const defaultLogFilePath = ensureNonEmptyString(
    logging.defaultLogFilePath,
    "logging.defaultLogFilePath"
  );
  const defaultRotateDaily = ensureBoolean(
    logging.defaultRotateDaily,
    "logging.defaultRotateDaily"
  );
  const defaultMaxSizeBytes = ensurePositiveInteger(
    logging.defaultMaxSizeBytes,
    "logging.defaultMaxSizeBytes"
  );
  const defaultLoggingEnabled = ensureBoolean(
    logging.defaultLoggingEnabled,
    "logging.defaultLoggingEnabled"
  );
  const defaultDebugEnabled = ensureBoolean(
    logging.defaultDebugEnabled,
    "logging.defaultDebugEnabled"
  );
  const defaultLogToFile = ensureBoolean(
    logging.defaultLogToFile,
    "logging.defaultLogToFile"
  );

  if (!levels.includes(defaultLevel)) {
    throw new Error("logging.defaultLevel muss in logging.levels enthalten sein.");
  }

  return {
    levels,
    defaultLevel,
    defaultLogFilePath,
    defaultRotateDaily,
    defaultMaxSizeBytes,
    defaultLoggingEnabled,
    defaultDebugEnabled,
    defaultLogToFile
  };
};

const normalizeThemes = (payload) => {
  const themes = ensurePlainObject(payload, "themes");
  const available = ensureArrayOfNonEmptyStrings(themes.available, "themes.available");
  const defaultTheme = ensureNonEmptyString(themes.default, "themes.default");
  if (!available.includes(defaultTheme)) {
    throw new Error("themes.default muss in themes.available enthalten sein.");
  }
  return {
    available,
    default: defaultTheme
  };
};

const normalizeExportRules = (payload) => {
  const exportRules = ensurePlainObject(payload, "exportRules");
  const allowedFormats = ensureArrayOfNonEmptyStrings(
    exportRules.allowedFormats,
    "exportRules.allowedFormats"
  ).map((value) => value.toLowerCase());
  const exportsSubdir = ensureNonEmptyString(
    exportRules.exportsSubdir,
    "exportRules.exportsSubdir"
  );

  return {
    allowedFormats,
    exportsSubdir
  };
};

const normalizePaths = (payload, appRoot, manifestPath) => {
  const paths = ensurePlainObject(payload, "paths");
  const dataDir = ensureNonEmptyString(paths.dataDir, "paths.dataDir");
  const logsDir = ensureNonEmptyString(paths.logsDir, "paths.logsDir");
  const templatesSeed = ensureNonEmptyString(paths.templatesSeed, "paths.templatesSeed");
  const templatesStatsSchema = ensureNonEmptyString(
    paths.templatesStatsSchema,
    "paths.templatesStatsSchema"
  );
  const pluginsDir = ensureNonEmptyString(paths.pluginsDir, "paths.pluginsDir");
  const userConfig = ensureNonEmptyString(paths.userConfig, "paths.userConfig");
  const qualityConfig = ensureNonEmptyString(paths.qualityConfig, "paths.qualityConfig");
  const qualityManifest = ensureNonEmptyString(
    paths.qualityManifest,
    "paths.qualityManifest"
  );
  const standardsManifest = ensureNonEmptyString(
    paths.standardsManifest,
    "paths.standardsManifest"
  );

  const resolvedDataDir = resolvePath(appRoot, dataDir);
  const resolvedLogsDir = resolvePath(appRoot, logsDir);
  const resolvedTemplatesSeed = resolvePath(appRoot, templatesSeed);
  const resolvedTemplatesStatsSchema = resolvePath(appRoot, templatesStatsSchema);
  const resolvedPluginsDir = resolvePath(appRoot, pluginsDir);
  const resolvedUserConfig = resolvePath(appRoot, userConfig);
  const resolvedQualityConfig = resolvePath(appRoot, qualityConfig);
  const resolvedQualityManifest = resolvePath(appRoot, qualityManifest);
  const resolvedStandardsManifest = resolvePath(appRoot, standardsManifest);

  return {
    appRoot: ensureNonEmptyString(appRoot, "paths.appRoot"),
    manifestPath: ensureNonEmptyString(manifestPath, "paths.manifestPath"),
    dataDir: ensureNonEmptyString(resolvedDataDir, "paths.dataDir"),
    logsDir: ensureNonEmptyString(resolvedLogsDir, "paths.logsDir"),
    templatesSeed: ensureNonEmptyString(resolvedTemplatesSeed, "paths.templatesSeed"),
    templatesStatsSchema: ensureNonEmptyString(
      resolvedTemplatesStatsSchema,
      "paths.templatesStatsSchema"
    ),
    pluginsDir: ensureNonEmptyString(resolvedPluginsDir, "paths.pluginsDir"),
    userConfig: ensureNonEmptyString(resolvedUserConfig, "paths.userConfig"),
    qualityConfig: ensureNonEmptyString(resolvedQualityConfig, "paths.qualityConfig"),
    qualityManifest: ensureNonEmptyString(resolvedQualityManifest, "paths.qualityManifest"),
    standardsManifest: ensureNonEmptyString(
      resolvedStandardsManifest,
      "paths.standardsManifest"
    )
  };
};

const normalizeTemplates = (payload) => {
  const templates = ensurePlainObject(payload, "templates");
  const defaultCategories = ensureArrayOfNonEmptyStrings(
    templates.defaultCategories,
    "templates.defaultCategories"
  );
  return {
    defaultCategories
  };
};

const normalizeManifest = ({ rawManifest, appRoot, manifestPath }) => {
  const manifest = ensurePlainObject(rawManifest, "manifest");
  const version = ensureNonEmptyString(manifest.version, "version");
  const app = ensurePlainObject(manifest.app, "app");
  const appName = ensureNonEmptyString(app.name, "app.name");
  const appDescription = ensureOptionalString(app.description, "app.description");
  const exportRules = normalizeExportRules(manifest.exportRules);
  const paths = normalizePaths(manifest.paths, appRoot, manifestPath);
  const exportsDir = path.resolve(paths.dataDir, exportRules.exportsSubdir);

  return {
    version,
    app: {
      name: appName,
      description: appDescription ?? ""
    },
    logging: normalizeLogging(manifest.logging),
    themes: normalizeThemes(manifest.themes),
    exportRules,
    paths: {
      ...paths,
      exportsDir: ensureNonEmptyString(exportsDir, "paths.exportsDir")
    },
    templates: normalizeTemplates(manifest.templates)
  };
};

export const loadManifest = (options = {}) => {
  const settings = options === undefined ? {} : ensurePlainObject(options, "options");
  const manifestPath = ensureNonEmptyString(
    settings.manifestPath ?? DEFAULT_MANIFEST_PATH,
    "manifestPath"
  );
  const appRoot = ensureNonEmptyString(settings.appRoot ?? DEFAULT_APP_ROOT, "appRoot");
  const logger = settings.logger ? ensureLogger(settings.logger) : null;

  if (!fs.existsSync(manifestPath)) {
    throw new Error("Manifest-Datei fehlt.");
  }

  const raw = fs.readFileSync(manifestPath, "utf-8");
  const parsed = JSON.parse(raw);
  const manifest = normalizeManifest({ rawManifest: parsed, appRoot, manifestPath });

  if (logger) {
    logger.info(`Manifest geladen: ${manifest.app.name}`);
    logger.debug(`Manifest-Pfad: ${manifest.paths.manifestPath}`);
  }

  return ensurePlainObject(manifest, "manifest");
};
