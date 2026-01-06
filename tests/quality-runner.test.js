import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { ensureDependencies, runQualityPlan } from "../src/utils/quality-runner.js";

const createLoggerStub = () => ({
  info: () => {},
  warn: () => {},
  error: () => {},
  debug: () => {}
});

const createTempDir = () => fs.mkdtempSync(path.join(os.tmpdir(), "quality-runner-"));

test("runQualityPlan verarbeitet Auto-Fix und Fehlerhinweise", () => {
  const plan = {
    steps: [
      {
        id: "lint",
        label: "Linting (Stilprüfung)",
        description: "Prüft Regeln.",
        command: "npm run lint",
        fixCommand: "npm run lint:fix",
        shouldFix: true
      },
      {
        id: "a11y",
        label: "A11y (Barrierefreiheit)",
        description: "Prüft Barrierefreiheit.",
        command: "npm run test:a11y",
        shouldFix: false
      }
    ],
    stopOnFailure: true
  };

  const queue = [
    {
      command: "npm run lint",
      result: { ok: false, exitCode: 1, status: "failed" }
    },
    {
      command: "npm run lint:fix",
      result: { ok: true, exitCode: 0, status: "ok" }
    },
    {
      command: "npm run lint",
      result: { ok: true, exitCode: 0, status: "ok" }
    },
    {
      command: "npm run test:a11y",
      result: { ok: false, exitCode: 1, status: "failed" }
    }
  ];

  const commandRunner = ({ command }) => {
    const next = queue.shift();
    assert.ok(next, "Es fehlen erwartete Kommandos.");
    assert.equal(command, next.command);
    return next.result;
  };

  const result = runQualityPlan({
    plan,
    logger: createLoggerStub(),
    commandRunner
  });

  assert.equal(result.ok, false);
  assert.equal(result.steps.length, 2);
  assert.equal(result.steps[0].status, "ok");
  assert.equal(result.steps[1].status, "failed");
  assert.ok(result.steps[1].message.includes("Hinweise"));
  assert.equal(queue.length, 0);
});

test("ensureDependencies installiert fehlende Abhängigkeiten automatisch", () => {
  const tempDir = createTempDir();
  const calls = [];
  const commandRunner = ({ command }) => {
    calls.push(command);
    return { ok: true, exitCode: 0, status: "ok" };
  };

  const result = ensureDependencies({
    logger: createLoggerStub(),
    commandRunner,
    projectRoot: tempDir
  });

  assert.equal(result.ok, true);
  assert.equal(calls.length, 1);
  assert.equal(calls[0], "npm install");
});

test("ensureDependencies überspringt Installation bei vorhandenem node_modules", () => {
  const tempDir = createTempDir();
  fs.mkdirSync(path.join(tempDir, "node_modules"));

  const calls = [];
  const commandRunner = ({ command }) => {
    calls.push(command);
    return { ok: true, exitCode: 0, status: "ok" };
  };

  const result = ensureDependencies({
    logger: createLoggerStub(),
    commandRunner,
    projectRoot: tempDir
  });

  assert.equal(result.ok, true);
  assert.equal(calls.length, 0);
});
