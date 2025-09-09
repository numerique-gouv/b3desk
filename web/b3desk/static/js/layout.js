function generatePassWord(n){
    var result = '';
    var characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    var charactersLength = characters.length;
    for ( var i = 0; i < n; i++ ) {
        result += characters.charAt(Math.floor(Math.random() * charactersLength));
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
