import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { fileURLToPath } from "node:url";
import { createLogger } from "../src/core/logger.js";
import { initializeTemplatesStorage } from "../src/services/templates.js";
import { registerTemplatesIpcHandlers } from "../src/ipc/templatesIpc.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const createTempDir = () => fs.mkdtempSync(path.join(os.tmpdir(), "ipc-test-"));

const buildLogger = () =>
  createLogger({
    debugEnabled: false,
    loggingEnabled: false
  });

const createMockIpcMain = () => {
  const handlers = new Map();
  return {
    handlers,
    handle: (channel, handler) => handlers.set(channel, handler)
  };
};

test("registerTemplatesIpcHandlers rejects invalid options", () => {
  assert.throws(() => registerTemplatesIpcHandlers({}));
});

test("registerTemplatesIpcHandlers wires load/save handlers with mock ipcMain", async () => {
  const tempDir = createTempDir();
  const seedPath = path.join(__dirname, "fixtures", "templates_seed.json");
  const logger = buildLogger();
  const ipcMain = createMockIpcMain();
  const dialog = {
    showOpenDialog: async () => ({ canceled: true, filePaths: [] })
  };

  initializeTemplatesStorage({ dataDir: tempDir, seedPath, logger });

  registerTemplatesIpcHandlers({ dataDir: tempDir, logger, ipcMain, dialog });

  const loadHandler = ipcMain.handlers.get("templates:load");
  const saveHandler = ipcMain.handlers.get("templates:save");

  const loadResult = await loadHandler();
  assert.ok(loadResult.payload.templates.length > 0);
  assert.equal(loadResult.stats.totals.templatesCount, loadResult.payload.templates.length);

  const saveResult = await saveHandler(null, loadResult.payload);
  assert.ok(saveResult.payload.templates.length > 0);
  assert.equal(saveResult.stats.totals.templatesCount, saveResult.payload.templates.length);
});

test("templates:import returns merged payload when dialog provides file", async () => {
  const tempDir = createTempDir();
  const seedPath = path.join(__dirname, "fixtures", "templates_seed.json");
  const logger = buildLogger();
  const ipcMain = createMockIpcMain();
  const importPath = path.join(tempDir, "incoming.json");
  const incoming = {
    templates: [
      {
        id: "imported",
        title: "Neues Template",
        category: "Test",
        description: "Beschreibung",
        content: "Inhalt",
        favorite: false,
        usageCount: 0,
        lastUsed: null,
        editable: true
      }
    ]
  };
  fs.writeFileSync(importPath, JSON.stringify(incoming, null, 2));

  const dialog = {
    showOpenDialog: async () => ({ canceled: false, filePaths: [importPath] })
  };

  initializeTemplatesStorage({ dataDir: tempDir, seedPath, logger });

  registerTemplatesIpcHandlers({ dataDir: tempDir, logger, ipcMain, dialog });

  const importHandler = ipcMain.handlers.get("templates:import");
  const result = await importHandler();

  assert.ok(result);
  assert.ok(result.payload.templates.some((template) => template.title === "Neues Template"));
});
