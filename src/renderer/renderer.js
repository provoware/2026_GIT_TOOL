const themeButtons = document.querySelectorAll(".theme-button");
const clockElement = document.querySelector(".clock");

const isNonEmptyString = (value) => typeof value === "string" && value.trim().length > 0;

const getAllowedThemes = (buttons) =>
  Array.from(buttons)
    .map((button) => button.dataset.theme)
    .filter((theme) => isNonEmptyString(theme));

const updateClock = () => {
  const now = new Date();
  const timeString = now.toLocaleTimeString("de-DE", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit"
  });

  if (clockElement) {
    clockElement.textContent = `Uhrzeit: ${timeString}`;
  }
};

const applyTheme = (themeClass, allowedThemes) => {
  if (!isNonEmptyString(themeClass)) {
    return false;
  }

  if (Array.isArray(allowedThemes) && !allowedThemes.includes(themeClass)) {
    return false;
  }

  document.body.className = themeClass;
  return true;
};

if (themeButtons.length > 0) {
  const allowedThemes = getAllowedThemes(themeButtons);
  const initialTheme = document.body.className;

  themeButtons.forEach((button) => {
    const isActive = button.dataset.theme === initialTheme;
    button.setAttribute("aria-pressed", isActive ? "true" : "false");
  });

  themeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const themeClass = button.dataset.theme;
      const applied = applyTheme(themeClass, allowedThemes);

      if (applied) {
        themeButtons.forEach((entry) => {
          entry.setAttribute("aria-pressed", entry === button ? "true" : "false");
        });
      }
    });
  });
}

updateClock();
setInterval(updateClock, 1000);
