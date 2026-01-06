import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  ensureArrayOfStrings,
  ensureBoolean,
  ensureNonEmptyString,
  ensurePlainObject
} from "./validation.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const defaultManifestPath = path.resolve(
  __dirname,
  "..",
  "..",
  "config",
  "system",
  "quality.manifest.json"
);
const defaultConfigPath = path.resolve(
  __dirname,
  "..",
  "..",
  "config",
  "user",
  "quality.config.json"
);

const ensureOptionalArrayOfStrings = (value, label) => {
  if (value === undefined || value === null) {
    return [];
  }
  return ensureArrayOfStrings(value, label);
};

const ensureOptionalString = (value, label) => {
  if (value === undefined || value === null || value === "") {
    return null;
  }
  return ensureNonEmptyString(value, label);
};

const ensureJsonFile = (filePath, label) => {
  const resolvedPath = ensureNonEmptyString(filePath, "filePath");
  if (!fs.existsSync(resolvedPath)) {
    throw new Error(`${label} fehlt.`);
  }
  const raw = fs.readFileSync(resolvedPath, "utf-8");
  const parsed = JSON.parse(raw);
  return ensurePlainObject(parsed, label);
};

const normalizeQualityStep = (step, index) => {
  const normalizedStep = ensurePlainObject(step, `step[${index}]`);
  const id = ensureNonEmptyString(normalizedStep.id, `step[${index}].id`);
  const label = ensureNonEmptyString(normalizedStep.label, `step[${index}].label`);
  const description = ensureNonEmptyString(
    normalizedStep.description,
    `step[${index}].description`
  );
  const command = ensureNonEmptyString(
    normalizedStep.command,
    `step[${index}].command`
  );
  const fixCommand = ensureOptionalString(
    normalizedStep.fixCommand,
    `step[${index}].fixCommand`
  );
  const required = ensureBoolean(
    normalizedStep.required ?? true,
    `step[${index}].required`
  );

  return {
    id,
    label,
    description,
    command,
    fixCommand,
    required
  };
};

export const buildDefaultQualityManifest = () => ({
  version: "1.0",
  description: "Automatische Code-Qualitätsprüfung und Auto-Formatierung.",
  steps: [
    {
      id: "lint",
      label: "Linting (Stilprüfung)",
      description: "Prüft Regeln für sauberen, einheitlichen Code.",
      command: "npm run lint",
      fixCommand: "npm run lint:fix",
      required: true
    },
    {
      id: "format",
      label: "Formatierung (Code-Format)",
      description: "Prüft und formatiert Code mit Prettier.",
      command: "npm run format",
      fixCommand: "npm run format:write",
      required: true
    },
    {
      id: "test",
      label: "Tests (Automatische Prüfungen)",
      description: "Führt automatische Tests aus, um Fehler zu finden.",
      command: "npm test",
      required: true
    }
  ]
});

export const buildDefaultQualityConfig = () => ({
  autoFix: true,
  stopOnFailure: true,
  stepsEnabled: ["lint", "format", "test"],
  printSummary: true
});

export const loadQualityManifest = (options = {}) => {
  const normalizedOptions =
    options === undefined ? {} : ensurePlainObject(options, "options");
  const manifestPath = ensureNonEmptyString(
    normalizedOptions.manifestPath ?? defaultManifestPath,
    "manifestPath"
  );
  const rawManifest = ensureJsonFile(manifestPath, "qualityManifest");
  const version = ensureNonEmptyString(rawManifest.version, "version");
  const description = ensureNonEmptyString(rawManifest.description, "description");

  if (!Array.isArray(rawManifest.steps) || rawManifest.steps.length === 0) {
    throw new Error("steps muss eine Liste mit Einträgen sein.");
  }

  const steps = rawManifest.steps.map((step, index) =>
    normalizeQualityStep(step, index)
  );

  return {
    version,
    description,
    steps,
    manifestPath
  };
};

export const loadQualityConfig = (options = {}) => {
  const normalizedOptions =
    options === undefined ? {} : ensurePlainObject(options, "options");
  const configPath = ensureNonEmptyString(
    normalizedOptions.configPath ?? defaultConfigPath,
    "configPath"
  );
  const rawConfig = ensureJsonFile(configPath, "qualityConfig");
  const defaults = buildDefaultQualityConfig();
  const merged = {
    ...defaults,
    ...rawConfig
  };

  const autoFix = ensureBoolean(merged.autoFix, "autoFix");
  const stopOnFailure = ensureBoolean(merged.stopOnFailure, "stopOnFailure");
  const printSummary = ensureBoolean(merged.printSummary, "printSummary");
  const stepsEnabled = ensureOptionalArrayOfStrings(
    merged.stepsEnabled,
    "stepsEnabled"
  );

  return {
    autoFix,
    stopOnFailure,
    printSummary,
    stepsEnabled,
    configPath
  };
};

export const buildQualityPlan = ({ manifest, config }) => {
  const normalizedManifest = ensurePlainObject(manifest, "manifest");
  const normalizedConfig = ensurePlainObject(config, "config");
  const steps = Array.isArray(normalizedManifest.steps)
    ? normalizedManifest.steps.map((step, index) =>
        normalizeQualityStep(step, index)
      )
    : [];

  const stepsEnabled = ensureOptionalArrayOfStrings(
    normalizedConfig.stepsEnabled,
    "stepsEnabled"
  );
  const autoFix = ensureBoolean(normalizedConfig.autoFix, "autoFix");
  const stopOnFailure = ensureBoolean(normalizedConfig.stopOnFailure, "stopOnFailure");
  const printSummary = ensureBoolean(normalizedConfig.printSummary, "printSummary");

  const enabledSteps = stepsEnabled.length
    ? steps.filter((step) => stepsEnabled.includes(step.id))
    : steps;

  const plan = enabledSteps.map((step) => ({
    ...step,
    shouldFix: autoFix && Boolean(step.fixCommand)
  }));

  return {
    steps: plan,
    autoFix,
    stopOnFailure,
    printSummary
  };
};

export const buildQualityRunResult = ({ ok, steps }) => {
  const safeOk = ensureBoolean(ok, "ok");
  if (!Array.isArray(steps)) {
    throw new Error("steps muss eine Liste sein.");
  }
  const normalizedSteps = steps.map((step, index) => {
    const normalizedStep = ensurePlainObject(step, `steps[${index}]`);
    const id = ensureNonEmptyString(normalizedStep.id, `steps[${index}].id`);
    const label = ensureNonEmptyString(
      normalizedStep.label,
      `steps[${index}].label`
    );
    const status = ensureNonEmptyString(
      normalizedStep.status,
      `steps[${index}].status`
    );
    const message = ensureNonEmptyString(
      normalizedStep.message,
      `steps[${index}].message`
    );

    return {
      id,
      label,
      status,
      message
    };
  });

  return {
    ok: safeOk,
    steps: normalizedSteps
  };
};
