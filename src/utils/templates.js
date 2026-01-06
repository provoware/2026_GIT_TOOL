import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import {
  ensureArrayOfNonEmptyStrings,
  ensureBoolean,
  ensureNonEmptyString,
  ensurePlainObject
} from "./validation.js";
import { loadManifest } from "./manifestLoader.js";

const resolveManifest = (manifest) =>
  manifest ? ensurePlainObject(manifest, "manifest") : loadManifest();

const resolveTemplatesDefaults = (manifest) => {
  const safeManifest = resolveManifest(manifest);
  const paths = ensurePlainObject(safeManifest.paths, "manifest.paths");
  return {
    dataDir: ensureNonEmptyString(paths.dataDir, "manifest.paths.dataDir"),
    templatesSeed: ensureNonEmptyString(
      paths.templatesSeed,
      "manifest.paths.templatesSeed"
    )
  };
};

const resolveExportRules = (manifest) => {
  const safeManifest = resolveManifest(manifest);
  const exportRules = ensurePlainObject(
    safeManifest.exportRules,
    "manifest.exportRules"
  );
  const allowedFormats = ensureArrayOfNonEmptyStrings(
    exportRules.allowedFormats,
    "manifest.exportRules.allowedFormats"
  ).map((value) => value.toLowerCase());
  const exportsSubdir = ensureNonEmptyString(
    exportRules.exportsSubdir,
    "manifest.exportRules.exportsSubdir"
  );
  return {
    allowedFormats,
    exportsSubdir
  };
};

const resolveDefaultCategories = (manifest) => {
  const safeManifest = resolveManifest(manifest);
  const templates = ensurePlainObject(safeManifest.templates, "manifest.templates");
  return ensureArrayOfNonEmptyStrings(
    templates.defaultCategories,
    "manifest.templates.defaultCategories"
  );
};

const ensureNumber = (value, label) => {
  if (typeof value !== "number" || Number.isNaN(value)) {
    throw new Error(`${label} muss eine Zahl sein.`);
  }

  return value;
};

