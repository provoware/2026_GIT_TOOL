#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const TODO_PATH = path.join(ROOT, "todo.txt");
const PROGRESS_PATH = path.join(ROOT, "PROGRESS.md");

const args = new Set(process.argv.slice(2));
const shouldUpdate = args.has("--update");
const shouldCheck = args.has("--check");

function formatPercent(value) {
  return value.toFixed(2).replace(".", ",");
}

function parseTodo(text) {
  const lines = text.split(/\r?\n/);
  const tasks = lines
    .map((line) => line.trim())
    .filter((line) => /^\[(x|X| )\]\s+/.test(line));
  const done = tasks.filter((line) => /^\[(x|X)\]/.test(line)).length;
  return { total: tasks.length, done, open: tasks.length - done };
}

function buildProgressMarkdown(stats) {
  const today = new Date().toISOString().slice(0, 10);
  const percent = stats.total ? (stats.done / stats.total) * 100 : 0;
  return [
    "# PROGRESS",
    "",
    `Stand: ${today}`,
    "",
    `- Gesamt: ${stats.total} Tasks`,
    `- Erledigt: ${stats.done} Tasks`,
    `- Offen: ${stats.open} Tasks`,
    `- Fortschritt: ${formatPercent(percent)} %`,
    "",
  ].join("\n");
}

function readFileOrExit(filePath, label) {
  try {
    return fs.readFileSync(filePath, "utf8");
  } catch (error) {
    console.error(`${label} konnte nicht gelesen werden: ${filePath}`);
    console.error(String(error));
    process.exit(1);
  }
}

function parseProgress(text) {
  const getNum = (pattern, isPercent = false) => {
    const match = text.match(pattern);
    if (!match) return null;
    const raw = match[1];
    return isPercent ? Number(raw.replace(",", ".")) : Number(raw);
  };
  return {
    total: getNum(/- Gesamt:\s+(\d+)\s+Tasks/),
    done: getNum(/- Erledigt:\s+(\d+)\s+Tasks/),
    open: getNum(/- Offen:\s+(\d+)\s+Tasks/),
    percent: getNum(/- Fortschritt:\s+([\d,]+)\s+%/, true),
  };
}

const todoText = readFileOrExit(TODO_PATH, "todo.txt");
const stats = parseTodo(todoText);
const percent = stats.total ? (stats.done / stats.total) * 100 : 0;

console.log("Fortschritt aus todo.txt berechnet:");
console.log(`- Gesamt: ${stats.total} Tasks`);
console.log(`- Erledigt: ${stats.done} Tasks`);
console.log(`- Offen: ${stats.open} Tasks`);
console.log(`- Fortschritt: ${formatPercent(percent)} %`);

if (shouldUpdate) {
  const content = buildProgressMarkdown(stats);
  try {
    fs.writeFileSync(PROGRESS_PATH, content, "utf8");
    console.log("PROGRESS.md wurde aktualisiert.");
  } catch (error) {
    console.error("PROGRESS.md konnte nicht geschrieben werden.");
    console.error(String(error));
    process.exit(1);
  }
}

if (shouldCheck) {
  const progressText = readFileOrExit(PROGRESS_PATH, "PROGRESS.md");
  const recorded = parseProgress(progressText);
  const expectedPercent = formatPercent(percent);
  const expected = {
    total: stats.total,
    done: stats.done,
    open: stats.open,
    percent: expectedPercent,
  };

  const issues = [];
  if (recorded.total !== expected.total) issues.push("Gesamt");
  if (recorded.done !== expected.done) issues.push("Erledigt");
  if (recorded.open !== expected.open) issues.push("Offen");
  if (String(recorded.percent).replace(".", ",") !== expected.percent) issues.push("Fortschritt");

  if (issues.length > 0) {
    console.error(`PROGRESS.md stimmt nicht mit todo.txt überein (${issues.join(", ")}).`);
    process.exit(2);
  }
  console.log("PROGRESS.md stimmt mit todo.txt überein.");
}
