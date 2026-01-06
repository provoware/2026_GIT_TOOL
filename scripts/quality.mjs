import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createLogger } from "../src/utils/logger.js";
import { loadConfig } from "../src/utils/config.js";
import {
  buildQualityPlan,
  loadQualityConfig,
  loadQualityManifest
} from "../src/utils/quality.js";
import { ensureBoolean, ensureNonEmptyString, ensurePlainObject } from "../src/utils/validation.js";
import { loadManifest } from "../src/utils/manifestLoader.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const appRoot = path.resolve(__dirname, "..");

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
import {
  createShellCommandRunner,
  ensureDependencies,
  runQualityPlan
} from "../src/utils/quality-runner.js";

const run = () => {
  console.log("\n[Start] Qualitätsprüfung (Quality Check) läuft...");
  console.log(
    "[Info] Wir prüfen Linting (Regelcheck), Formatierung, Tests und A11y (Barrierefreiheit)."
  );

  const manifest = loadManifest({ appRoot });
  const appConfig = loadConfig({ manifest, configPath: manifest.paths.userConfig });
  const logger = createLogger(appConfig);
  const qualityManifest = loadQualityManifest({
    manifestPath: manifest.paths.qualityManifest
  });
  const config = loadQualityConfig({ configPath: manifest.paths.qualityConfig });
  const plan = buildQualityPlan({ manifest: qualityManifest, config });
  const manifest = loadQualityManifest();
  const config = loadQualityConfig();
  const plan = buildQualityPlan({ manifest, config });
  const commandRunner = createShellCommandRunner();

  logger.debug(`[Debug] Qualitätsplan geladen (${plan.steps.length} Schritte).`);

  const dependencyStatus = ensureDependencies({
    logger,
    commandRunner,
    projectRoot: process.cwd()
  });

  if (!dependencyStatus.ok) {
    console.error("\n[Fehler] Abhängigkeiten fehlen. Quality-Check gestoppt.");
    console.error(
      "[Hinweis] Bitte npm install starten oder Internet prüfen."
    );
    process.exitCode = 1;
    return;
  }

  const result = runQualityPlan({ plan, logger, commandRunner });

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