const ensureNullableIsoString = (value, label) => {
  if (value === null) {
    return null;
  }

  const text = ensureNonEmptyString(value, label);
  if (Number.isNaN(Date.parse(text))) {
    throw new Error(`${label} muss ein gültiges ISO-Datum sein.`);
  }

  return text;
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

const ensureDirectoryExists = (directoryPath) => {
  const resolvedPath = ensureNonEmptyString(directoryPath, "directoryPath");
  if (!fs.existsSync(resolvedPath)) {
    fs.mkdirSync(resolvedPath, { recursive: true });
  }
  if (!fs.statSync(resolvedPath).isDirectory()) {
    throw new Error("directoryPath muss ein Ordner sein.");
  }
  return resolvedPath;
};

const sanitizeFilename = (value) =>
  value
    .normalize("NFKD")
    .replace(/[^a-zA-Z0-9\s._-]/g, "")
    .replace(/\s+/g, " ")
    .trim();

export const ensureValidFilename = (value, label) => {
  const raw = ensureNonEmptyString(value, label);
  const cleaned = sanitizeFilename(raw);
  if (cleaned.length === 0) {
    throw new Error(`${label} ist ungültig.`);
  }
  if (cleaned.includes(path.sep) || cleaned.includes("..")) {
    throw new Error(`${label} enthält unerlaubte Zeichen.`);
  }
  return cleaned;
};

const normalizeTags = (tags) => {
  if (tags === undefined) {
    return [];
  }
  if (!Array.isArray(tags)) {
    throw new Error("tags muss eine Liste sein.");
  }
  return tags.map((tag, index) => ensureNonEmptyString(tag, `tags[${index}]`));
};

const normalizeTemplate = (template, nowIso) => {
  const data = ensurePlainObject(template, "template");
  const id = ensureNonEmptyString(data.id, "template.id");
  const title = ensureNonEmptyString(data.title, "template.title");
  const category = ensureNonEmptyString(data.category, "template.category");
  const description = ensureNonEmptyString(
    data.description ?? "Ohne Beschreibung.",
    "template.description"
  );
  const content = ensureNonEmptyString(data.content, "template.content");
  const favorite = ensureBoolean(data.favorite ?? false, "template.favorite");
  const usageCount = ensureNumber(data.usageCount ?? 0, "template.usageCount");
  const lastUsed = ensureNullableIsoString(data.lastUsed ?? null, "template.lastUsed");
  const created = ensureNullableIsoString(data.created ?? nowIso, "template.created");
  const updated = ensureNullableIsoString(data.updated ?? nowIso, "template.updated");
  const editable = ensureBoolean(data.editable ?? true, "template.editable");
  const tags = normalizeTags(data.tags ?? []);

  return {
    ...data,
    id,
    title,
    category,
    description,
    content,
    favorite,
    usageCount,
    lastUsed,
    created,
    updated,
    tags,
    editable
  };
};

const normalizeTemplatesPayload = (payload, nowIso) => {
  const data = ensurePlainObject(payload, "payload");
  const meta = ensurePlainObject(data.meta ?? {}, "payload.meta");
  const version = ensureNonEmptyString(meta.version ?? "2.0", "meta.version");
  const created = ensureNullableIsoString(meta.created ?? nowIso, "meta.created");
  const lastUpdated = ensureNullableIsoString(meta.lastUpdated ?? nowIso, "meta.lastUpdated");
  const templates = Array.isArray(data.templates) ? data.templates : [];
  const normalizedTemplates = templates.map((template) => normalizeTemplate(template, nowIso));

  return {
    meta: {
      version,
      created,
      lastUpdated
    },
    templates: normalizedTemplates
  };
};

export const getDefaultCategories = (manifest) =>
  ensureArrayOfNonEmptyStrings(resolveDefaultCategories(manifest), "defaultCategories");

export const computeTemplatesStats = (templates, nowIso = new Date().toISOString()) => {
  const list = Array.isArray(templates) ? templates : [];
  const statsTemplates = list.map((template) => normalizeTemplate(template, nowIso));
  const favorites = statsTemplates.filter((template) => template.favorite);
  const usedAtLeastOnce = statsTemplates.filter((template) => template.usageCount > 0);
  const usageTotal = statsTemplates.reduce((sum, template) => sum + template.usageCount, 0);

  const sortByUsage = (a, b) => {
    if (b.usageCount !== a.usageCount) {
      return b.usageCount - a.usageCount;
    }
    const aDate = a.lastUsed ?? "";
    const bDate = b.lastUsed ?? "";
    if (bDate !== aDate) {
      return bDate.localeCompare(aDate);
    }
    return a.title.localeCompare(b.title, "de");
  };

  const toSummary = (template) => ({
    id: template.id,
    title: template.title,
    category: template.category,
    usageCount: template.usageCount,
    lastUsed: template.lastUsed,
    favorite: template.favorite
  });

  const topByUsage = [...statsTemplates].sort(sortByUsage).slice(0, 10).map(toSummary);
  const topFavorites = [...favorites].sort(sortByUsage).slice(0, 10).map((template) => ({
    id: template.id,
    title: template.title,
    category: template.category,
    usageCount: template.usageCount,
    lastUsed: template.lastUsed
  }));
  const recentlyUsed = [...statsTemplates]
    .filter((template) => template.lastUsed)
    .sort((a, b) => (b.lastUsed ?? "").localeCompare(a.lastUsed ?? ""))
    .slice(0, 10)
    .map((template) => ({
      id: template.id,
      title: template.title,
      category: template.category,
      lastUsed: template.lastUsed,
      usageCount: template.usageCount
    }));

  const categoryStats = statsTemplates.reduce((acc, template) => {
    if (!acc[template.category]) {
      acc[template.category] = [];
    }
    acc[template.category].push(template);
    return acc;
  }, {});

  const categorySummary = Object.fromEntries(
    Object.entries(categoryStats).map(([category, templatesInCategory]) => {
      const favoritesCount = templatesInCategory.filter((template) => template.favorite).length;
      const usageTotalCategory = templatesInCategory.reduce(
        (sum, template) => sum + template.usageCount,
        0
      );
      return [category, {
        count: templatesInCategory.length,
        favorites: favoritesCount,
        usageTotal: usageTotalCategory
      }];
    })
  );

  return {
    meta: {
      version: "1.0",
      generated: ensureNonEmptyString(nowIso, "stats.generated")
    },
    totals: {
      templatesCount: statsTemplates.length,
      favoritesCount: favorites.length,
      usageTotal,
      usedAtLeastOnce: usedAtLeastOnce.length
    },
    topTemplates: {
      topByUsage,
      topFavorites,
      recentlyUsed
    },
    categoryStats: categorySummary
  };
};

export const initializeTemplatesStorage = ({
  dataDir,
  seedPath,
  logger,
  manifest
}) => {
  const safeLogger = ensureLogger(logger);
  const defaults = resolveTemplatesDefaults(manifest);
  const resolvedDir = ensureDirectoryExists(dataDir ?? defaults.dataDir);
  const resolvedSeedPath = ensureNonEmptyString(
    seedPath ?? defaults.templatesSeed,
    "seedPath"
  );
  const nowIso = new Date().toISOString();
  const templatesPath = path.join(resolvedDir, "templates.json");

  if (!fs.existsSync(templatesPath)) {
    if (!fs.existsSync(resolvedSeedPath)) {
      throw new Error("Vorlage für templates.json fehlt.");
    }
    const seedRaw = fs.readFileSync(resolvedSeedPath, "utf-8");
    const seedData = JSON.parse(seedRaw);
    const normalized = normalizeTemplatesPayload(seedData, nowIso);
    fs.writeFileSync(templatesPath, JSON.stringify(normalized, null, 2));
    safeLogger.info("templates.json wurde neu angelegt.");
  }

  const loaded = loadTemplatesData({ dataDir: resolvedDir, logger: safeLogger });
  const stats = computeTemplatesStats(loaded.templates, nowIso);
  fs.writeFileSync(path.join(resolvedDir, "templates_stats.json"), JSON.stringify(stats, null, 2));
  safeLogger.info("templates_stats.json wurde aktualisiert.");

  return {
    templatesPath,
    statsPath: path.join(resolvedDir, "templates_stats.json"),
    templatesCount: loaded.templates.length
  };
};

export const loadTemplatesData = ({ dataDir, logger, manifest } = {}) => {
  const safeLogger = ensureLogger(logger);
  const defaults = resolveTemplatesDefaults(manifest);
  const resolvedDir = ensureDirectoryExists(dataDir ?? defaults.dataDir);
  const templatesPath = path.join(resolvedDir, "templates.json");
  const nowIso = new Date().toISOString();

  if (!fs.existsSync(templatesPath)) {
    throw new Error("templates.json fehlt.");
  }

  const raw = fs.readFileSync(templatesPath, "utf-8");
  const parsed = JSON.parse(raw);
  const normalized = normalizeTemplatesPayload(parsed, nowIso);

  safeLogger.debug("templates.json geladen und validiert.");
  return normalized;
};

export const saveTemplatesData = ({ dataDir, payload, logger, manifest } = {}) => {
  const safeLogger = ensureLogger(logger);
  const defaults = resolveTemplatesDefaults(manifest);
  const resolvedDir = ensureDirectoryExists(dataDir ?? defaults.dataDir);
  const nowIso = new Date().toISOString();
  const templatesPath = path.join(resolvedDir, "templates.json");
  const normalized = normalizeTemplatesPayload(payload, nowIso);
  const nextPayload = {
    meta: {
      ...normalized.meta,
      lastUpdated: nowIso
    },
    templates: normalized.templates.map((template) => ({
      ...template,
      updated: nowIso
    }))
  };

  fs.writeFileSync(templatesPath, JSON.stringify(nextPayload, null, 2));
  safeLogger.info("templates.json gespeichert.");

  const stats = computeTemplatesStats(nextPayload.templates, nowIso);
  fs.writeFileSync(path.join(resolvedDir, "templates_stats.json"), JSON.stringify(stats, null, 2));
  safeLogger.info("templates_stats.json gespeichert.");

  return nextPayload;
};

const buildHash = (template) => {
  const content = `${template.title}::${template.content}`;
  return crypto.createHash("sha256").update(content).digest("hex");
};

export const importTemplatesFromFile = ({
  dataDir,
  filePath,
  logger,
  manifest
}) => {
  const safeLogger = ensureLogger(logger);
  const defaults = resolveTemplatesDefaults(manifest);
  const resolvedDir = ensureDirectoryExists(dataDir ?? defaults.dataDir);
  const sourcePath = ensureNonEmptyString(filePath, "filePath");
  if (!fs.existsSync(sourcePath)) {
    throw new Error("Importdatei fehlt.");
  }

  const incomingRaw = fs.readFileSync(sourcePath, "utf-8");
  const incoming = JSON.parse(incomingRaw);
  const existing = loadTemplatesData({ dataDir: resolvedDir, logger: safeLogger });
  const nowIso = new Date().toISOString();
  const incomingTemplates = Array.isArray(incoming.templates) ? incoming.templates : [];

  const existingHashes = new Set(existing.templates.map(buildHash));
  const existingTitles = new Set(existing.templates.map((template) => template.title));

  const merged = [...existing.templates];
  incomingTemplates.forEach((template) => {
    const normalized = normalizeTemplate(template, nowIso);
    const hash = buildHash(normalized);
    if (existingHashes.has(hash)) {
      return;
    }

    let title = normalized.title;
    let suffix = 2;
    while (existingTitles.has(title)) {
      title = `${normalized.title} (${suffix})`;
      suffix += 1;
    }

    const imported = {
      ...normalized,
      id: crypto.randomUUID(),
      title,
      usageCount: 0,
      lastUsed: null,
      created: nowIso,
      updated: nowIso
    };

    existingHashes.add(hash);
    existingTitles.add(imported.title);
    merged.push(imported);
  });

  const saved = saveTemplatesData({
    dataDir: resolvedDir,
    payload: { meta: existing.meta, templates: merged },
    logger: safeLogger
  });
  safeLogger.info("Templates wurden importiert.");
  return saved;
};

const ensureExportDirectory = ({ dataDir, manifest }) => {
  const { exportsSubdir } = resolveExportRules(manifest);
  const exportDir = path.join(dataDir, exportsSubdir);
  return ensureDirectoryExists(exportDir);
};

export const exportTemplateToFile = ({
  dataDir,
  template,
  format = "txt",
  logger,
  manifest
}) => {
  const safeLogger = ensureLogger(logger);
  const defaults = resolveTemplatesDefaults(manifest);
  const resolvedDir = ensureDirectoryExists(dataDir ?? defaults.dataDir);
  const { allowedFormats } = resolveExportRules(manifest);
  const safeTemplate = normalizeTemplate(template, new Date().toISOString());
  const exportDir = ensureExportDirectory({ dataDir: resolvedDir, manifest });
  const safeName = ensureValidFilename(safeTemplate.title, "template.title");
  const fileFormat = ensureNonEmptyString(format, "format").toLowerCase();

  if (!allowedFormats.includes(fileFormat)) {
    throw new Error("Format ist nicht erlaubt.");
  }

  const timestamp = new Date().toISOString().replace(/[:]/g, "-");
  const baseName = `${safeName}-${timestamp}`;
  const filePath = path.join(exportDir, `${baseName}.${fileFormat}`);

  if (fileFormat === "txt") {
    const text = `${safeTemplate.title}\n\n${safeTemplate.description}\n\n${safeTemplate.content}\n`;
    fs.writeFileSync(filePath, text);
  } else if (fileFormat === "json") {
    fs.writeFileSync(filePath, JSON.stringify(safeTemplate, null, 2));
  } else {
    throw new Error("Format muss txt oder json sein.");
  }

  safeLogger.info(`Template exportiert: ${filePath}`);
  return filePath;
};

const buildZip = async (destination, entries) => {
  const { default: archiver } = await import("archiver");
  return new Promise((resolve, reject) => {
    const output = fs.createWriteStream(destination);
    const archive = archiver("zip", { zlib: { level: 9 } });

    output.on("close", () => resolve(destination));
    archive.on("error", (error) => reject(error));

    archive.pipe(output);
    entries.forEach(({ name, content }) => archive.append(content, { name }));
    archive.finalize();
  });
};

export const exportCategoryZip = async ({
  dataDir,
  category,
  logger,
  manifest
}) => {
  const safeLogger = ensureLogger(logger);
  const defaults = resolveTemplatesDefaults(manifest);
  const resolvedDir = ensureDirectoryExists(dataDir ?? defaults.dataDir);
  const categoryName = ensureNonEmptyString(category, "category");
  const data = loadTemplatesData({ dataDir: resolvedDir, logger: safeLogger });
  const templates = data.templates.filter((template) => template.category === categoryName);
  const exportDir = ensureExportDirectory({ dataDir: resolvedDir, manifest });
  const safeName = ensureValidFilename(categoryName, "category");
  const timestamp = new Date().toISOString().replace(/[:]/g, "-");
  const zipPath = path.join(exportDir, `${safeName}-${timestamp}.zip`);

  const entries = templates.map((template) => ({
    name: `${ensureValidFilename(template.title, "template.title")}.json`,
    content: JSON.stringify(template, null, 2)
  }));

  if (entries.length === 0) {
    throw new Error("Kategorie enthält keine Templates.");
  }

  const result = await buildZip(zipPath, entries);
  safeLogger.info(`Kategorie exportiert: ${result}`);
  return result;
};

export const exportArchiveZip = async ({ dataDir, logger, manifest }) => {
  const safeLogger = ensureLogger(logger);
  const defaults = resolveTemplatesDefaults(manifest);
  const resolvedDir = ensureDirectoryExists(dataDir ?? defaults.dataDir);
  const data = loadTemplatesData({ dataDir: resolvedDir, logger: safeLogger });
  const exportDir = ensureExportDirectory({ dataDir: resolvedDir, manifest });
  const timestamp = new Date().toISOString().replace(/[:]/g, "-");
  const zipPath = path.join(exportDir, `templates-archive-${timestamp}.zip`);
  const entries = data.templates.map((template) => ({
    name: `${ensureValidFilename(template.title, "template.title")}.json`,
    content: JSON.stringify(template, null, 2)
  }));

  const result = await buildZip(zipPath, entries);
  safeLogger.info(`Archiv exportiert: ${result}`);
  return result;
};

export const createTemplateDraft = ({ title, category, description = "", content, tags = [] }) => {
  const nowIso = new Date().toISOString();
  const template = normalizeTemplate(
    {
      id: crypto.randomUUID(),
      title,
      category,
      description,
      content,
      tags,
      favorite: false,
      usageCount: 0,
      lastUsed: null,
      editable: true,
      created: nowIso,
      updated: nowIso
    },
    nowIso
  );

  return template;
};
