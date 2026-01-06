import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { execFileSync } from "node:child_process";

const createTempLogPath = () => {
  const logDir = fs.mkdtempSync(path.join(os.tmpdir(), "bootstrap-log-"));
  return path.join(logDir, "bootstrap.log");
};

test("bootstrap script writes accessible logs in dry-run", () => {
  const logPath = createTempLogPath();

  const output = execFileSync("bash", ["scripts/start.sh"], {
    env: {
      ...process.env,
      BOOTSTRAP_DRY_RUN: "1",
      BOOTSTRAP_SKIP_QUALITY: "1",
      BOOTSTRAP_SKIP_START: "1",
      BOOTSTRAP_THEME: "none",
      BOOTSTRAP_LOG_PATH: logPath
    },
    encoding: "utf-8"
  });

  assert.ok(fs.existsSync(logPath));
  const logContent = fs.readFileSync(logPath, "utf-8");

  assert.match(output, /\[INFO\]/);
  assert.match(output, /Bootstrap-Check startet/);
  assert.match(logContent, /Bootstrap-Check startet/);
  assert.match(logContent, /Logs liegen unter/);
});
