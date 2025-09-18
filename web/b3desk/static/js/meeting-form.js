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
