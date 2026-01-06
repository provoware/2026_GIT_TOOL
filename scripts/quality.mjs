import { createLogger } from "../src/utils/logger.js";
import { loadConfig } from "../src/utils/config.js";
import {
  buildQualityPlan,
  loadQualityConfig,
  loadQualityManifest
} from "../src/utils/quality.js";
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

  const appConfig = loadConfig();
  const logger = createLogger(appConfig);
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
