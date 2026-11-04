function generatePassWord(n){
    const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    const limit = 256 - (256 % characters.length);
    const byte = new Uint8Array(1);
    let result = '';
    while (result.length < n) {
        crypto.getRandomValues(byte);
        if (byte[0] < limit) {
            result += characters[byte[0] % characters.length];
        }
    }
    return result;
}

function copyInClipboard(selector, textToCopy){
    clickedButton = document.getElementById(selector);
    navigator.clipboard.writeText(textToCopy);
    clickedButton.classList.remove("fr-icon-clipboard-line")
    clickedButton.classList.add("fr-icon-success-fill")
    previousWidth = clickedButton.getBoundingClientRect().width
    clickedButton.classList.add("justify-content-space-between")
    clickedButton.style.width = previousWidth+"px"
    setTimeout(function(clickedBtn) {
        clickedBtn.classList.remove("fr-icon-success-fill")
        clickedBtn.classList.remove("justify-content-space-between")
        clickedBtn.classList.add("fr-icon-clipboard-line")
        clickedBtn.style.width = ""
    }, 2000, clickedButton);
}
