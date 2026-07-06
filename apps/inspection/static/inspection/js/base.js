(function initUiConfig() {
    "use strict";

    var translationsElement = document.getElementById("ui-translations");
    window.uiLanguage = document.body ? document.body.dataset.uiLanguage || "th" : "th";
    window.uiTranslations = {};
    if (!translationsElement) {
        return;
    }
    try {
        window.uiTranslations = JSON.parse(translationsElement.textContent || "{}");
    } catch (error) {
        window.uiTranslations = {};
    }
})();
window.uiTranslate = function (value) {
            const key = String(value || "").replace(/\s+/g, " ").trim();
            return window.uiTranslations[key] || value;
        };
        (function () {
            const sidebarStorageKey = "inspection.sidebar.collapsed";
            function setSidebarCollapsed(collapsed) {
                document.body.classList.toggle("sidebar-collapsed", collapsed);
                document.querySelectorAll("[data-sidebar-toggle]").forEach((button) => {
                    button.setAttribute("aria-expanded", collapsed ? "false" : "true");
                });
                localStorage.setItem(sidebarStorageKey, collapsed ? "1" : "0");
            }
            if (localStorage.getItem(sidebarStorageKey) === "1") {
                document.body.classList.add("sidebar-collapsed");
            }
            document.addEventListener("DOMContentLoaded", () => {
                document.querySelectorAll("[data-sidebar-toggle]").forEach((button) => {
                    button.setAttribute("aria-expanded", document.body.classList.contains("sidebar-collapsed") ? "false" : "true");
                    button.addEventListener("click", () => setSidebarCollapsed(!document.body.classList.contains("sidebar-collapsed")));
                });
            });
        })();
        (function () {
            const skipTags = new Set(["SCRIPT", "STYLE", "TEXTAREA", "CODE", "PRE"]);
            function translateTextNodes(root) {
                const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
                    acceptNode(node) {
                        if (!node.nodeValue || !node.nodeValue.trim()) { return NodeFilter.FILTER_REJECT; }
                        if (node.parentElement && skipTags.has(node.parentElement.tagName)) { return NodeFilter.FILTER_REJECT; }
                        return NodeFilter.FILTER_ACCEPT;
                    }
                });
                const nodes = [];
                while (walker.nextNode()) { nodes.push(walker.currentNode); }
                nodes.forEach((node) => {
                    const original = node.nodeValue;
                    const leading = original.match(/^\s*/)[0];
                    const trailing = original.match(/\s*$/)[0];
                    const normalized = original.replace(/\s+/g, " ").trim();
                    let translated = window.uiTranslations[normalized];
                    if (!translated && window.uiLanguage === "th") {
                        let match = normalized.match(/^(\d+) selected$/);
                        if (match) { translated = `เลือก ${match[1]} รายการ`; }
                        match = normalized.match(/^Round (\d+)$/);
                        if (match) { translated = `รอบที่ ${match[1]}`; }
                        match = normalized.match(/^(\d+) rounds$/);
                        if (match) { translated = `${match[1]} รอบ`; }
                        match = normalized.match(/^Defect (\d+) of (\d+)$/);
                        if (match) { translated = `ของเสีย ${match[1]} จาก ${match[2]}`; }
                    }
                    if (translated) {
                        node.nodeValue = leading + translated + trailing;
                    }
                });
            }
            function translateAttributes(root) {
                root.querySelectorAll("[placeholder], [title], [aria-label], [data-i18n]").forEach((element) => {
                    ["placeholder", "title", "aria-label"].forEach((attr) => {
                        const value = element.getAttribute(attr);
                        if (value && window.uiTranslations[value]) { element.setAttribute(attr, window.uiTranslations[value]); }
                    });
                    const key = element.getAttribute("data-i18n");
                    if (key && window.uiTranslations[key]) { element.textContent = window.uiTranslations[key]; }
                });
            }
            document.addEventListener("DOMContentLoaded", () => {
                translateTextNodes(document.body);
                translateAttributes(document.body);
            });
        })();
        (function () {
            function getCookie(name) {
                const value = `; ${document.cookie}`;
                const parts = value.split(`; ${name}=`);
                if (parts.length === 2) { return parts.pop().split(";").shift(); }
                return "";
            }
            document.addEventListener("submit", (event) => {
                const form = event.target;
                if (!form || String(form.method || "").toLowerCase() !== "post") { return; }
                const token = getCookie("csrftoken");
                const input = form.querySelector("input[name='csrfmiddlewaretoken']");
                if (token && input) { input.value = decodeURIComponent(token); }
            }, true);
        })();

