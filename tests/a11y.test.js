import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import path from "node:path";
import { pathToFileURL } from "node:url";
import AxeBuilder from "@axe-core/playwright";
import { chromium } from "playwright";

const themeClasses = [
  "theme-dark",
  "theme-light",
  "theme-high-contrast",
  "theme-high-contrast-dark",
  "theme-high-contrast-light",
  "theme-high-contrast-ocean",
  "theme-high-contrast-sand",
  "theme-high-contrast-forest",
  "theme-high-contrast-violet"
];

const indexUrl = pathToFileURL(path.resolve("src/renderer/index.html")).toString();

let browser;
let page;

const parseColor = (color) => {
  if (color.startsWith("#")) {
    const hex = color.replace("#", "");
    const normalized = hex.length === 3 ? [...hex].map((v) => v + v).join("") : hex;
    return {
      r: Number.parseInt(normalized.slice(0, 2), 16),
      g: Number.parseInt(normalized.slice(2, 4), 16),
      b: Number.parseInt(normalized.slice(4, 6), 16),
      a: 1
    };
  }

  const match = color.match(/rgba?\(([^)]+)\)/u);
  if (!match) {
    throw new Error(`Unbekanntes Farbformat: ${color}`);
  }
  const [r, g, b, a = "1"] = match[1].split(",").map((part) => part.trim());
  return {
    r: Number(r),
    g: Number(g),
    b: Number(b),
    a: Number(a)
  };
};

const blendOnBackground = (foreground, background) => {
  const alpha = foreground.a;
  return {
    r: Math.round(foreground.r * alpha + background.r * (1 - alpha)),
    g: Math.round(foreground.g * alpha + background.g * (1 - alpha)),
    b: Math.round(foreground.b * alpha + background.b * (1 - alpha)),
    a: 1
  };
};

const relativeLuminance = ({ r, g, b }) => {
  const channels = [r, g, b].map((value) => {
    const normalized = value / 255;
    return normalized <= 0.03928
      ? normalized / 12.92
      : ((normalized + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
};

const contrastRatio = (colorA, colorB) => {
  const lumA = relativeLuminance(colorA);
  const lumB = relativeLuminance(colorB);
  const lighter = Math.max(lumA, lumB);
  const darker = Math.min(lumA, lumB);
  return (lighter + 0.05) / (darker + 0.05);
};

const getFocusableDescriptions = async () =>
  page.evaluate(() => {
    const isVisible = (element) => {
      if (element.hasAttribute("hidden")) {
        return false;
      }
      const style = window.getComputedStyle(element);
      return (
        style.display !== "none" &&
        style.visibility !== "hidden" &&
        element.getClientRects().length > 0
      );
    };

    const describe = (element) =>
      element.getAttribute("data-theme") ||
      element.getAttribute("aria-label") ||
      element.id ||
      element.textContent?.trim() ||
      element.tagName;

    return Array.from(
      document.querySelectorAll(
        "button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])"
      )
    )
      .filter((element) => !element.disabled && element.tabIndex >= 0 && isVisible(element))
      .map((element) => describe(element));
  });

const getActiveElementDescription = async () =>
  page.evaluate(() => {
    const describe = (element) =>
      element.getAttribute("data-theme") ||
      element.getAttribute("aria-label") ||
      element.id ||
      element.textContent?.trim() ||
      element.tagName;

    return describe(document.activeElement);
  });

const getActiveOutlineState = async () =>
  page.evaluate(() => {
    const style = window.getComputedStyle(document.activeElement);
    return {
      outlineStyle: style.outlineStyle,
      outlineWidth: style.outlineWidth,
      boxShadow: style.boxShadow,
      textDecorationLine: style.textDecorationLine
    };
  });

before(async () => {
  browser = await chromium.launch();
  page = await browser.newPage();
  await page.goto(indexUrl);
});

after(async () => {
  await page?.close();
  await browser?.close();
});

test("A11y-Scan (axe) für Renderer-Startseite", async () => {
  const results = await new AxeBuilder({ page }).analyze();
  assert.equal(
    results.violations.length,
    0,
    `A11y-Verstöße gefunden: ${results.violations.map((item) => item.id).join(", ")}`
  );
});

test("A11y-Scan (axe) für alle Theme-Varianten", async () => {
  for (const theme of themeClasses) {
    await page.evaluate((themeClass) => {
      document.body.className = themeClass;
    }, theme);

    const results = await new AxeBuilder({ page }).analyze();
    assert.equal(
      results.violations.length,
      0,
      `Theme ${theme}: A11y-Verstöße gefunden: ${results.violations
        .map((item) => item.id)
        .join(", ")}`
    );
  }
});

test("Kontrastwerte (WCAG AA ≥ 4.5:1) für alle Themes", async () => {
  for (const theme of themeClasses) {
    await page.evaluate((themeClass) => {
      document.body.className = themeClass;
    }, theme);

    const variables = await page.evaluate(() => {
      const styles = window.getComputedStyle(document.body);
      return {
        bg: styles.getPropertyValue("--color-bg").trim(),
        text: styles.getPropertyValue("--color-text").trim(),
        primary: styles.getPropertyValue("--color-primary").trim(),
        onPrimary: styles.getPropertyValue("--color-on-primary").trim(),
        muted: styles.getPropertyValue("--color-muted").trim()
      };
    });

    const background = parseColor(variables.bg);
    const text = parseColor(variables.text);
    const primary = parseColor(variables.primary);
    const onPrimary = parseColor(variables.onPrimary);
    const muted = blendOnBackground(parseColor(variables.muted), background);

    const checks = [
      { label: "Text auf Hintergrund", ratio: contrastRatio(text, background) },
      { label: "Primary-Text auf Primary", ratio: contrastRatio(onPrimary, primary) },
      { label: "Muted-Text auf Hintergrund", ratio: contrastRatio(muted, background) }
    ];

    checks.forEach(({ label, ratio }) => {
      assert.ok(
        ratio >= 4.5,
        `${theme}: ${label} unter WCAG AA (ratio ${ratio.toFixed(2)})`
      );
    });
  }
});

test("Fokus-Reihenfolge entspricht der DOM-Reihenfolge", async () => {
  const expectedOrder = await getFocusableDescriptions();
  await page.click("body");

  const actualOrder = [];
  for (let index = 0; index < expectedOrder.length; index += 1) {
    await page.keyboard.press("Tab");
    actualOrder.push(await getActiveElementDescription());
  }

  assert.deepEqual(actualOrder, expectedOrder);
});

test("Fokus ist sichtbar für alle fokussierbaren Elemente", async () => {
  const focusables = await getFocusableDescriptions();
  await page.click("body");

  for (let index = 0; index < focusables.length; index += 1) {
    await page.keyboard.press("Tab");
    const { outlineStyle, outlineWidth, boxShadow, textDecorationLine } =
      await getActiveOutlineState();
    assert.ok(
      outlineStyle !== "none" && outlineWidth !== "0px",
      `Kein sichtbarer Fokus für: ${await getActiveElementDescription()}`
    );
    assert.ok(
      boxShadow !== "none" || textDecorationLine !== "none",
      `Kein zusätzlicher Fokusindikator für: ${await getActiveElementDescription()}`
    );
  }
});
