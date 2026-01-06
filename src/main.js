import { app, BrowserWindow, dialog, ipcMain } from "electron";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createLogger } from "./utils/logger.js";
import { loadConfig } from "./utils/config.js";
import { initializeTemplatesStorage } from "./utils/templates.js";
import { registerTemplatesIpcHandlers } from "./ipc/templatesIpc.js";

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

  logger.info(`${config.appName} startet.`);
  logger.debug(`Aktives Theme: ${config.theme}`);

  initializeTemplatesStorage({ dataDir, logger });
  createWindow(logger);

  registerTemplatesIpcHandlers({
    dataDir,
    logger,
    ipcMain,
    dialog
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
