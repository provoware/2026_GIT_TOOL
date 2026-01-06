import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import {
  ensureArrayOfStrings,
  ensureNonEmptyString,
  ensurePlainObject
} from "../core/validation.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const defaultManifestPath = path.resolve(
  __dirname,
  "..",
  "..",
  "config",
  "system",
  "modules.manifest.json"
);

const ensureLogger = (logger, label) => {
  const candidate = ensurePlainObject(logger, label);
  const requiredMethods = ["info", "warn", "error", "debug"];

  requiredMethods.forEach((method) => {
    if (typeof candidate[method] !== "function") {
      throw new Error(`${label}.${method} muss eine Funktion sein.`);
    }
  });

  return candidate;
};

const normalizeModuleRecord = (record, index) => {
  const candidate = ensurePlainObject(record, `modules[${index}]`);
  const id = ensureNonEmptyString(candidate.id, `modules[${index}].id`);
  const name = ensureNonEmptyString(candidate.name, `modules[${index}].name`);
  const version = ensureNonEmptyString(candidate.version, `modules[${index}].version`);
  const entry = ensureNonEmptyString(candidate.entry, `modules[${index}].entry`);
  const dependencies = ensureArrayOfStrings(
    candidate.dependencies ?? [],
    `modules[${index}].dependencies`
  );

  return {
    id,
    name,
    version,
    entry,
    dependencies
  };
};

export const readModulesManifest = (options = {}) => {
  const normalizedOptions =
    options === undefined ? {} : ensurePlainObject(options, "options");
  const { manifestPath = defaultManifestPath, logger } = normalizedOptions;
  const resolvedManifestPath = ensureNonEmptyString(manifestPath, "manifestPath");

  if (!fs.existsSync(resolvedManifestPath)) {
    throw new Error("Modul-Manifest fehlt.");
  }

  const raw = fs.readFileSync(resolvedManifestPath, "utf-8");
  const parsed = JSON.parse(raw);
  const manifest = ensurePlainObject(parsed, "manifest");
  const manifestVersion = ensureNonEmptyString(
    manifest.manifestVersion,
    "manifest.manifestVersion"
  );

  const modulesRaw = manifest.modules;
  if (!Array.isArray(modulesRaw)) {
    throw new Error("manifest.modules muss eine Liste sein.");
  }

  const modules = modulesRaw.map(normalizeModuleRecord);
  const seenIds = new Set();
  modules.forEach((moduleRecord) => {
    if (seenIds.has(moduleRecord.id)) {
      throw new Error(`Doppelte Modul-ID: ${moduleRecord.id}`);
    }
    seenIds.add(moduleRecord.id);
  });

  if (logger) {
    const normalizedLogger = ensureLogger(logger, "logger");
    normalizedLogger.debug(
      `Modul-Manifest ${manifestVersion} geladen (${modules.length} Einträge).`
    );
  }

  return {
    manifestVersion,
    modules
  };
};

export const sortModulesByDependencies = (modules) => {
  if (!Array.isArray(modules)) {
    throw new Error("modules muss eine Liste sein.");
  }

  const indexById = new Map();
  modules.forEach((moduleRecord, index) => {
    indexById.set(moduleRecord.id, index);
  });

  const dependencyMap = new Map();
  const inDegree = new Map();

  modules.forEach((moduleRecord) => {
    const deps = ensureArrayOfStrings(
      moduleRecord.dependencies ?? [],
      `modules.${moduleRecord.id}.dependencies`
    );
    dependencyMap.set(moduleRecord.id, deps);
    inDegree.set(moduleRecord.id, 0);
  });

  dependencyMap.forEach((deps, moduleId) => {
    deps.forEach((depId) => {
      if (!indexById.has(depId)) {
        throw new Error(`Abhängigkeit fehlt: ${moduleId} -> ${depId}`);
      }
      inDegree.set(moduleId, (inDegree.get(moduleId) ?? 0) + 1);
    });
  });

  const queue = modules
    .filter((moduleRecord) => (inDegree.get(moduleRecord.id) ?? 0) === 0)
    .map((moduleRecord) => moduleRecord.id)
    .sort((a, b) => (indexById.get(a) ?? 0) - (indexById.get(b) ?? 0));

  const sorted = [];

  while (queue.length > 0) {
    const currentId = queue.shift();
    const currentModule = modules[indexById.get(currentId)];
    sorted.push(currentModule);

    dependencyMap.forEach((deps, moduleId) => {
      if (!deps.includes(currentId)) {
        return;
      }

      const nextDegree = (inDegree.get(moduleId) ?? 0) - 1;
      inDegree.set(moduleId, nextDegree);
      if (nextDegree === 0) {
        queue.push(moduleId);
        queue.sort((a, b) => (indexById.get(a) ?? 0) - (indexById.get(b) ?? 0));
      }
    });
  }

  if (sorted.length !== modules.length) {
    throw new Error("Zyklische Modul-Abhängigkeiten erkannt.");
  }

  return sorted;
};

