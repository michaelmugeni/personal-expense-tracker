(function () {
  "use strict";

  var STORAGE_KEY = "expense-tracker-theme";

  function getSavedTheme() {
    try {
      return localStorage.getItem(STORAGE_KEY);
    } catch (e) {
      return null;
    }
  }

  function saveTheme(theme) {
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch (e) {
      /* localStorage unavailable — theme just won't persist */
    }
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);

    var icons = document.querySelectorAll(".theme-toggle-icon");
    for (var i = 0; i < icons.length; i++) {
      icons[i].className =
        "theme-toggle-icon bi " +
        (theme === "dark" ? "bi-moon-stars-fill" : "bi-sun-fill");
    }
  }

  // Apply saved (or system-preferred) theme immediately
  var saved = getSavedTheme();

  if (!saved) {
    saved =
      window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light";
  }

  applyTheme(saved);

  // Wire up every toggle switch on the page once DOM is ready
  document.addEventListener("DOMContentLoaded", function () {
    var toggles = document.querySelectorAll(".theme-toggle");

    for (var i = 0; i < toggles.length; i++) {
      toggles[i].addEventListener("click", function () {
        var current = document.documentElement.getAttribute("data-theme");
        var next = current === "dark" ? "light" : "dark";
        applyTheme(next);
        saveTheme(next);
      });
    }
  });
})();
