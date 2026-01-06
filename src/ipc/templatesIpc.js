import {
  computeTemplatesStats,
  exportArchiveZip,
  exportCategoryZip,
  exportTemplateToFile,
  importTemplatesFromFile,
  loadTemplatesData,
  saveTemplatesData
} from "../services/templates.js";
import { ensureNonEmptyString, ensurePlainObject } from "../core/validation.js";

const ensureLogger = (logger) => {
  const target = ensurePlainObject(logger, "logger");
  ["info", "warn", "error", "debug"].forEach((key) => {
    if (typeof target[key] !== "function") {
      throw new Error(`logger.${key} muss eine Funktion sein.`);
    }
  });
  return target;
};

const ensureIpcMain = (ipcMain) => {
  const target = ensurePlainObject(ipcMain, "ipcMain");
  if (typeof target.handle !== "function") {
    throw new Error("ipcMain.handle muss eine Funktion sein.");
  }
  return target;
};

const ensureDialog = (dialog) => {
  const target = ensurePlainObject(dialog, "dialog");
  if (typeof target.showOpenDialog !== "function") {
    throw new Error("dialog.showOpenDialog muss eine Funktion sein.");
  }
  return target;
};

const ensurePayloadWithStats = (payload, stats) => ({
  payload: ensurePlainObject(payload, "payload"),
  stats: ensurePlainObject(stats, "stats")
});

export const registerTemplatesIpcHandlers = (options) => {
  const resolvedOptions = ensurePlainObject(options, "options");
  const dataDir = ensureNonEmptyString(resolvedOptions.dataDir, "dataDir");
  const logger = ensureLogger(resolvedOptions.logger);
  const ipcMain = ensureIpcMain(resolvedOptions.ipcMain);
  const dialog = ensureDialog(resolvedOptions.dialog);

  logger.debug("Templates-IPC-Handler werden registriert.");

  ipcMain.handle("templates:load", () => {
    const payload = loadTemplatesData({ dataDir, logger });
    const stats = computeTemplatesStats(payload.templates);
    return ensurePayloadWithStats(payload, stats);
  });

  ipcMain.handle("templates:save", (_event, payload) => {
    const saved = saveTemplatesData({
      dataDir,
      payload: ensurePlainObject(payload, "payload"),
      logger
    });
    const stats = computeTemplatesStats(saved.templates);
    return ensurePayloadWithStats(saved, stats);
  });

  ipcMain.handle("templates:export", (_event, args) => {
    const params = ensurePlainObject(args, "args");
    const filePath = exportTemplateToFile({
      dataDir,
      template: params.template,
      format: params.format,
      logger
    });
    return ensureNonEmptyString(filePath, "filePath");
  });

  ipcMain.handle("templates:exportCategory", async (_event, args) => {
    const params = ensurePlainObject(args, "args");
    const zipPath = await exportCategoryZip({ dataDir, category: params.category, logger });
    return ensureNonEmptyString(zipPath, "zipPath");
  });

  ipcMain.handle("templates:exportArchive", async () => {
    const zipPath = await exportArchiveZip({ dataDir, logger });
    return ensureNonEmptyString(zipPath, "zipPath");
  });

  ipcMain.handle("templates:import", async () => {
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
    return ensurePayloadWithStats(merged, stats);
  });

  return {
    dataDir,
    logger,
    handlersRegistered: true
  };
};
