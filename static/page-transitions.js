/* =========================================================
   Page-transition animation between landing.html <-> index.html
   Plain multi-page navigation (Flask renders full pages), so we
   fade+blur+zoom+tilt the outgoing page out in 3D, then let the
   browser navigate normally, and reverse the effect on load.

   NOTE: this file used to be named "Page transitions.js" (with a
   space and capital P), which does not match the
   url_for('static', filename='page-transitions.js') reference in
   the templates. On case-sensitive servers that meant the script
   never actually loaded. This file uses the correct name so the
   transition (and the extra 3D touch below) actually runs.
   ========================================================= */
(function () {
    "use strict";

    document.documentElement.classList.add("js-transitions");

    var EXIT_DELAY = 380; // must roughly match the CSS transition duration
    var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function reveal() {
        document.documentElement.classList.remove("page-exit");
        requestAnimationFrame(function () {
            requestAnimationFrame(function () {
                document.documentElement.classList.add("page-loaded");
            });
        });
    }

    function initPageTransitions() {
        reveal();

        document.addEventListener("click", function (e) {
            var link = e.target.closest && e.target.closest("a[href]");
            if (!link) return;

            var href = link.getAttribute("href");
            if (!href || href.charAt(0) === "#") return;
            if (link.target && link.target !== "" && link.target !== "_self") return;
            if (link.hasAttribute("download")) return;
            if (e.defaultPrevented || e.button !== 0) return;
            if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;

            var url;
            try {
                url = new URL(href, window.location.href);
            } catch (err) {
                return;
            }
            if (url.origin !== window.location.origin) return;

            e.preventDefault();
            document.documentElement.classList.remove("page-loaded");
            document.documentElement.classList.add("page-exit");
            if (!reduceMotion) document.documentElement.classList.add("page-exit-3d");
            setTimeout(function () {
                window.location.href = url.href;
            }, EXIT_DELAY);
        });

        window.addEventListener("pageshow", function (event) {
            if (event.persisted) reveal();
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initPageTransitions);
    } else {
        initPageTransitions();
    }
})();