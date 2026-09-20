// Apply the explicit preference before styles paint. Light remains the default.
(() => {
  const key = "patient-sim-theme";
  let theme = "light";
  try {
    if (localStorage.getItem(key) === "dark") theme = "dark";
  } catch {
    // Storage can be disabled; the current page still supports theme switching.
  }
  document.documentElement.dataset.theme = theme;
  document.addEventListener("DOMContentLoaded", () => {
    const button = document.getElementById("theme-toggle");
    const update = () => {
      document.documentElement.dataset.theme = theme;
      const label = theme === "dark" ? "Use light mode" : "Use dark mode";
      button.setAttribute("aria-label", label);
      button.dataset.tooltip = label;
    };
    update();
    button.addEventListener("click", () => {
      theme = theme === "light" ? "dark" : "light";
      update();
      try {
        localStorage.setItem(key, theme);
      } catch {
        // The preference lasts for this page when storage is unavailable.
      }
    });
  });
})();
