(function () {
    "use strict";

    var form = document.querySelector("[data-bulk-delete-form]");
    if (!form) {
        return;
    }

    var selectAll = form.querySelector("[data-select-all-sessions]");
    var checkboxes = Array.from(form.querySelectorAll("[data-session-checkbox]"));
    var deleteButton = form.querySelector("[data-bulk-delete-button]");

    function selectedCount() {
        return checkboxes.filter(function (checkbox) {
            return checkbox.checked;
        }).length;
    }

    function syncState() {
        var count = selectedCount();
        if (deleteButton) {
            deleteButton.disabled = count === 0;
            deleteButton.textContent = count ? "ลบ " + count + " รายการ" : "ลบรายการที่เลือก";
            if (count) {
                var icon = document.createElement("i");
                icon.className = "bi bi-trash";
                deleteButton.prepend(icon);
            }
        }
        if (selectAll) {
            selectAll.checked = count > 0 && count === checkboxes.length;
            selectAll.indeterminate = count > 0 && count < checkboxes.length;
        }
    }

    if (selectAll) {
        selectAll.addEventListener("change", function () {
            checkboxes.forEach(function (checkbox) {
                checkbox.checked = selectAll.checked;
            });
            syncState();
        });
    }

    checkboxes.forEach(function (checkbox) {
        checkbox.addEventListener("change", syncState);
    });

    form.addEventListener("submit", function (event) {
        var count = selectedCount();
        if (!count) {
            event.preventDefault();
            return;
        }
        if (!window.confirm("ยืนยันลบ " + count + " รายการที่เลือก?")) {
            event.preventDefault();
        }
    });

    syncState();
})();