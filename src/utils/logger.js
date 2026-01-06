import {
  ensureBoolean,
  ensureInList,
  ensureNonEmptyString
} from "./validation.js";

export const createLogger = ({ debugEnabled, loggingEnabled }) => {
  ensureBoolean(debugEnabled, "debugEnabled");
  ensureBoolean(loggingEnabled, "loggingEnabled");

  const allowedLevels = ["INFO", "WARN", "ERROR", "DEBUG"];

  const buildEntry = (level, message, delivered) => {
    const normalizedLevel = ensureInList(level, allowedLevels, "level");
    const normalizedMessage = ensureNonEmptyString(message, "message");
    const timestamp = ensureNonEmptyString(new Date().toISOString(), "timestamp");
    const deliveredFlag = ensureBoolean(delivered, "delivered");

    return {
      level: normalizedLevel,
      message: normalizedMessage,
      timestamp,
      delivered: deliveredFlag
    };
  };

  const log = (level, message) => {
    const entry = buildEntry(level, message, loggingEnabled);

    if (!loggingEnabled) {
      return entry;
    }

    console.log(`[${entry.timestamp}] [${entry.level}] ${entry.message}`);
    return entry;
  };

  const debug = (message) => {
    if (!debugEnabled) {
      return buildEntry("DEBUG", message, false);
    }

    return log("DEBUG", message);
  };

  return {
    info: (message) => log("INFO", message),
    warn: (message) => log("WARN", message),
    error: (message) => log("ERROR", message),
    debug
  };
};
