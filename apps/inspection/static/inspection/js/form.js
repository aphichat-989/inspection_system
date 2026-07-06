(function () {
        const toggles = Array.from(document.querySelectorAll("[data-defect-toggle]"));
        const roundEmpty = document.getElementById("round-empty");
        const selectedCount = document.getElementById("selected-defect-count");
        function syncDefectUi() {
            let activeCount = 0;
            toggles.forEach((toggle) => {
                const id = toggle.dataset.defectToggle;
                const card = document.querySelector(`[data-defect-card="${id}"]`);
                const row = document.querySelector(`[data-round-row="${id}"]`);
                if (card) { card.classList.toggle("active", toggle.checked); }
                if (row) { row.classList.toggle("active", toggle.checked); }
                if (toggle.checked) { activeCount += 1; }
            });
            if (roundEmpty) { roundEmpty.classList.toggle("d-none", activeCount > 0); }
            if (selectedCount) { selectedCount.textContent = window.uiTranslate ? window.uiTranslate(`${activeCount} selected`) : `${activeCount} selected`; }
        }
        toggles.forEach((toggle) => toggle.addEventListener("change", syncDefectUi));
        document.querySelectorAll(".round-step").forEach((button) => {
            button.addEventListener("click", () => {
                const input = document.getElementById(button.dataset.target);
                const step = Number(button.dataset.step || 0);
                if (!input) { return; }
                input.value = Math.max(1, Number(input.value || 1) + step);
            });
        });
        syncDefectUi();
    })();

