import { test } from "node:test";
import assert from "node:assert/strict";
import { createLogger } from "../src/utils/logger.js";

const withConsoleSpy = async (fn) => {
  const original = console.log;
  const calls = [];
  console.log = (...args) => calls.push(args);

  try {
    await fn(calls);
  } finally {
    console.log = original;
  }
};

test("createLogger respects loggingEnabled", async () => {
  await withConsoleSpy((calls) => {
    const logger = createLogger({ debugEnabled: false, loggingEnabled: false });
    const infoEntry = logger.info("test");
    const errorEntry = logger.error("fail");
    assert.equal(calls.length, 0);
    assert.equal(infoEntry.delivered, false);
    assert.equal(errorEntry.delivered, false);
  });
});

test("createLogger emits debug only when enabled", async () => {
  await withConsoleSpy((calls) => {
    const logger = createLogger({ debugEnabled: true, loggingEnabled: true });
    const entry = logger.debug("debug message");
    assert.equal(calls.length, 1);
    assert.match(calls[0][0], /\[DEBUG\]/);
    assert.equal(entry.level, "DEBUG");
  });
});
