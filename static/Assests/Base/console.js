/* ================================================
   DISABLE RIGHT CLICK CONTEXT MENU
   ================================================ */
document.addEventListener('contextmenu', function (e) {
  e.preventDefault();
});


/* ================================================
   DISABLE COMMON DEVELOPER SHORTCUT KEYS
   F12
   CTRL + SHIFT + I
   CTRL + SHIFT + J
   CTRL + SHIFT + C
   CTRL + U
   ================================================ */
document.addEventListener('keydown', function (e) {
  if (
    e.key === "F12" ||
    (e.ctrlKey && e.shiftKey && ["I", "J", "C"].includes(e.key)) ||
    (e.ctrlKey && e.key === "U")
  ) {
    e.preventDefault();
    return false;
  }
});


/* ================================================
   BLOCK VIEW SOURCE VIA MOUSE SELECTION
   ================================================ */
document.addEventListener('selectstart', function (e) {
  e.preventDefault();
});


/* ================================================
   DETECT DEVTOOLS OPEN (SIZE-BASED CHECK)
   ================================================ */
(function () {
  const threshold = 160;
  setInterval(function () {
    const widthDiff = window.outerWidth - window.innerWidth;
    const heightDiff = window.outerHeight - window.innerHeight;

    if (widthDiff > threshold || heightDiff > threshold) {
      console.clear();
      console.log("%cSTOP!", "color:red;font-size:40px;font-weight:bold;");
      console.log("%cDEVTOOLS ARE DISABLED.", "color:red;font-size:16px;");
      // OPTIONAL ACTION
      // window.location.reload();
    }
  }, 1000);
})();


/* ================================================
   CONSOLE TAMPERING (ANTI-CONSOLE SPAM)
   ================================================ */
(function () {
  try {
    Object.defineProperty(window, "console", {
      get: function () {
        throw new Error("CONSOLE IS DISABLED");
      }
    });
  } catch (err) {}
})();


/* ================================================
   DISABLE DEBUGGER STATEMENTS
   ================================================ */
setInterval(function () {
  debugger;
}, 500);