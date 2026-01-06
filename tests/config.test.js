import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { loadConfig } from "../src/utils/config.js";

const writeTempConfig = (config) => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "git-tool-config-"));
  const filePath = path.join(dir, "app.config.json");
  fs.writeFileSync(filePath, JSON.stringify(config, null, 2));
  return filePath;
};

test("loadConfig loads and validates configuration", () => {
  const configPath = writeTempConfig({
    appName: "Test Tool",
    debugEnabled: false,
    loggingEnabled: true,
    logToFile: true,
    logLevel: "INFO",
    logFilePath: "data/logs/test.log",
    logRotateDaily: false,
    logMaxSizeBytes: 1024,
    theme: "theme-high-contrast-dark",
    availableThemes: ["theme-high-contrast-dark", "theme-high-contrast-light"]
  });

  const config = loadConfig({ configPath });

  assert.equal(config.appName, "Test Tool");
  assert.equal(config.debugEnabled, false);
  assert.equal(config.loggingEnabled, true);
  assert.equal(config.logToFile, true);
  assert.equal(config.logLevel, "INFO");
  assert.equal(config.theme, "theme-high-contrast-dark");
});

test("loadConfig rejects invalid theme", () => {
  const configPath = writeTempConfig({
    appName: "Test Tool",
    debugEnabled: true,
    loggingEnabled: true,
    logToFile: false,
    logLevel: "INFO",
    logFilePath: "data/logs/test.log",
    logRotateDaily: true,
    logMaxSizeBytes: 2048,
    theme: "invalid",
    availableThemes: ["theme-high-contrast-dark"]
  });

  assert.throws(() => loadConfig({ configPath }), /theme ist ungültig/);
});
