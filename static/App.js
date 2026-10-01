(function () {
    "use strict";

    /* =========================================================
       i18n dictionary — only the app's own chrome text.
       The agent's answer (LLM output) is never translated here;
       it stays in whatever language the user asked in.
       ========================================================= */
    var I18N = {
        en: {
            loading: "Preparing your journey&hellip;",
            backLanding: "&larr; Home",
            brandTitle: "Agentic Travel Assistant",
            brandTagline: "Give the AI a travel goal. The agent decides which tools it needs, executes them, observes the results, and continues until it can answer.",
            themeBoard: "Night board",
            themeParchment: "Parchment",
            toolkitTitle: "Quick Currency Converter",
            convSwap: "Swap",
            convButton: "Convert",
            goalTitle: "Your Travel Goal",
            goalPlaceholder: "Example: I am traveling to Istanbul for 5 days with 500 JOD. Check the weather, convert my money to TRY, and calculate my daily budget.",
            modeTabNew: "New Trip",
            modeTabEdit: "Edit Current Trip",
            editChip1: "+ Change a day",
            editChip2: "+ Adjust budget",
            editChip3: "+ Remove activity",
            editChip4: "+ Move dates",
            words: "words",
            runButton: "Run Travel Agent",
            readinessTitle: "Trip Readiness",
            readinessComplete: "complete",
            readinessMissing: "Still needed:",
            stateTitle: "Agent State",
            stateGoal: "Goal",
            stateStatus: "Status",
            stateIterations: "Iterations",
            stateToolsUsed: "Tools Used",
            traceTitle: "Agent Execution Trace",
            planTitle: "Your Travel Plan",
            print: "Print",
            text: "Text",
            mapTitle: "Places on the Map",
            copyPlan: "Copy"
        },
        ar: {
            loading: "نجهزو رحلتك&hellip;",
            backLanding: "الرئيسية &rarr;",
            brandTitle: "المساعد الذكي للسفر",
            brandTagline: "عطي للذكاء الاصطناعي هدف السفر تاعك. الوكيل يقرر شنو الأدوات لي يحتاجها، يستعملها، يراقب النتائج، ويكمل حتى يجاوبك.",
            themeBoard: "وضع الليل",
            themeParchment: "وضع الرقّ",
            toolkitTitle: "محول عملات سريع",
            convSwap: "بدّل",
            convButton: "حوّل",
            goalTitle: "هدف رحلتك",
            goalPlaceholder: "مثال: راني مسافر لإسطنبول لمدة 5 أيام بميزانية 500 دينار أردني. تحقق من الطقس، حوّل فلوسي لليرة التركية، واحسب الميزانية اليومية.",
            modeTabNew: "رحلة جديدة",
            modeTabEdit: "عدّل الرحلة الحالية",
            editChip1: "+ بدّل يوم",
            editChip2: "+ عدّل الميزانية",
            editChip3: "+ احذف نشاط",
            editChip4: "+ بدّل التواريخ",
            words: "كلمة",
            runButton: "شغّل وكيل السفر",
            readinessTitle: "جاهزية الرحلة",
            readinessComplete: "مكتمل",
            readinessMissing: "لازال ناقص:",
            stateTitle: "حالة الوكيل",
            stateGoal: "الهدف",
            stateStatus: "الحالة",
            stateIterations: "عدد الدورات",
            stateToolsUsed: "الأدوات المستعملة",
            traceTitle: "مسار تنفيذ الوكيل",
            planTitle: "خطة رحلتك",
            print: "طباعة",
            text: "نص",
            mapTitle: "الأماكن على الخريطة",
            copyPlan: "نسخ"
        }
    };

    var STORAGE_THEME = "tavel_theme";
    var STORAGE_LANG = "tavel_lang";

    /* ---------------- Theme toggle (Night board / Parchment) ---------------- */
    function initTheme() {
        var root = document.documentElement;
        var saved = localStorage.getItem(STORAGE_THEME);
        var initial = saved || "parchment";
        root.setAttribute("data-theme", initial);

        var btn = document.getElementById("theme-toggle");
        if (!btn) return;

        function updateLabel() {
            var lang = localStorage.getItem(STORAGE_LANG) || "en";
            var current = root.getAttribute("data-theme");
            var dict = I18N[lang];
            var labelSpan = btn.querySelector("span[data-i18n]");
            if (labelSpan) {
                labelSpan.setAttribute("data-i18n", current === "board" ? "themeParchment" : "themeBoard");
                labelSpan.textContent = current === "board" ? dict.themeParchment : dict.themeBoard;
            }
        }

        updateLabel();

        btn.addEventListener("click", function () {
            var current = root.getAttribute("data-theme");
            var next = current === "board" ? "parchment" : "board";
            root.setAttribute("data-theme", next);
            localStorage.setItem(STORAGE_THEME, next);
            updateLabel();
        });
    }

    /* ---------------- Language toggle (EN / AR) ---------------- */
    function applyLanguage(lang) {
        var dict = I18N[lang] || I18N.en;
        document.documentElement.setAttribute("lang", lang);
        document.documentElement.setAttribute("dir", lang === "ar" ? "rtl" : "ltr");

        document.querySelectorAll("[data-i18n]").forEach(function (el) {
            var key = el.getAttribute("data-i18n");
            if (dict[key]) el.innerHTML = dict[key];
        });

        document.querySelectorAll("[data-i18n-placeholder]").forEach(function (el) {
            var key = el.getAttribute("data-i18n-placeholder");
            if (dict[key]) el.setAttribute("placeholder", dict[key]);
        });

        var langLabel = document.getElementById("lang-toggle-label");
        if (langLabel) langLabel.textContent = lang === "ar" ? "English" : "العربية";
    }

    function initLanguage() {
        var saved = localStorage.getItem(STORAGE_LANG) || "en";
        applyLanguage(saved);

        var btn = document.getElementById("lang-toggle");
        if (!btn) return;

        btn.addEventListener("click", function () {
            var current = localStorage.getItem(STORAGE_LANG) || "en";
            var next = current === "en" ? "ar" : "en";
            localStorage.setItem(STORAGE_LANG, next);
            applyLanguage(next);

            // update theme-toggle label text (depends on language dict)
            var themeBtn = document.getElementById("theme-toggle");
            if (themeBtn) {
                var root = document.documentElement;
                var themeCurrent = root.getAttribute("data-theme");
                var labelSpan = themeBtn.querySelector("span[data-i18n]");
                if (labelSpan) {
                    labelSpan.textContent = themeCurrent === "board"
                        ? I18N[next].themeParchment
                        : I18N[next].themeBoard;
                }
            }

            window.dispatchEvent(new CustomEvent("tavel:langchange", { detail: { lang: next } }));
        });
    }

    /* ---------------- Loading state on the submit button ---------------- */
    function initFormLoading() {
        var form = document.getElementById("goal-form");
        var runBtn = document.getElementById("run-btn");
        if (!form || !runBtn) return;

        form.addEventListener("submit", function () {
            if (!form.checkValidity()) return;
            runBtn.classList.add("is-loading");
        });
    }

    /* ---------------- Readiness bar: animated fill + count-up ---------------- */
    function initReadinessBar() {
        var fill = document.getElementById("readiness-bar-fill");
        var numberEl = document.getElementById("readiness-pct-number");
        if (!fill) return;

        var target = parseInt(fill.getAttribute("data-target-pct"), 10) || 0;

        requestAnimationFrame(function () {
            setTimeout(function () {
                fill.style.width = target + "%";
            }, 150);
        });

        if (!numberEl) return;
        var start = 0;
        var duration = 900;
        var startTime = null;

        function step(timestamp) {
            if (!startTime) startTime = timestamp;
            var progress = Math.min((timestamp - startTime) / duration, 1);
            var eased = 1 - Math.pow(1 - progress, 3);
            numberEl.textContent = Math.round(start + (target - start) * eased);
            if (progress < 1) requestAnimationFrame(step);
        }
        setTimeout(function () { requestAnimationFrame(step); }, 150);
    }

    /* ---------------- Scroll-to-top floating button ---------------- */
    function initScrollTop() {
        var btn = document.createElement("button");
        btn.type = "button";
        btn.id = "scroll-top-btn";
        btn.className = "scroll-top-btn no-print";
        btn.setAttribute("aria-label", "Scroll to top");
        btn.innerHTML = "&#8593;";
        document.body.appendChild(btn);

        function toggle() {
            if (window.scrollY > 420) {
                btn.classList.add("visible");
            } else {
                btn.classList.remove("visible");
            }
        }

        window.addEventListener("scroll", toggle, { passive: true });
        toggle();

        btn.addEventListener("click", function () {
            window.scrollTo({ top: 0, behavior: "smooth" });
        });
    }

    /* ---------------- Copy plan to clipboard ---------------- */
    function initCopyAnswer() {
        var btn = document.getElementById("copy-answer-btn");
        var dataEl = document.getElementById("agent-answer-data");
        if (!btn || !dataEl) return;

        btn.addEventListener("click", function () {
            var raw;
            try {
                raw = JSON.parse(dataEl.textContent);
            } catch (e) {
                raw = dataEl.textContent;
            }
            var label = btn.querySelector("span");
            navigator.clipboard.writeText(raw).then(function () {
                var original = label ? label.textContent : btn.textContent;
                if (label) label.textContent = "Copied!"; else btn.textContent = "Copied!";
                btn.classList.add("copied");
                setTimeout(function () {
                    if (label) label.textContent = original; else btn.textContent = original;
                    btn.classList.remove("copied");
                }, 1600);
            }).catch(function () { /* clipboard unavailable, ignore */ });
        });
    }

    /* ---------------- Word counter for the goal textarea ---------------- */
    function initWordCount() {
        var textarea = document.getElementById("goal-textarea");
        var counter = document.getElementById("word-count");
        if (!textarea || !counter) return;

        function update() {
            var words = textarea.value.trim().split(/\s+/).filter(Boolean);
            var lang = localStorage.getItem(STORAGE_LANG) || "en";
            var label = I18N[lang].words;
            counter.textContent = words.length + " " + label;
        }

        textarea.addEventListener("input", update);
        update();
    }

    /* ---------------- Voice input (Web Speech API, feature-detected) ---------------- */
    function initVoiceInput() {
        var micBtn = document.getElementById("mic-btn");
        var textarea = document.getElementById("goal-textarea");
        if (!micBtn || !textarea) return;

        var SpeechRecognitionCtor = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognitionCtor) return; // not supported -> keep button hidden

        micBtn.hidden = false;

        var recognition = new SpeechRecognitionCtor();
        recognition.continuous = false;
        recognition.interimResults = false;

        var listening = false;

        micBtn.addEventListener("click", function () {
            if (listening) return;

            var lang = localStorage.getItem(STORAGE_LANG) || "en";
            recognition.lang = lang === "ar" ? "ar-SA" : "en-US";

            try {
                recognition.start();
                listening = true;
                micBtn.classList.add("mic-active");
            } catch (e) {
                /* recognition may already be running; ignore */
            }
        });

        recognition.addEventListener("result", function (event) {
            var transcript = event.results[0][0].transcript;
            textarea.value = (textarea.value ? textarea.value + " " : "") + transcript;
            textarea.dispatchEvent(new Event("input"));
        });

        recognition.addEventListener("end", function () {
            listening = false;
            micBtn.classList.remove("mic-active");
        });

        recognition.addEventListener("error", function () {
            listening = false;
            micBtn.classList.remove("mic-active");
        });
    }

    /* ---------------- Confetti burst on a successful plan ---------------- */
    function initConfetti() {
        var trigger = document.getElementById("confetti-trigger");
        if (!trigger || typeof confetti !== "function") return;

        confetti({
            particleCount: 90,
            spread: 70,
            startVelocity: 35,
            origin: { y: 0.3 },
            colors: ["#F0C862", "#8A1F11", "#3E6B3A", "#EFE3C8"]
        });
    }

    /* ---------------- Currency converter widget ---------------- */
    function initConverter() {
        var amountEl = document.getElementById("conv-amount");
        var fromEl = document.getElementById("conv-from");
        var toEl = document.getElementById("conv-to");
        var runBtn = document.getElementById("conv-run");
        var swapBtn = document.getElementById("conv-swap");
        var resultEl = document.getElementById("conv-result");

        if (!amountEl || !runBtn) return;

        function run() {
            var amount = parseFloat(amountEl.value);
            if (isNaN(amount) || amount < 0) {
                resultEl.textContent = "Please enter a valid amount.";
                resultEl.className = "converter-result status-fail";
                return;
            }

            runBtn.disabled = true;
            resultEl.textContent = "Converting...";
            resultEl.className = "converter-result";

            fetch("/api/convert", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    amount: amount,
                    from_currency: fromEl.value,
                    to_currency: toEl.value
                })
            }).then(function (res) { return res.json(); })
              .then(function (data) {
                  runBtn.disabled = false;
                  if (data.success) {
                      resultEl.textContent =
                          amount + " " + fromEl.value + " = " +
                          data.converted_amount + " " + toEl.value +
                          " (rate " + data.rate + ")";
                      resultEl.className = "converter-result status-ok";
                  } else {
                      resultEl.textContent = data.error || "Conversion failed.";
                      resultEl.className = "converter-result status-fail";
                  }
              }).catch(function () {
                  runBtn.disabled = false;
                  resultEl.textContent = "Network error. Please try again.";
                  resultEl.className = "converter-result status-fail";
              });
        }

        runBtn.addEventListener("click", run);

        if (swapBtn) {
            swapBtn.addEventListener("click", function () {
                var tmp = fromEl.value;
                fromEl.value = toEl.value;
                toEl.value = tmp;
            });
        }
    }

    /* ---------------- Trip map (Leaflet, fed by real search_places results) ---------------- */
    function initMap() {
        var mapEl = document.getElementById("trip-map");
        var dataEl = document.getElementById("map-data");
        if (!mapEl || !dataEl || typeof L === "undefined") return;

        var places;
        try {
            places = JSON.parse(dataEl.textContent);
        } catch (e) {
            return;
        }

        if (!places || !places.length) return;

        var map = L.map(mapEl, { scrollWheelZoom: false });
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: "&copy; OpenStreetMap contributors",
            maxZoom: 19
        }).addTo(map);

        // Custom "fantasy pin" divIcon so real places drop onto the map
        // with a little life instead of the plain default Leaflet marker.
        var fantasyIcon = L.divIcon({
            className: "",
            html: '<div class="fantasy-pin"></div>',
            iconSize: [26, 26],
            iconAnchor: [13, 26],
            popupAnchor: [0, -24]
        });

        var bounds = [];
        var latlngs = [];
        places.forEach(function (place, index) {
            var marker = L.marker([place.lat, place.lon], { icon: fantasyIcon }).addTo(map);
            marker.bindPopup(
                "<strong>" + place.name + "</strong>" +
                (place.address ? "<br>" + place.address : "") +
                (place.category ? "<br><em>" + place.category + "</em>" : "")
            );
            // Stagger the drop-in animation slightly per marker.
            var el = marker.getElement && marker.getElement();
            if (el) {
                var pin = el.querySelector(".fantasy-pin");
                if (pin) pin.style.animationDelay = (index * 90) + "ms, " + (600 + index * 90) + "ms";
            }
            bounds.push([place.lat, place.lon]);
            latlngs.push([place.lat, place.lon]);
        });

        // Real route line connecting the actual places, in visit order,
        // with a subtle animated dash so the trip reads as a journey.
        if (latlngs.length > 1) {
            L.polyline(latlngs, {
                color: "#23A97E",
                weight: 3,
                opacity: 0.8,
                dashArray: "8 6",
                className: "leaflet-route-line"
            }).addTo(map);
        }

        if (bounds.length === 1) {
            map.setView(bounds[0], 14);
        } else {
            map.fitBounds(bounds, { padding: [30, 30] });
        }
    }

    /* ---------------- 3D tilt-on-hover for cards ---------------- */
    function initTiltCards() {
        if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
        if (window.matchMedia("(pointer: coarse)").matches) return; // skip on touch

        var selector = ".card, .pass-card, .gate-step, .step-card, .trace-section, .boarding-card, .map-card";
        var cards = document.querySelectorAll(selector);

        cards.forEach(function (card) {
            var maxTilt = 6; // degrees, kept subtle so text stays readable

            card.addEventListener("mousemove", function (e) {
                var rect = card.getBoundingClientRect();
                var x = (e.clientX - rect.left) / rect.width;
                var y = (e.clientY - rect.top) / rect.height;
                var rotateY = (x - 0.5) * maxTilt * 2;
                var rotateX = (0.5 - y) * maxTilt * 2;
                card.style.transform =
                    "perspective(1200px) rotateX(" + rotateX.toFixed(2) + "deg) " +
                    "rotateY(" + rotateY.toFixed(2) + "deg) translateZ(6px)";
                card.classList.add("tilt-active");
            });

            card.addEventListener("mouseleave", function () {
                card.style.transform = "";
                card.classList.remove("tilt-active");
            });
        });
    }

    /* ---------------- Scroll reveal: cards fly in from 3D space ---------------- */
    function initScrollReveal() {
        var selector = ".card, .pass-card, .gate-step, .step-card, .trace-section, .boarding-card, .map-card";
        var targets = document.querySelectorAll(selector);
        if (!targets.length) return;

        targets.forEach(function (el) { el.classList.add("reveal-3d"); });

        if (typeof IntersectionObserver === "undefined") {
            targets.forEach(function (el) { el.classList.add("in-view"); });
            return;
        }

        var observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add("in-view");
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });

        targets.forEach(function (el) { observer.observe(el); });
    }

    /* ---------------- Fantasy sky: floating clouds, stars, a passing plane ---------------- */
    function initFantasySky() {
        if (document.getElementById("fantasy-sky")) return;
        if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

        var sky = document.createElement("div");
        sky.id = "fantasy-sky";
        sky.className = "fantasy-sky no-print";
        sky.setAttribute("aria-hidden", "true");

        var cloudSvg = '<svg viewBox="0 0 120 60" xmlns="http://www.w3.org/2000/svg" fill="currentColor">' +
            '<ellipse cx="30" cy="40" rx="26" ry="16"/><ellipse cx="60" cy="30" rx="32" ry="20"/>' +
            '<ellipse cx="90" cy="42" rx="24" ry="14"/></svg>';

        var cloudDefs = [
            { top: "8%",  size: 120, dur: "70s", delay: "0s",   color: "#ffffff" },
            { top: "18%", size: 90,  dur: "95s", delay: "-20s", color: "#ffffff" },
            { top: "4%",  size: 70,  dur: "60s", delay: "-45s", color: "#ffffff" }
        ];

        cloudDefs.forEach(function (def) {
            var cloud = document.createElement("div");
            cloud.className = "fantasy-cloud";
            cloud.style.top = def.top;
            cloud.style.width = def.size + "px";
            cloud.style.height = (def.size * 0.5) + "px";
            cloud.style.color = def.color;
            cloud.style.animationDuration = def.dur;
            cloud.style.animationDelay = def.delay;
            cloud.innerHTML = cloudSvg;
            sky.appendChild(cloud);
        });

        for (var i = 0; i < 22; i++) {
            var star = document.createElement("div");
            star.className = "fantasy-star";
            star.style.left = Math.random() * 100 + "%";
            star.style.top = Math.random() * 60 + "%";
            star.style.animationDelay = (Math.random() * 3).toFixed(2) + "s";
            sky.appendChild(star);
        }

        var plane = document.createElement("div");
        plane.className = "fantasy-plane";
        plane.style.animationDelay = "-8s";
        plane.innerHTML = '<svg viewBox="0 0 24 24" fill="currentColor">' +
            '<path d="M2.5 14.5l7-2 3-6.7c.3-.6 1.2-.6 1.5 0l1 2.2 4-1.1a1 1 0 011.2 1.3l-1.5 3.7 3 1.6c.7.4.5 1.4-.3 1.5l-4.3.6-1.8 4.6c-.2.6-1 .6-1.3.1l-1.8-3.5-6.7 1.6z"/></svg>';
        sky.appendChild(plane);

        document.body.insertBefore(sky, document.body.firstChild);
    }

    /* ---------------- Edit-goal box: modify the existing trip instead of starting over ---------------- */
    function initEditMode() {
        var form = document.getElementById("goal-form");
        var textarea = document.getElementById("goal-textarea");
        var newTab = document.getElementById("mode-tab-new");
        var editTab = document.getElementById("mode-tab-edit");
        var hint = document.getElementById("edit-mode-hint");
        var chipRow = document.getElementById("edit-chip-row");
        var runBtnLabel = document.querySelector("#run-btn [data-i18n='runButton']");
        if (!form || !textarea || !newTab || !editTab) return;

        var hasExistingPlan = editTab.getAttribute("data-has-plan") === "1";
        var STORAGE_MODE = "tavel_edit_mode";
        var lang = localStorage.getItem(STORAGE_LANG) || "en";

        var LABELS = {
            en: {
                newPlaceholder: "Example: I am traveling to Istanbul for 5 days with 500 JOD. Check the weather, convert my money to TRY, and calculate my daily budget.",
                editPlaceholder: "Example: Change day 2 to include more museums, or move my budget to 600 JOD.",
                hint: "This updates your current trip instead of starting a new one — the agent keeps everything else as-is.",
                run: "Run Travel Agent",
                update: "Update Plan"
            },
            ar: {
                newPlaceholder: "مثال: راني مسافر لإسطنبول لمدة 5 أيام بميزانية 500 دينار أردني. تحقق من الطقس، حوّل فلوسي لليرة التركية، واحسب الميزانية اليومية.",
                editPlaceholder: "مثال: بدّل اليوم 2 وزيد متاحف، أو بدّل الميزانية لـ 600 دينار.",
                hint: "هاذ التعديل يبدّل فالرحلة الحالية متاعك، ما يبدأش رحلة جديدة من الصفر — باقي كل شيء آخر كيما هو.",
                run: "شغّل وكيل السفر",
                update: "حدّث الخطة"
            }
        };

        function applyMode(mode, focus) {
            localStorage.setItem(STORAGE_MODE, mode);
            var dict = LABELS[lang] || LABELS.en;
            var isEdit = mode === "edit" && hasExistingPlan;

            newTab.classList.toggle("active", !isEdit);
            editTab.classList.toggle("active", isEdit);
            form.setAttribute("data-mode", isEdit ? "edit" : "new");

            if (hint) hint.classList.toggle("is-visible", isEdit);
            if (hint) hint.textContent = dict.hint;
            if (chipRow) chipRow.classList.toggle("is-visible", isEdit);

            textarea.setAttribute("placeholder", isEdit ? dict.editPlaceholder : dict.newPlaceholder);
            if (runBtnLabel) runBtnLabel.textContent = isEdit ? dict.update : dict.run;

            if (focus && isEdit) {
                textarea.value = "";
                textarea.dispatchEvent(new Event("input"));
                textarea.focus();
            }
        }

        newTab.addEventListener("click", function () { applyMode("new", true); });
        editTab.addEventListener("click", function () {
            if (!hasExistingPlan) return;
            applyMode("edit", true);
        });

        if (chipRow) {
            chipRow.querySelectorAll(".edit-chip").forEach(function (chip) {
                chip.addEventListener("click", function () {
                    var text = chip.getAttribute("data-text") || chip.textContent;
                    textarea.value = (textarea.value ? textarea.value.trim() + " " : "") + text;
                    textarea.dispatchEvent(new Event("input"));
                    textarea.focus();
                });
            });
        }

        // On submit in edit mode, make sure the intent to modify the
        // existing plan (rather than build a new one) is explicit for
        // the agent — the backend already sends the saved itinerary as
        // context, this just phrases the request so it's used.
        form.addEventListener("submit", function () {
            var isEdit = form.getAttribute("data-mode") === "edit";
            if (!isEdit) return;
            var value = textarea.value.trim();
            var lower = value.toLowerCase();
            if (value && lower.indexOf("existing") === -1 && lower.indexOf("current trip") === -1) {
                textarea.value = "Update my existing trip plan (do not start a new one from scratch): " + value;
            }
        });

        var savedMode = hasExistingPlan ? (localStorage.getItem(STORAGE_MODE) || "new") : "new";
        applyMode(savedMode, false);

        window.addEventListener("tavel:langchange", function (e) {
            lang = (e.detail && e.detail.lang) || lang;
            applyMode(form.getAttribute("data-mode") === "edit" ? "edit" : "new", false);
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        initTheme();
        initLanguage();
        initFormLoading();
        initWordCount();
        initVoiceInput();
        initConfetti();
        initConverter();
        initMap();
        initReadinessBar();
        initScrollTop();
        initCopyAnswer();
        initEditMode();
        initFantasySky();
        initTiltCards();
        initScrollReveal();
    });
})();