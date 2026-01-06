import { app, BrowserWindow, dialog, ipcMain } from "electron";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createLogger } from "./utils/logger.js";
import { loadConfig } from "./utils/config.js";
import { createSafeHandle } from "./utils/ipcSafe.js";
import {
  computeTemplatesStats,
  exportArchiveZip,
  exportCategoryZip,
  exportTemplateToFile,
  importTemplatesFromFile,
  initializeTemplatesStorage,
  loadTemplatesData,
  saveTemplatesData
} from "./utils/templates.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const dataDir = path.resolve(__dirname, "..", "data");

const createWindow = (logger) => {
  const mainWindow = new BrowserWindow({
    width: 1100,
    height: 720,
    backgroundColor: "#0b0d11",
    webPreferences: {
      contextIsolation: true,
      preload: path.join(__dirname, "preload.js")
    }
  });

  const rendererPath = path.join(__dirname, "renderer", "index.html");
  mainWindow.loadFile(rendererPath);
  logger.info("Fenster gestartet.");
};

app.whenReady().then(() => {
  const config = loadConfig();
  const logger = createLogger(config);
  const safeHandle = createSafeHandle({ ipcMain, logger });

  logger.info(`${config.appName} startet.`);
  logger.debug(`Aktives Theme: ${config.theme}`);

  initializeTemplatesStorage({ dataDir, logger });
  createWindow(logger);

  safeHandle("templates:load", () => {
    const payload = loadTemplatesData({ dataDir, logger });
    const stats = computeTemplatesStats(payload.templates);
    return { payload, stats };
  });

  safeHandle("templates:save", (_event, payload) => {
    const saved = saveTemplatesData({ dataDir, payload, logger });
    const stats = computeTemplatesStats(saved.templates);
    return { payload: saved, stats };
  });

  safeHandle("templates:export", (_event, { template, format }) =>
    exportTemplateToFile({ dataDir, template, format, logger })
  );

  safeHandle("templates:exportCategory", (_event, { category }) =>
    exportCategoryZip({ dataDir, category, logger })
  );

  safeHandle("templates:exportArchive", () => exportArchiveZip({ dataDir, logger }));

  safeHandle("templates:import", async () => {
    const result = await dialog.showOpenDialog({
      title: "Template-Import",
      properties: ["openFile"],
      filters: [{ name: "JSON", extensions: ["json"] }]
    });

    if (result.canceled || result.filePaths.length === 0) {
      return null;
    }

    const merged = importTemplatesFromFile({
      dataDir,
      filePath: result.filePaths[0],
      logger
    });
    const stats = computeTemplatesStats(merged.templates);
    return { payload: merged, stats };
  });

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow(logger);
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});
