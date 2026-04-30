document.addEventListener("DOMContentLoaded", () => {
    let buttons = document.getElementsByClassName("visio-code-button");
    for (let button of buttons){
        button.addEventListener("click", async (event) => {
            let visioCodeInput = document.getElementById(event.target.dataset.fieldName)
            const response = await fetch(window.visioCodeUrl, {
                method: "GET",
                headers: {
                    "Content-Type": "application/json"
                }
            })
            const json = await response.json();
            visioCodeInput.value = json.available_visio_code;
        });
    }
});

document.addEventListener("DOMContentLoaded", () => {
    const needConfirm = document.getElementsByClassName("need-confirm");
    const modal = document.querySelector("#delegate-confirmation");
    const form = document.getElementById("meeting-form");
    needConfirm[0].addEventListener("click", (event) => {
        event.preventDefault();
        window.dsfr(modal).modal.disclose();
    });
    const modalValidation = document.getElementsByClassName("delegate-confirm");
    modalValidation[0].addEventListener("click", (event) => {
        event.preventDefault();
        form.submit();
    });
});
