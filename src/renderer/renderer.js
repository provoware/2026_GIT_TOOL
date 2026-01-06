const themeButtons = document.querySelectorAll(".theme-button");
const clockElement = document.querySelector(".clock");

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

const applyTheme = (themeClass) => {
  if (typeof themeClass !== "string" || themeClass.length === 0) {
    return;
  }

  document.body.className = themeClass;
};

if (themeButtons.length > 0) {
  themeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const themeClass = button.dataset.theme;
      applyTheme(themeClass);
    });
  });
}

updateClock();
setInterval(updateClock, 1000);
