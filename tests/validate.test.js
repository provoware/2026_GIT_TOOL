import { test } from "node:test";
import assert from "node:assert/strict";
import {
  ensureArray,
  ensureFunction,
  ensureOptionalString
} from "../src/utils/validate.js";

test("ensureOptionalString returns null for empty input", () => {
  assert.equal(ensureOptionalString("", "maybe"), null);
  assert.equal(ensureOptionalString(null, "maybe"), null);
});

test("ensureOptionalString trims non-empty input", () => {
  assert.equal(ensureOptionalString("  ok ", "maybe"), "ok");
});

test("ensureFunction rejects non-function", () => {
  assert.throws(() => ensureFunction(123, "handler"), /handler muss eine Funktion sein/);
});

test("ensureArray accepts arrays", () => {
  const input = ["a", "b"];
  assert.deepEqual(ensureArray(input, "list"), input);
});