const validateModuleInterface = (moduleRecord, loadedModule) => {
  const candidate = ensurePlainObject(loadedModule, `module:${moduleRecord.id}`);
  const manifest = ensurePlainObject(
    candidate.manifest,
    `module:${moduleRecord.id}.manifest`
  );

  const manifestId = ensureNonEmptyString(
    manifest.id,
    `module:${moduleRecord.id}.manifest.id`
  );
  const name = ensureNonEmptyString(
    manifest.name,
    `module:${moduleRecord.id}.manifest.name`
  );
  const version = ensureNonEmptyString(
    manifest.version,
    `module:${moduleRecord.id}.manifest.version`
  );

  if (manifestId !== moduleRecord.id) {
    throw new Error(`Manifest-ID stimmt nicht: ${moduleRecord.id}`);
  }

  if (typeof candidate.activate !== "function") {
    throw new Error(`module:${moduleRecord.id}.activate fehlt.`);
  }

  if (candidate.deactivate && typeof candidate.deactivate !== "function") {
    throw new Error(`module:${moduleRecord.id}.deactivate ist ungültig.`);
  }

  return {
    id: manifestId,
    name,
    version,
    activate: candidate.activate,
    deactivate: candidate.deactivate ?? null
  };
};

const ensureLoadResult = (result) => {
  const candidate = ensurePlainObject(result, "moduleLoadResult");
  const id = ensureNonEmptyString(candidate.id, "moduleLoadResult.id");
  const status = ensureNonEmptyString(candidate.status, "moduleLoadResult.status");
  const message = ensureNonEmptyString(candidate.message, "moduleLoadResult.message");

  return {
    id,
    status,
    message
  };
};

export const loadModules = async (options = {}) => {
  const normalizedOptions =
    options === undefined ? {} : ensurePlainObject(options, "options");
  const {
    manifestPath = defaultManifestPath,
    appRoot = path.resolve(__dirname, "..", ".."),
    logger,
    context = {}
  } = normalizedOptions;

  const normalizedLogger = ensureLogger(logger, "logger");
  const normalizedContext = ensurePlainObject(context, "context");

  const manifest = readModulesManifest({ manifestPath, logger: normalizedLogger });
  const sortedModules = sortModulesByDependencies(manifest.modules);
  const results = [];

  normalizedLogger.info(
    `Module werden geladen (${sortedModules.length} Einträge).`
  );

  for (const moduleRecord of sortedModules) {
    const entryPath = path.resolve(appRoot, moduleRecord.entry);

    if (!fs.existsSync(entryPath)) {
      const result = ensureLoadResult({
        id: moduleRecord.id,
        status: "fehlgeschlagen",
        message: `Entry fehlt: ${moduleRecord.entry}`
      });
      normalizedLogger.error(result.message);
      results.push(result);
      continue;
    }

    const importResult = await import(pathToFileURL(entryPath).href)
      .then((moduleValue) => ({ moduleValue }))
      .catch((error) => ({ error }));

    if (importResult.error) {
      const result = ensureLoadResult({
        id: moduleRecord.id,
        status: "fehlgeschlagen",
        message: `Import fehlgeschlagen: ${importResult.error.message}`
      });
      normalizedLogger.error(result.message);
      results.push(result);
      continue;
    }

    try {
      const moduleInterface = validateModuleInterface(
        moduleRecord,
        importResult.moduleValue
      );
      const activationResult = await Promise.resolve(
        moduleInterface.activate(normalizedContext)
      );
      const normalizedActivation = ensurePlainObject(
        activationResult,
        `module:${moduleRecord.id}.activationResult`
      );

      const result = ensureLoadResult({
        id: moduleInterface.id,
        status: ensureNonEmptyString(
          normalizedActivation.status ?? "aktiv",
          `module:${moduleRecord.id}.activationResult.status`
        ),
        message: ensureNonEmptyString(
          normalizedActivation.message ?? "Modul aktiviert.",
          `module:${moduleRecord.id}.activationResult.message`
        )
      });

      normalizedLogger.info(`${moduleInterface.name}: ${result.message}`);
      results.push(result);
    } catch (error) {
      const result = ensureLoadResult({
        id: moduleRecord.id,
        status: "fehlgeschlagen",
        message: `Modulfehler: ${error.message}`
      });
      normalizedLogger.error(result.message);
      results.push(result);
    }
  }

  normalizedLogger.debug(
    `Module geladen: ${results.filter((result) => result.status !== "fehlgeschlagen").length}/${
      results.length
    } erfolgreich.`
  );

  return results.map(ensureLoadResult);
};
