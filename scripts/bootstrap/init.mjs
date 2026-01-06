import { createLogger } from "../../src/utils/logger.js";
import { runStartupRoutine } from "../../src/utils/startup.js";

const appRoot = process.env.BOOTSTRAP_PROJECT_ROOT ?? process.cwd();

const logger = createLogger({
  debugEnabled: false,
  loggingEnabled: false
});

const reportStatus = (payload) => {
  const level = String(payload.level ?? "info").toUpperCase();
  const message = String(payload.message ?? "Status aktualisiert.");
  const suggestion = payload.suggestion
    ? ` Hinweis: ${payload.suggestion}`
    : "";
  console.log(`[${level}] ${message}${suggestion}`);
};

const result = runStartupRoutine({
  appRoot,
  logger,
  reportStatus
});

if (!result.ok) {
  console.error("[ERROR] Startprüfung konnte nicht abgeschlossen werden.");
  process.exit(1);
}

console.log("[SUCCESS] Startprüfung abgeschlossen.");
