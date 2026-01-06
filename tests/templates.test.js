import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { fileURLToPath } from "node:url";
import {
  computeTemplatesStats,
  exportArchiveZip,
  exportCategoryZip,
  exportTemplateToFile,
  importTemplatesFromFile,
  initializeTemplatesStorage
} from "../src/services/templates.js";
import { createLogger } from "../src/core/logger.js";

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

test("exportCategoryZip creates zip in export folder", async () => {
  const tempDir = createTempDir();
  const seedPath = path.join(__dirname, "fixtures", "templates_seed.json");
  const logger = buildLogger();

  initializeTemplatesStorage({ dataDir: tempDir, seedPath, logger });

  const zipPath = await exportCategoryZip({ dataDir: tempDir, category: "Test", logger });

  assert.ok(zipPath.includes(`${path.sep}exports${path.sep}`));
  assert.ok(fs.existsSync(zipPath));
  assert.ok(fs.statSync(zipPath).isFile());
});

test("exportArchiveZip creates zip in export folder", async () => {
  const tempDir = createTempDir();
  const seedPath = path.join(__dirname, "fixtures", "templates_seed.json");
  const logger = buildLogger();

  initializeTemplatesStorage({ dataDir: tempDir, seedPath, logger });

  const zipPath = await exportArchiveZip({ dataDir: tempDir, logger });

  assert.ok(zipPath.includes(`${path.sep}exports${path.sep}`));
  assert.ok(fs.existsSync(zipPath));
  assert.ok(fs.statSync(zipPath).isFile());
});

test("importTemplatesFromFile skips duplicates and resolves title collisions", () => {
  const tempDir = createTempDir();
  const seedPath = path.join(__dirname, "fixtures", "templates_seed.json");
  const logger = buildLogger();

  initializeTemplatesStorage({ dataDir: tempDir, seedPath, logger });

  const importPath = path.join(tempDir, "incoming.json");
  const incoming = {
    templates: [
      {
        id: "dup",
        title: "Test Template",
        category: "Test",
        description: "Beschreibung",
        content: "Inhalt",
        favorite: false,
        usageCount: 0,
        lastUsed: null,
        editable: true
      },
      {
        id: "collision",
        title: "Test Template",
        category: "Test",
        description: "Andere Beschreibung",
        content: "Neuer Inhalt",
        favorite: false,
        usageCount: 0,
        lastUsed: null,
        editable: true
      }
    ]
  };
  fs.writeFileSync(importPath, JSON.stringify(incoming, null, 2));

  const merged = importTemplatesFromFile({ dataDir: tempDir, filePath: importPath, logger });

  assert.equal(merged.templates.length, 2);
  assert.ok(merged.templates.some((template) => template.title === "Test Template"));
  assert.ok(merged.templates.some((template) => template.title === "Test Template (2)"));
});

test("importTemplatesFromFile throws when file is missing", () => {
  const tempDir = createTempDir();
  const logger = buildLogger();

  assert.throws(() =>
    importTemplatesFromFile({ dataDir: tempDir, filePath: "missing.json", logger })
  );
});
