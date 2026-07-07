/* MAD-1 Prep — app.js
   Adds: dark mode toggle, study progress tracking, collapsible Q&A (active recall),
   reading progress bar, arrow-key page navigation, back-to-top.
   Everything stores in localStorage — no server, works offline. */

(function () {
    "use strict";
    document.documentElement.classList.add("js");

    var THEME_KEY = "mad1-theme";
    var PROGRESS_KEY = "mad1-progress";

    function pageId() {
        var base = location.pathname.split("/").pop() || "index.html";
        return base.replace(/\.html$/, "") || "index";
    }

    function getProgress() {
        try { return JSON.parse(localStorage.getItem(PROGRESS_KEY)) || {}; }
        catch (e) { return {}; }
    }
    function saveProgress(p) { localStorage.setItem(PROGRESS_KEY, JSON.stringify(p)); }

    document.addEventListener("DOMContentLoaded", function () {
        var nav = document.querySelector(".topnav");
        var wrap = document.querySelector(".wrap");

        /* ---- 1. theme toggle ---- */
        if (nav) {
            var btn = document.createElement("button");
            btn.className = "theme-btn";
            btn.type = "button";
            var setLabel = function () {
                var dark = document.documentElement.getAttribute("data-theme") === "dark";
                btn.textContent = dark ? "☀️ Light" : "🌙 Dark";
                btn.setAttribute("aria-label", dark ? "Switch to light mode" : "Switch to dark mode");
            };
            btn.addEventListener("click", function () {
                var dark = document.documentElement.getAttribute("data-theme") === "dark";
                var next = dark ? "light" : "dark";
                document.documentElement.setAttribute("data-theme", next);
                localStorage.setItem(THEME_KEY, next);
                setLabel();
            });
            setLabel();
            nav.appendChild(btn);
        }

        /* ---- 2. reading progress bar ---- */
        var bar = document.createElement("div");
        bar.id = "reading-bar";
        document.body.appendChild(bar);
        var onScroll = function () {
            var h = document.documentElement;
            var max = h.scrollHeight - h.clientHeight;
            bar.style.width = (max > 0 ? (h.scrollTop / max) * 100 : 0) + "%";
        };
        window.addEventListener("scroll", onScroll, { passive: true });
        onScroll();

        /* ---- 3. collapsible Q&A (click question to reveal answer) ---- */
        var qas = document.querySelectorAll(".qa");
        if (qas.length) {
            qas.forEach(function (qa) {
                var q = qa.querySelector(".q");
                if (!q) { qa.classList.add("open"); return; }
                q.addEventListener("click", function () { qa.classList.toggle("open"); });
            });
            if (qas.length >= 3 && wrap) {
                var reveal = document.createElement("button");
                reveal.className = "reveal-btn";
                reveal.type = "button";
                var allOpen = false;
                var setRevealLabel = function () {
                    reveal.textContent = allOpen ? "Hide all answers (quiz me)" : "Show all answers";
                };
                reveal.addEventListener("click", function () {
                    allOpen = !allOpen;
                    qas.forEach(function (qa) { qa.classList.toggle("open", allOpen); });
                    setRevealLabel();
                });
                setRevealLabel();
                var firstQa = document.querySelector(".qa");
                firstQa.parentNode.insertBefore(reveal, firstQa);
            }
        }

        /* ---- 4. study progress ---- */
        var id = pageId();
        var progress = getProgress();

        if (id === "index") {
            // decorate lesson list + overall progress bar
            var links = document.querySelectorAll(".lesson-list li");
            var total = 0, done = 0;
            links.forEach(function (li) {
                var a = li.querySelector("a");
                if (!a) return;
                total++;
                var lid = (a.getAttribute("href") || "").replace(/\.html$/, "");
                if (progress[lid]) { li.classList.add("done"); done++; }
            });
            if (total && wrap) {
                var box = document.createElement("div");
                var pct = Math.round((done / total) * 100);
                box.innerHTML =
                    '<div class="progress-track"><div class="progress-fill"></div></div>' +
                    '<p class="progress-label">' +
                    (done === 0
                        ? "Start Lesson 0 — your progress is saved automatically on this device."
                        : done === total
                            ? "🎉 All " + total + " pages done. You are ready. Go pass that viva."
                            : "📚 " + done + " / " + total + " pages done (" + pct + "%) — keep the streak going!") +
                    "</p>";
                var h1 = wrap.querySelector("h1");
                h1.parentNode.insertBefore(box, h1.nextSibling);
                requestAnimationFrame(function () {
                    box.querySelector(".progress-fill").style.width = pct + "%";
                });
            }
        } else if (wrap) {
            // mark-done button on every content page
            var mark = document.createElement("button");
            mark.className = "mark-done-btn";
            mark.type = "button";
            var setMark = function () {
                var d = !!progress[id];
                mark.classList.toggle("is-done", d);
                mark.textContent = d ? "✓ Completed — click to undo" : "Mark this page complete ✓";
            };
            mark.addEventListener("click", function () {
                progress = getProgress();
                if (progress[id]) { delete progress[id]; } else {
                    progress[id] = true;
                    mark.textContent = "🎉 Nice! Saved.";
                    setTimeout(setMark, 900);
                }
                saveProgress(progress);
                if (progress[id] === undefined) setMark();
            });
            setMark();
            var pager = wrap.querySelector(".pager");
            if (pager) { wrap.insertBefore(mark, pager); } else { wrap.appendChild(mark); }
        }

        /* ---- 5. arrow keys follow the pager ---- */
        document.addEventListener("keydown", function (e) {
            if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
            var pager = document.querySelector(".pager");
            if (!pager) return;
            var links = pager.querySelectorAll("a");
            var prev = null, next = null;
            links.forEach(function (a) {
                var t = a.textContent;
                if (t.indexOf("←") !== -1) prev = a;
                if (t.indexOf("→") !== -1) next = a;
            });
            if (e.key === "ArrowRight" && next) location.href = next.getAttribute("href");
            if (e.key === "ArrowLeft" && prev) location.href = prev.getAttribute("href");
        });

        /* ---- 6. back to top ---- */
        var top = document.createElement("button");
        top.className = "backtop";
        top.type = "button";
        top.textContent = "↑";
        top.setAttribute("aria-label", "Back to top");
        top.addEventListener("click", function () { window.scrollTo({ top: 0, behavior: "smooth" }); });
        document.body.appendChild(top);
        window.addEventListener("scroll", function () {
            top.classList.toggle("show", window.scrollY > 500);
        }, { passive: true });

        /* ---- 7. desktop-app extras (only when served by the MAD1-Prep launcher) ---- */
        if (location.protocol === "http:") {
            fetch("/_ping", { cache: "no-store" }).then(function (r) {
                if (r.ok && nav) {
                    var gear = document.createElement("a");
                    gear.href = "/_settings";
                    gear.textContent = "⚙️ App settings";
                    nav.insertBefore(gear, nav.querySelector(".theme-btn"));
                }
            }).catch(function () { /* not the launcher — ignore */ });
        }
    });
})();
