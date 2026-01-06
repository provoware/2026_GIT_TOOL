import { ensureNonEmptyString, ensurePlainObject } from "./validation.js";

const ensureFunction = (value, label) => {
  if (typeof value !== "function") {
    throw new Error(`${label} muss eine Funktion sein.`);
  }

  return value;
};

const ensureHandleShape = (value) => {
  ensurePlainObject(value, "ipcMain");
  ensureFunction(value.handle, "ipcMain.handle");
  return value;
};

const isNonEmptyString = (value) => typeof value === "string" && value.trim().length > 0;

export const buildIpcSuccess = (data) => {
  const response = {
    ok: true,
    data
  };
  if (!isIpcResponse(response)) {
    throw new Error("IPC-Erfolgsmeldung ist ungültig.");
  }
  return response;
};

export const buildIpcError = (error, context) => {
  const safeContext = ensureNonEmptyString(context, "context");
  const message = isNonEmptyString(error?.message)
    ? error.message
    : "Unbekannter Fehler.";
  const code = isNonEmptyString(error?.code) ? error.code : "UNKNOWN";

  const response = {
    ok: false,
    error: {
      message,
      code,
      context: safeContext,
      details: {
        name: error?.name ?? "Error",
        stack: error?.stack ?? null
      }
    }
  };
  if (!isIpcResponse(response)) {
    throw new Error("IPC-Fehlermeldung ist ungültig.");
  }
  return response;
};

const isIpcResponse = (value) => {
  if (!value || typeof value !== "object") {
    return false;
  }
  if (typeof value.ok !== "boolean") {
    return false;
  }
  if (value.ok) {
    return Object.prototype.hasOwnProperty.call(value, "data");
  }
  return (
    Object.prototype.hasOwnProperty.call(value, "error") &&
    value.error &&
    typeof value.error === "object" &&
    isNonEmptyString(value.error.message) &&
    isNonEmptyString(value.error.code) &&
    isNonEmptyString(value.error.context)
  );
};

export const createSafeHandle = ({ ipcMain, logger }) => {
  const safeIpcMain = ensureHandleShape(ipcMain);
  const safeLogger = logger ?? null;

  return (channel, handler) => {
    const safeChannel = ensureNonEmptyString(channel, "channel");
    const safeHandler = ensureFunction(handler, "handler");

    safeIpcMain.handle(safeChannel, async (event, ...args) => {
      try {
        const result = await safeHandler(event, ...args);
        const response = buildIpcSuccess(result);
        if (!isIpcResponse(response)) {
          throw new Error("IPC-Antwort ist ungültig.");
        }
        return response;
      } catch (error) {
        const response = buildIpcError(error, safeChannel);
        if (safeLogger) {
          safeLogger.error(`IPC-Fehler (${safeChannel}): ${response.error.message}`);
        }
        return response;
      }
    });

    return true;
  };
};
