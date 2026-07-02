(function () {
    "use strict";

    function pad(value) {
        return String(value).padStart(2, "0");
    }

    function formatClock(date) {
        return (
            date.getFullYear() +
            "-" +
            pad(date.getMonth() + 1) +
            "-" +
            pad(date.getDate()) +
            " " +
            pad(date.getHours()) +
            ":" +
            pad(date.getMinutes())
        );
    }

    function updateClock() {
        var clock = document.querySelector("[data-dashboard-clock]");
        if (!clock) {
            return;
        }
        var now = new Date();
        clock.textContent = formatClock(now);
        var timeEl = clock.closest("time");
        if (timeEl) {
            timeEl.setAttribute("datetime", now.toISOString());
        }
    }

    document.addEventListener("DOMContentLoaded", function () {
        if (!document.body.classList.contains("dashboard-page")) {
            return;
        }
        updateClock();
        window.setInterval(updateClock, 30000);
    });
})();
