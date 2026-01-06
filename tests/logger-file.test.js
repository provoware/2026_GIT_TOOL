import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { createLogger } from "../src/utils/logger.js";

const withConsoleSpy = async (fn) => {
  const original = console.log;
  const calls = [];
  console.log = (...args) => calls.push(args);

  try {
    await fn(calls);
  } finally {
    console.log = original;
  }
};

const withTempDir = (fn) => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "git-tool-logs-"));
  try {
    return fn(dir);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
};

test("createLogger writes logs to file when enabled", async () => {
  await withConsoleSpy(() =>
    withTempDir((dir) => {
      const logFilePath = path.join(dir, "app.log");
      const logger = createLogger({
        debugEnabled: false,
        loggingEnabled: true,
        logToFile: true,
        logLevel: "INFO",
        logFilePath,
        logRotateDaily: false,
        logMaxSizeBytes: 1024
      });

      const entry = logger.info("Datei-Log aktiv");
      const content = fs.readFileSync(logFilePath, "utf8");

      assert.match(content, /Datei-Log aktiv/);
      assert.equal(entry.delivered, true);
    })
  );
});

test("createLogger rotates log file when size limit is reached", async () => {
  await withConsoleSpy(() =>
    withTempDir((dir) => {
      const logFilePath = path.join(dir, "app.log");
      fs.writeFileSync(logFilePath, "x".repeat(2048));

      const logger = createLogger({
        debugEnabled: false,
        loggingEnabled: true,
        logToFile: true,
        logLevel: "INFO",
        logFilePath,
        logRotateDaily: false,
        logMaxSizeBytes: 10
      });

      logger.info("Rotation aktiv");

      const files = fs.readdirSync(dir);
      const rotated = files.find((file) => file.startsWith("app-"));
      const currentContent = fs.readFileSync(logFilePath, "utf8");

      assert.ok(rotated, "Rotation file should exist");
      assert.match(currentContent, /Rotation aktiv/);
    })
  );
});
