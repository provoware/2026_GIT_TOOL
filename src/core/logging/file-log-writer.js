import fs from "node:fs";
import path from "node:path";
import {
  ensureBoolean,
  ensureInList,
  ensureNonEmptyString,
  ensurePlainObject,
  ensurePositiveInteger
} from "../validation.js";

const allowedLevels = ["DEBUG", "INFO", "WARN", "ERROR"];

const normalizeEntry = (entry) => {
  const normalizedEntry = ensurePlainObject(entry, "entry");
  const level = ensureInList(normalizedEntry.level, allowedLevels, "entry.level");
  const message = ensureNonEmptyString(normalizedEntry.message, "entry.message");
  const timestamp = ensureNonEmptyString(normalizedEntry.timestamp, "entry.timestamp");

  return {
    ...normalizedEntry,
    level,
    message,
    timestamp
  };
};

const formatEntry = (entry) => {
  const normalizedEntry = normalizeEntry(entry);
  const line = `[${normalizedEntry.timestamp}] [${normalizedEntry.level}] ${normalizedEntry.message}\n`;
  return ensureNonEmptyString(line, "formattedEntry");
};

const buildDailyPath = (basePath, date) => {
  const resolvedBasePath = ensureNonEmptyString(basePath, "basePath");
  const parsed = path.parse(resolvedBasePath);
  const dateStamp = ensureNonEmptyString(date.toISOString().slice(0, 10), "dateStamp");
  const extension = parsed.ext.length > 0 ? parsed.ext : ".log";
  const filename = `${parsed.name}-${dateStamp}${extension}`;
  return path.join(parsed.dir, filename);
};

const buildSizeRotationPath = (targetPath, date, index = 0) => {
  const resolvedTargetPath = ensureNonEmptyString(targetPath, "targetPath");
  const parsed = path.parse(resolvedTargetPath);
  const stamp = ensureNonEmptyString(
    date.toISOString().replace(/[:.]/g, "-"),
    "rotationStamp"
  );
  const extension = parsed.ext.length > 0 ? parsed.ext : ".log";
  const suffix = index > 0 ? `-${index}` : "";
  return path.join(parsed.dir, `${parsed.name}-${stamp}${suffix}${extension}`);
};

const ensureLogDirectory = (filePath) => {
  const normalizedPath = ensureNonEmptyString(filePath, "filePath");
  const directory = path.dirname(normalizedPath);
  fs.mkdirSync(directory, { recursive: true });
  return directory;
};

const rotateForSize = (filePath, maxSizeBytes) => {
  const normalizedPath = ensureNonEmptyString(filePath, "filePath");
  const limit = ensurePositiveInteger(maxSizeBytes, "maxSizeBytes");

  if (!fs.existsSync(normalizedPath)) {
    return normalizedPath;
  }

  const currentSize = fs.statSync(normalizedPath).size;
  if (currentSize < limit) {
    return normalizedPath;
  }

  const now = new Date();
  let candidate = buildSizeRotationPath(normalizedPath, now);
  let counter = 1;

  while (fs.existsSync(candidate)) {
    candidate = buildSizeRotationPath(normalizedPath, now, counter);
    counter += 1;
  }

  fs.renameSync(normalizedPath, candidate);
  return normalizedPath;
};

export const createFileLogWriter = (options = {}) => {
  const normalizedOptions =
    options === undefined ? {} : ensurePlainObject(options, "options");
  const logFilePath = ensureNonEmptyString(
    normalizedOptions.logFilePath,
    "logFilePath"
  );
  const logRotateDaily = ensureBoolean(
    normalizedOptions.logRotateDaily,
    "logRotateDaily"
  );
  const logMaxSizeBytes = ensurePositiveInteger(
    normalizedOptions.logMaxSizeBytes,
    "logMaxSizeBytes"
  );
  const resolvedBasePath = path.resolve(process.cwd(), logFilePath);

  const resolveTargetPath = (date) => {
    if (!logRotateDaily) {
      return resolvedBasePath;
    }

    return buildDailyPath(resolvedBasePath, date);
  };

  const writeEntry = (entry) => {
    const normalizedEntry = normalizeEntry(entry);
    const targetPath = resolveTargetPath(new Date());

    ensureLogDirectory(targetPath);
    rotateForSize(targetPath, logMaxSizeBytes);

    const line = formatEntry(normalizedEntry);
    fs.appendFileSync(targetPath, line, "utf8");

    return {
      logPath: ensureNonEmptyString(targetPath, "logPath"),
      line
    };
  };

  return {
    writeEntry
  };
};
