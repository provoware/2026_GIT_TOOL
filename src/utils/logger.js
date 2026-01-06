import {
  ensureBoolean,
  ensureInList,
  ensureNonEmptyString,
  ensurePlainObject,
  ensurePositiveInteger
} from "./validation.js";
import { createFileLogWriter } from "./logging/file-log-writer.js";

const allowedLevels = ["DEBUG", "INFO", "WARN", "ERROR"];
const levelRank = {
  DEBUG: 0,
  INFO: 1,
  WARN: 2,
  ERROR: 3
};

export const createLogger = (options = {}) => {
  const normalizedOptions =
    options === undefined ? {} : ensurePlainObject(options, "options");
  const debugEnabled = ensureBoolean(
    normalizedOptions.debugEnabled,
    "debugEnabled"
  );
  const loggingEnabled = ensureBoolean(
    normalizedOptions.loggingEnabled,
    "loggingEnabled"
  );
  const logToFile = ensureBoolean(normalizedOptions.logToFile ?? false, "logToFile");
  const logLevel = ensureInList(
    normalizedOptions.logLevel ?? "INFO",
    allowedLevels,
    "logLevel"
  );
  const logFilePath = ensureNonEmptyString(
    normalizedOptions.logFilePath ?? "data/logs/app.log",
    "logFilePath"
  );
  const logRotateDaily = ensureBoolean(
    normalizedOptions.logRotateDaily ?? true,
    "logRotateDaily"
  );
  const logMaxSizeBytes = ensurePositiveInteger(
    normalizedOptions.logMaxSizeBytes ?? 5_242_880,
    "logMaxSizeBytes"
  );

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

  const fileWriter = logToFile
    ? createFileLogWriter({
        logFilePath,
        logRotateDaily,
        logMaxSizeBytes
      })
    : null;

  const shouldLogLevel = (level) => {
    const normalizedLevel = ensureInList(level, allowedLevels, "level");
    const allowed = levelRank[normalizedLevel] >= levelRank[logLevel];
    return ensureBoolean(allowed, "shouldLogLevel");
  };

  const log = (level, message) => {
    const shouldLog = loggingEnabled && shouldLogLevel(level);
    const entry = buildEntry(level, message, shouldLog);

    if (!shouldLog) {
      return entry;
    }

    console.log(`[${entry.timestamp}] [${entry.level}] ${entry.message}`);
    if (fileWriter) {
      fileWriter.writeEntry(entry);
    }

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
