import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { createLogger } from "../src/utils/logger.js";
import { runStartupRoutine } from "../src/utils/startup.js";

const createTempRoot = () => fs.mkdtempSync(path.join(os.tmpdir(), "startup-test-"));

const fileExists = (filePath) => fs.existsSync(filePath);

const directoryExists = (dirPath) =>
  fileExists(dirPath) && fs.statSync(dirPath).isDirectory();

test("startup routine creates required structure and reports status", () => {
  const appRoot = createTempRoot();
  const logger = createLogger({ debugEnabled: false, loggingEnabled: false });
  const statuses = [];

  const result = runStartupRoutine({
    appRoot,
    logger,
    reportStatus: (payload) => statuses.push(payload)
  });

  const configPath = path.join(appRoot, "config", "user", "app.config.json");
  const dataDir = path.join(appRoot, "data");
  const pluginsDir = path.join(appRoot, "plugins");

  assert.equal(result.ok, true);
  assert.equal(result.configPath, configPath);
  assert.equal(result.dataDir, dataDir);
  assert.equal(result.pluginsDir, pluginsDir);

  assert.ok(directoryExists(path.join(appRoot, "config", "system")));
  assert.ok(directoryExists(path.join(appRoot, "config", "user")));
  assert.ok(directoryExists(dataDir));
  assert.ok(directoryExists(pluginsDir));
  assert.ok(directoryExists(path.join(dataDir, "exports")));

  assert.ok(fileExists(configPath));
  assert.ok(fileExists(path.join(dataDir, "templates_seed.json")));
  assert.ok(fileExists(path.join(dataDir, "templates.json")));
  assert.ok(fileExists(path.join(dataDir, "templates_stats.json")));
  assert.ok(fileExists(path.join(dataDir, "templates_stats_schema.json")));
  assert.ok(fileExists(path.join(appRoot, "config", "system", "standards.manifest.json")));

  const config = JSON.parse(fs.readFileSync(configPath, "utf-8"));
  assert.ok(config.availableThemes.includes("theme-high-contrast-forest"));
  assert.ok(config.availableThemes.includes("theme-high-contrast-violet"));

  assert.ok(statuses.length > 0);
  statuses.forEach((status) => {
    assert.equal(typeof status.message, "string");
    assert.equal(typeof status.level, "string");
  });
});
