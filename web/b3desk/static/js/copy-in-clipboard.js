const copyButtons = document.querySelectorAll(".copy-button");
copyButtons.forEach((button) => {
    button.addEventListener("click", (e) => {
        text = button.dataset.copyText
        copyInClipboard(button.id, text)
    })
});
