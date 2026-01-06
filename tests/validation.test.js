import { test } from "node:test";
import assert from "node:assert/strict";
import {
  ensureArrayOfNonEmptyStrings,
  ensureArrayOfStrings,
  ensureBoolean,
  ensureInList,
  ensureNonEmptyString,
  ensurePlainObject
} from "../src/core/validation.js";

test("ensureNonEmptyString trims input", () => {
  const result = ensureNonEmptyString("  ok ", "label");
  assert.equal(result, "ok");
});

test("ensureBoolean rejects non boolean", () => {
  assert.throws(() => ensureBoolean("yes", "flag"), /flag muss true oder false sein/);
});

test("ensureInList validates values", () => {
  assert.equal(ensureInList("a", ["a", "b"], "field"), "a");
});

test("ensurePlainObject rejects arrays", () => {
  assert.throws(() => ensurePlainObject([], "config"), /config muss ein Objekt sein/);
});

test("ensureArrayOfNonEmptyStrings trims items", () => {
  const result = ensureArrayOfNonEmptyStrings([" a ", "b"], "themes");
  assert.deepEqual(result, ["a", "b"]);
});

test("ensureArrayOfStrings accepts empty array", () => {
  const result = ensureArrayOfStrings([], "deps");
  assert.deepEqual(result, []);
});
