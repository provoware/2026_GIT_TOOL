import { app, BrowserWindow, dialog, ipcMain } from "electron";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createLogger } from "./utils/logger.js";
import { loadConfig } from "./utils/config.js";
import { loadModules } from "./utils/moduleLoader.js";
import { initializeTemplatesStorage } from "./utils/templates.js";
import { registerTemplatesIpcHandlers } from "./ipc/templatesIpc.js";
import { createSafeHandle } from "./utils/ipcSafe.js";
import { runStartupRoutine } from "./utils/startup.js";
import {
  ensureBoolean,
  ensurePlainObject
} from "./utils/validation.js";
import {
  computeTemplatesStats,
  exportArchiveZip,
  exportCategoryZip,
  exportTemplateToFile,
  importTemplatesFromFile,
  loadTemplatesData,
  saveTemplatesData
} from "./utils/templates.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const appRoot = path.resolve(__dirname, "..");
const dataDir = path.join(appRoot, "data");

const ensureLogger = (logger) => {
  const target = ensurePlainObject(logger, "logger");
  ["info", "warn", "error", "debug"].forEach((key) => {
    if (typeof target[key] !== "function") {
      throw new Error(`logger.${key} muss eine Funktion sein.`);
    }
  });
  return target;
};

const ensureStatusBuffer = (buffer) => {
  if (!Array.isArray(buffer)) {
    throw new Error("startupStatusBuffer muss eine Liste sein.");
  }
  return buffer;
};

const createWindow = ({ logger, loadRenderer = true, startupStatusBuffer = [] } = {}) => {
  const safeLogger = ensureLogger(logger);
  const shouldLoad = ensureBoolean(loadRenderer, "loadRenderer");
  const safeBuffer = ensureStatusBuffer(startupStatusBuffer);
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
  if (safeBuffer.length > 0) {
    mainWindow.webContents.on("did-finish-load", () => {
      safeBuffer.forEach((payload) => {
        mainWindow.webContents.send("startup:status", payload);
      });
    });
  }

  if (shouldLoad) {
    mainWindow.loadFile(rendererPath);
  }

  safeLogger.info("Fenster gestartet.");
  return mainWindow;
};

app.whenReady().then(async () => {
  const config = loadConfig();
app.whenReady().then(() => {
  const startupStatusBuffer = [];
  let mainWindow = null;
  const bootstrapLogger = createLogger({ debugEnabled: true, loggingEnabled: true });
  const enqueueStatus = (payload) => {
    startupStatusBuffer.push(payload);
    if (mainWindow?.webContents) {
      mainWindow.webContents.send("startup:status", payload);
    }
    return payload;
  };

  const startupResult = runStartupRoutine({
    appRoot,
    dataDir,
    logger: bootstrapLogger,
    reportStatus: enqueueStatus
  });

  const config = loadConfig({ configPath: startupResult.configPath });
  const logger = createLogger(config);
  const safeHandle = createSafeHandle({ ipcMain, logger });

  logger.info(`${config.appName} startet.`);
  logger.debug(`Aktives Theme: ${config.theme}`);

  await loadModules({
    logger,
    context: {
      app,
      appName: config.appName,
      config,
      dataDir,
      logger
    }
  });

  initializeTemplatesStorage({ dataDir, logger });
  createWindow(logger);
  mainWindow = createWindow({
    logger,
    loadRenderer: false,
    startupStatusBuffer
  });
  const rendererPath = path.join(__dirname, "renderer", "index.html");
  mainWindow.loadFile(rendererPath);

  registerTemplatesIpcHandlers({
    dataDir,
    logger,
    ipcMain,
    dialog
  safeHandle("templates:load", () => {
    const payload = loadTemplatesData({ dataDir, logger });
  ipcMain.handle("templates:load", () => {
    const payload = loadTemplatesData({ dataDir: startupResult.dataDir, logger });
    const stats = computeTemplatesStats(payload.templates);
    return { payload, stats };
  });

  safeHandle("templates:save", (_event, payload) => {
    const saved = saveTemplatesData({ dataDir, payload, logger });
  ipcMain.handle("templates:save", (_event, payload) => {
    const saved = saveTemplatesData({ dataDir: startupResult.dataDir, payload, logger });
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
  ipcMain.handle("templates:export", (_event, { template, format }) =>
    exportTemplateToFile({ dataDir: startupResult.dataDir, template, format, logger })
  );

  ipcMain.handle("templates:exportCategory", (_event, { category }) =>
    exportCategoryZip({ dataDir: startupResult.dataDir, category, logger })
  );

  ipcMain.handle("templates:exportArchive", () =>
    exportArchiveZip({ dataDir: startupResult.dataDir, logger })
  );

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
      dataDir: startupResult.dataDir,
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
