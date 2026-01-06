import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { fileURLToPath } from "node:url";
import {
  computeTemplatesStats,
  exportTemplateToFile,
  initializeTemplatesStorage
} from "../src/utils/templates.js";
import { createLogger } from "../src/utils/logger.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const createTempDir = () => fs.mkdtempSync(path.join(os.tmpdir(), "templates-test-"));

const buildLogger = () =>
  createLogger({
    debugEnabled: false,
    loggingEnabled: false
  });

test("initializeTemplatesStorage creates templates and stats", () => {
  const tempDir = createTempDir();
  const seedPath = path.join(__dirname, "fixtures", "templates_seed.json");
  const logger = buildLogger();

  const result = initializeTemplatesStorage({ dataDir: tempDir, seedPath, logger });

  assert.ok(fs.existsSync(path.join(tempDir, "templates.json")));
  assert.ok(fs.existsSync(path.join(tempDir, "templates_stats.json")));
  assert.ok(result.templatesCount > 0);
});

test("computeTemplatesStats returns expected totals", () => {
  const stats = computeTemplatesStats([
    {
      id: "1",
      title: "A",
      category: "Test",
      description: "desc",
      content: "content",
      favorite: true,
      usageCount: 2,
      lastUsed: null,
      created: new Date().toISOString(),
      updated: new Date().toISOString(),
      tags: [],
      editable: true
    },
    {
      id: "2",
      title: "B",
      category: "Test",
      description: "desc",
      content: "content",
      favorite: false,
      usageCount: 0,
      lastUsed: null,
      created: new Date().toISOString(),
      updated: new Date().toISOString(),
      tags: [],
      editable: true
    }
  ]);

  assert.equal(stats.totals.templatesCount, 2);
  assert.equal(stats.totals.favoritesCount, 1);
  assert.equal(stats.totals.usageTotal, 2);
});

test("exportTemplateToFile rejects invalid filenames", () => {
  const tempDir = createTempDir();
  const logger = buildLogger();
  const template = {
    id: "bad",
    title: "../illegal",
    category: "Test",
    description: "desc",
    content: "content",
    favorite: false,
    usageCount: 0,
    lastUsed: null,
    created: new Date().toISOString(),
    updated: new Date().toISOString(),
    tags: [],
    editable: true
  };

  assert.throws(() =>
    exportTemplateToFile({ dataDir: tempDir, template, format: "txt", logger })
  );
});
