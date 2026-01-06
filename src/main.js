import { app, BrowserWindow, dialog, ipcMain } from "electron";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createLogger } from "./core/logger.js";
import { loadConfig } from "./core/config.js";
import { runStartupRoutine } from "./core/startup.js";
import { ensureBoolean, ensurePlainObject } from "./core/validation.js";
import { registerTemplatesIpcHandlers } from "./ipc/templatesIpc.js";
import { loadModules } from "./services/moduleLoader.js";
import { initializeTemplatesStorage } from "./services/templates.js";

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

  if (!startupResult.ok) {
    bootstrapLogger.error("Startroutine fehlgeschlagen. Anwendung wird beendet.");
    app.quit();
    return;
  }

  const config = loadConfig({ configPath: startupResult.configPath });
  const logger = createLogger(config);

  logger.info(`${config.appName} startet.`);
  logger.debug(`Aktives Theme: ${config.theme}`);

  await loadModules({
    logger,
    context: {
      app,
      appName: config.appName,
      config,
      dataDir: startupResult.dataDir,
      logger
    }
  });

  initializeTemplatesStorage({ dataDir: startupResult.dataDir, logger });

  registerTemplatesIpcHandlers({
    dataDir: startupResult.dataDir,
    logger,
    ipcMain,
    dialog
  });

  mainWindow = createWindow({
    logger,
    startupStatusBuffer
  });

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      mainWindow = createWindow({
        logger,
        startupStatusBuffer
      });
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});
