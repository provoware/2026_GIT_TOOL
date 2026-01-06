import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import {
  buildQualityPlan,
  buildQualityRunResult,
  loadQualityConfig,
  loadQualityManifest
} from "../src/utils/quality.js";

const createTempDir = () => fs.mkdtempSync(path.join(os.tmpdir(), "quality-test-"));

const writeJson = (filePath, payload) => {
  fs.writeFileSync(filePath, JSON.stringify(payload, null, 2));
  return fs.existsSync(filePath);
};

test("quality manifest and config build a runnable plan", () => {
  const tempDir = createTempDir();
  const manifestPath = path.join(tempDir, "quality.manifest.json");
  const configPath = path.join(tempDir, "quality.config.json");

  const manifestWritten = writeJson(manifestPath, {
    version: "1.0",
    description: "Test-Manifest",
    steps: [
      {
        id: "lint",
        label: "Linting (Stilprüfung)",
        description: "Prüft Stilregeln.",
        command: "npm run lint",
        fixCommand: "npm run lint:fix",
        required: true
      }
    ]
  });
  const configWritten = writeJson(configPath, {
    autoFix: true,
    stopOnFailure: true,
    stepsEnabled: ["lint"],
    printSummary: true
  });

  assert.equal(manifestWritten, true);
  assert.equal(configWritten, true);

  const manifest = loadQualityManifest({ manifestPath });
  const config = loadQualityConfig({ configPath });
  const plan = buildQualityPlan({ manifest, config });

  assert.equal(plan.steps.length, 1);
  assert.equal(plan.steps[0].id, "lint");
  assert.equal(plan.steps[0].shouldFix, true);
  assert.equal(plan.stopOnFailure, true);
});

test("quality run result validates output", () => {
  const result = buildQualityRunResult({
    ok: true,
    steps: [
      {
        id: "lint",
        label: "Linting (Stilprüfung)",
        status: "ok",
        message: "Prüfung erfolgreich."
      }
    ]
  });

  assert.equal(result.ok, true);
  assert.equal(result.steps.length, 1);
  assert.equal(result.steps[0].status, "ok");
});

test("required quality steps are always included", () => {
  const plan = buildQualityPlan({
    manifest: {
      steps: [
        {
          id: "lint",
          label: "Linting (Stilprüfung)",
          description: "Pflichtschritt.",
          command: "npm run lint",
          required: true
        },
        {
          id: "optional",
          label: "Optional",
          description: "Optionaler Schritt.",
          command: "echo optional",
          required: false
        }
      ]
    },
    config: {
      autoFix: false,
      stopOnFailure: true,
      stepsEnabled: ["optional"],
      printSummary: true
    }
  });

  const stepIds = plan.steps.map((step) => step.id);
  assert.deepEqual(stepIds, ["lint", "optional"]);
});
