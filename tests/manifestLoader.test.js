import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { loadManifest } from "../src/utils/manifestLoader.js";

const writeTempManifest = (manifest) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "manifest-test-"));
  const configDir = path.join(root, "config");
  fs.mkdirSync(configDir, { recursive: true });
  const filePath = path.join(configDir, "manifest.json");
  fs.writeFileSync(filePath, JSON.stringify(manifest, null, 2));
  return { root, filePath };
};

test("loadManifest loads and normalizes manifest", () => {
  const { root, filePath } = writeTempManifest({
    version: "1.0",
    app: {
      name: "Test App",
      description: "Test defaults"
    },
    logging: {
      levels: ["DEBUG", "INFO"],
      defaultLevel: "INFO",
      defaultLogFilePath: "data/logs/app.log",
      defaultRotateDaily: true,
      defaultMaxSizeBytes: 1024,
      defaultLoggingEnabled: true,
      defaultDebugEnabled: false,
      defaultLogToFile: true
    },
    themes: {
      available: ["theme-a", "theme-b"],
      default: "theme-a"
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
      defaultCategories: ["A", "B"]
    }
  });

  const manifest = loadManifest({ appRoot: root, manifestPath: filePath });

  assert.equal(manifest.app.name, "Test App");
  assert.equal(manifest.logging.defaultLevel, "INFO");
  assert.equal(manifest.paths.dataDir, path.join(root, "data"));
  assert.equal(manifest.paths.exportsDir, path.join(root, "data", "exports"));
  assert.deepEqual(manifest.exportRules.allowedFormats, ["txt", "json"]);
});

test("loadManifest rejects invalid manifest schema", () => {
  const { root, filePath } = writeTempManifest({
    version: "1.0",
    app: { name: "Broken" },
    logging: {
      levels: [],
      defaultLevel: "INFO",
      defaultLogFilePath: "data/logs/app.log",
      defaultRotateDaily: true,
      defaultMaxSizeBytes: 1024,
      defaultLoggingEnabled: true,
      defaultDebugEnabled: false,
      defaultLogToFile: true
    },
    themes: {
      available: ["theme-a"],
      default: "theme-a"
    },
    exportRules: {
      allowedFormats: ["txt"],
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
      defaultCategories: ["A"]
    }
  });

  assert.throws(
    () => loadManifest({ appRoot: root, manifestPath: filePath }),
    /logging\.levels muss eine Liste mit Werten sein/
  );
});
