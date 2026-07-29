const selectAllCheckbox = document.getElementById("select-all-users");
const selectAllScope = document.getElementById("select-all-scope");
const memberCheckboxes = document.querySelectorAll('input[name="user_ids"]');

const restrictSelectionToCheckedRows = () => {
    if (selectAllScope) {
        selectAllScope.remove();
    }
    if (selectAllCheckbox) {
        selectAllCheckbox.checked = false;
    }
}

memberCheckboxes.forEach((checkbox) => {
    checkbox.addEventListener("change", () => {
        if (!checkbox.checked) {
            restrictSelectionToCheckedRows();
        }
    })
})
