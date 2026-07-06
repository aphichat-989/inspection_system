(function () {
        const form = document.getElementById("testing-form");
        const selectedResult = document.getElementById("selected-result");
        const saveButton = document.getElementById("save-round");
        const buttons = Array.from(document.querySelectorAll("[data-result-button]"));
        buttons.forEach((button) => {
            button.addEventListener("click", () => {
                buttons.forEach((other) => other.classList.remove("active"));
                button.classList.add("active");
                if (selectedResult) { selectedResult.value = button.dataset.resultButton; }
                if (saveButton) { saveButton.disabled = false; }
            });
        });
        if (form) {
            form.addEventListener("submit", () => {
                if (saveButton && selectedResult && selectedResult.value) { saveButton.disabled = true; }
            });
        }
    })();

