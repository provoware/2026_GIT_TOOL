import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const REQUIRED_DIRS = [
  {
    name: "config",
    purpose: "Einstellungen (Konfiguration)",
  },
  {
    name: "data",
    purpose: "variable Daten (Datenablage)",
  },
  {
    name: "logs",
    purpose: "Protokolle (Log-Dateien)",
  },
];

const args = new Set(process.argv.slice(2));
const isDryRun = args.has("--dry-run");
const isDebug = args.has("--debug");

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(scriptDir, "..");

const formatPath = (targetPath) => `${path.relative(projectRoot, targetPath)}/`;

const validateDirName = (name) => {
  if (typeof name !== "string" || name.trim().length === 0) {
    return {
      ok: false,
      message:
        "Ungültiger Ordnername (Verzeichnisname). Bitte prüfe die Start-Konfiguration.",
    };
  }
  if (name.includes(path.sep)) {
    return {
      ok: false,
      message:
        "Ungültiger Ordnername (Verzeichnisname): Der Name darf keine Pfadtrenner enthalten.",
    };
  }
  return { ok: true };
};

const ensureDirectory = ({ name, purpose }) => {
  const validation = validateDirName(name);
  if (!validation.ok) {
    return { status: "failed", name, message: validation.message };
  }

  const targetPath = path.join(projectRoot, name);

  if (fs.existsSync(targetPath)) {
    return {
      status: "exists",
      name,
      targetPath,
      message: `OK: Ordner (Verzeichnis) vorhanden: ${formatPath(targetPath)}`,
    };
  }

  if (isDryRun) {
    return {
      status: "missing",
      name,
      targetPath,
      message: `Fehlt: Ordner (Verzeichnis) ${formatPath(
        targetPath,
      )} würde erstellt werden.`,
    };
  }

  try {
    fs.mkdirSync(targetPath, { recursive: true });
    return {
      status: "created",
      name,
      targetPath,
      message: `Neu erstellt: Ordner (Verzeichnis) ${formatPath(targetPath)}.`,
    };
  } catch (error) {
    const details =
      error instanceof Error ? error.message : "Unbekannter Fehler.";
    return {
      status: "failed",
      name,
      targetPath,
      message: `Fehler: Ordner (Verzeichnis) ${formatPath(
        targetPath,
      )} konnte nicht erstellt werden. Bitte prüfe Rechte (Zugriffsrechte). Details: ${details}`,
    };
  }
};

const printHeader = () => {
  console.log("Start-Check: Projektstruktur prüfen");
  console.log("-----------------------------------");
  if (isDryRun) {
    console.log(
      "Hinweis: Trockenlauf (dry run) aktiviert. Es werden keine Ordner erstellt.",
    );
  }
};

const printFooter = ({ results, failureCount }) => {
  const createdCount = results.filter((item) => item.status === "created").length;
  const existsCount = results.filter((item) => item.status === "exists").length;
  const missingCount = results.filter((item) => item.status === "missing").length;

  console.log("-----------------------------------");
  console.log(
    `Zusammenfassung: ${existsCount} vorhanden, ${createdCount} neu erstellt, ${missingCount} fehlt, ${failureCount} Fehler.`,
  );

  if (failureCount > 0) {
    console.log(
      "Bitte behebe die Fehler und starte das Tool erneut. Tipp: Rechte (Zugriffsrechte) prüfen oder Ordner manuell anlegen.",
    );
  } else {
    console.log("Alles bereit. Du kannst das Tool jetzt starten.");
  }
};

const run = () => {
  printHeader();

  const results = REQUIRED_DIRS.map((entry) => ensureDirectory(entry));

  results.forEach((result) => {
    console.log(result.message);
    if (result.status === "created" && result.targetPath) {
      const entry = REQUIRED_DIRS.find((item) => item.name === result.name);
      if (entry) {
        console.log(
          `Hinweis: ${entry.purpose} liegen in ${formatPath(result.targetPath)}`,
        );
      }
    }

    if (isDebug && result.targetPath) {
      console.log(`Debug: Zielpfad (voller Pfad) = ${result.targetPath}`);
    }
  });

  const failureCount = results.filter((item) => item.status === "failed").length;
  printFooter({ results, failureCount });

  if (failureCount > 0) {
    process.exitCode = 1;
  }
};

run();
