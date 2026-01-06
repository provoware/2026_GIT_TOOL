import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { loadModules, sortModulesByDependencies } from "../src/services/moduleLoader.js";

const createTempDir = () => fs.mkdtempSync(path.join(os.tmpdir(), "git-tool-modules-"));

const writeModuleFile = (dir, fileName, contents) => {
  const filePath = path.join(dir, fileName);
  fs.writeFileSync(filePath, contents);
  return filePath;
};

const writeManifest = (dir, manifest) => {
  const manifestPath = path.join(dir, "modules.manifest.json");
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
  return manifestPath;
};

const createLogger = () => {
  const messages = {
    info: [],
    warn: [],
    error: [],
    debug: []
  };

  return {
    messages,
    info: (message) => messages.info.push(message),
    warn: (message) => messages.warn.push(message),
    error: (message) => messages.error.push(message),
    debug: (message) => messages.debug.push(message)
  };
};

test("sortModulesByDependencies orders by dependency graph", () => {
  const modules = [
    { id: "core", dependencies: [] },
    { id: "feature", dependencies: ["core"] },
    { id: "addon", dependencies: ["feature"] }
  ];

  const sorted = sortModulesByDependencies(modules);
  assert.deepEqual(
    sorted.map((moduleRecord) => moduleRecord.id),
    ["core", "feature", "addon"]
  );
});

test("loadModules loads modules in dependency order", async () => {
  const tempDir = createTempDir();
  const modulesDir = path.join(tempDir, "modules");
  fs.mkdirSync(modulesDir);

  writeModuleFile(
    modulesDir,
    "core.js",
    [
      "export const manifest = { id: 'core', name: 'Core', version: '1.0.0' };",
      "export const activate = () => ({ status: 'aktiv', message: 'Core ok.' });"
    ].join("\n")
  );

  writeModuleFile(
    modulesDir,
    "feature.js",
    [
      "export const manifest = { id: 'feature', name: 'Feature', version: '1.0.0' };",
      "export const activate = () => ({ status: 'aktiv', message: 'Feature ok.' });"
    ].join("\n")
  );

  const manifestPath = writeManifest(tempDir, {
    manifestVersion: "1.0",
    modules: [
      {
        id: "feature",
        name: "Feature",
        version: "1.0.0",
        entry: "modules/feature.js",
        dependencies: ["core"]
      },
      {
        id: "core",
        name: "Core",
        version: "1.0.0",
        entry: "modules/core.js",
        dependencies: []
      }
    ]
  });

  const logger = createLogger();
  const results = await loadModules({
    manifestPath,
    appRoot: tempDir,
    logger,
    context: { logger, appName: "Test App" }
  });

  assert.deepEqual(
    results.map((result) => result.id),
    ["core", "feature"]
  );
  assert.equal(results[0].status, "aktiv");
});
