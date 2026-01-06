import { ensureBoolean } from "./validation.js";

export const createLogger = ({ debugEnabled, loggingEnabled }) => {
  ensureBoolean(debugEnabled, "debugEnabled");
  ensureBoolean(loggingEnabled, "loggingEnabled");

  const log = (level, message) => {
    if (!loggingEnabled) {
      return;
    }

    const timestamp = new Date().toISOString();
    console.log(`[${timestamp}] [${level}] ${message}`);
  };

  const debug = (message) => {
    if (!debugEnabled) {
      return;
    }

    log("DEBUG", message);
  };

  return {
    info: (message) => log("INFO", message),
    warn: (message) => log("WARN", message),
    error: (message) => log("ERROR", message),
    debug
  };
};
