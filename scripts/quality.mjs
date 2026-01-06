import { spawnSync } from "node:child_process";
import { createLogger } from "../src/core/logger.js";
import { loadConfig } from "../src/core/config.js";
import {
  buildQualityPlan,
  buildQualityRunResult,
  loadQualityConfig,
  loadQualityManifest
} from "../src/services/quality.js";
import {
  ensureBoolean,
  ensureNonEmptyString,
  ensurePlainObject
} from "../src/core/validation.js";

const buildRunMessage = (step) => {
  const normalizedStep = ensurePlainObject(step, "step");
  const label = ensureNonEmptyString(normalizedStep.label, "label");
  const description = ensureNonEmptyString(
    normalizedStep.description,
    "description"
  );
  return `${label}: ${description}`;
};

const runCommand = (command, label, logger) => {
  const safeCommand = ensureNonEmptyString(command, "command");
  const safeLabel = ensureNonEmptyString(label, "label");
  const safeLogger = ensurePlainObject(logger, "logger");

  safeLogger.info(`[Schritt] ${safeLabel} startet.`);
  const result = spawnSync(safeCommand, { shell: true, stdio: "inherit" });
  const exitCode = typeof result.status === "number" ? result.status : 1;
  const ok = exitCode === 0;
  const status = ok ? "ok" : "failed";

  safeLogger.info(
    `[Status] ${safeLabel} beendet: ${status.toUpperCase()} (Exit-Code ${exitCode}).`
  );

  return {
    ok,
    exitCode,
    status
  };
};

const runQualityPlan = ({ plan, logger }) => {
  const normalizedPlan = ensurePlainObject(plan, "plan");
  const safeLogger = ensurePlainObject(logger, "logger");
  const steps = Array.isArray(normalizedPlan.steps) ? normalizedPlan.steps : [];
  const stopOnFailure = ensureBoolean(normalizedPlan.stopOnFailure, "stopOnFailure");
  const results = [];

  let overallOk = true;

  steps.forEach((step) => {
    if (!overallOk && stopOnFailure) {
      return;
    }

    const message = buildRunMessage(step);
    safeLogger.info(`[Info] ${message}`);

    const firstRun = runCommand(step.command, step.label, safeLogger);
    if (firstRun.ok) {
      results.push({
        id: step.id,
        label: step.label,
        status: "ok",
        message: "Prüfung erfolgreich abgeschlossen."
      });
      return;
    }

    if (step.shouldFix && step.fixCommand) {
      safeLogger.warn(
        `[Hinweis] Fehler erkannt. Ich starte Auto-Reparatur (Auto-Fix).`
      );
      const fixRun = runCommand(step.fixCommand, `${step.label} Auto-Fix`, safeLogger);
      if (fixRun.ok) {
        safeLogger.info(
          `[Info] Auto-Fix abgeschlossen. Ich prüfe erneut (Re-Check).`
        );
        const retryRun = runCommand(step.command, step.label, safeLogger);
        if (retryRun.ok) {
          results.push({
            id: step.id,
            label: step.label,
            status: "ok",
            message: "Auto-Fix erfolgreich, Prüfung besteht."
          });
          return;
        }
      }
    }

    results.push({
      id: step.id,
      label: step.label,
      status: "failed",
      message: "Prüfung fehlgeschlagen. Bitte Ausgabe prüfen."
    });
    overallOk = false;
  });

  return buildQualityRunResult({ ok: overallOk, steps: results });
};

const run = () => {
  console.log("\n[Start] Qualitätsprüfung (Quality Check) läuft...");
  console.log("[Info] Wir prüfen Code-Regeln (Linting) und Formatierung.");

  const appConfig = loadConfig();
  const logger = createLogger(appConfig);
  const manifest = loadQualityManifest();
  const config = loadQualityConfig();
  const plan = buildQualityPlan({ manifest, config });

  logger.debug(`[Debug] Qualitätsplan geladen (${plan.steps.length} Schritte).`);

  const result = runQualityPlan({ plan, logger });

  if (plan.printSummary) {
    console.log("\n[Zusammenfassung] Ergebnis der Qualitätsprüfung:");
    result.steps.forEach((step) => {
      console.log(`- ${step.label}: ${step.status.toUpperCase()} (${step.message})`);
    });
  }

  if (!result.ok) {
    console.error("\n[Fehler] Qualitätsprüfung fehlgeschlagen.");
    console.error(
      "[Hinweis] Bitte Hinweise lesen und erneut starten (Re-Run)."
    );
    process.exitCode = 1;
    return;
  }

  console.log("\n[Erfolg] Alle Qualitätsprüfungen sind erfolgreich.");
};

try {
  run();
} catch (error) {
  const message = error instanceof Error ? error.message : "Unbekannter Fehler";
  console.error(`\n[Fehler] Qualitätsprüfung konnte nicht gestartet werden: ${message}`);
  console.error("[Hinweis] Bitte Konfiguration prüfen (Config-Check)." );
  process.exitCode = 1;
}
