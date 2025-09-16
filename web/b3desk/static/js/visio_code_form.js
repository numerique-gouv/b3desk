const captchaIsNeeded = Boolean(window.visioCodeAttemptCounter > window.captchaNumberAttempt);
const inputs = document.querySelectorAll(".visio-code-container .visio-code-input-container input");
let captchaInput = null;
let captchaDescription = null;
if (captchaIsNeeded) {
    captchaInput = document.getElementById("captchaCode");
    captchaDescription = document.getElementById("captcha-description");
}

const getVisioCode = () => {
    return Array.from(inputs).map(i => i.value).join("");
}

const visioCodeIsComplete = () => {
    const visioCode = getVisioCode();
    return visioCode.match(/\d{9}$/);
}

const formIsComplete = () => {
    if (captchaIsNeeded) {
        return captchaInput.value != "" && visioCodeIsComplete();
    } else {
        return visioCodeIsComplete();
    }
}

const allowSubmitButton = (event, input) => {
    if (formIsComplete()) {
            document.getElementById("submit-visio-code").disabled = false;
            if (event.key == "Enter") {
                formValidateAndSubmit(input);
            }
        } else {
            document.getElementById("submit-visio-code").disabled = true;
        }
}

const formValidateAndSubmit = async (input) => {
    if (captchaIsNeeded) {
        if (await captchaValidation() && visioCodeIsComplete()) {
            formValidation(getVisioCode());
        } else {
            captchaDescription.innerHTML = "Captcha saisi incorrect";
        }
    } else if (visioCodeIsComplete()) {
        formValidation(getVisioCode());
    } else {
        visualValidation(input);
    }
}

const focusAtEnd = (input) => {
    input.focus();
    input.selectionStart = 3;
    input.selectionEnd = 3;
}
const formValidation = (visioCode) => {
    document.getElementById("visio-code").value = visioCode;
    if (captchaIsNeeded) {
        document.getElementById("captcha-uuid").value = document.getElementById('captchetat-uuid').value,
        document.getElementById("captcha-code").value = document.getElementById('captchaCode').value
    }
    document.getElementById("visio-code-form").submit();
}

const moveToNextInputIfNeeded = (target) => {
    const isAtEnd = target.selectionStart == target.value.length && target.value.length == target.selectionEnd;
    const nextSibling = target.parentElement.nextElementSibling;
    if (nextSibling && nextSibling.children) {
        const nextSiblingChild = nextSibling.children[0];
        const nextSiblingInput = nextSiblingChild && nextSiblingChild.nodeName === "INPUT";
        if (nextSiblingInput && isAtEnd) {
            nextSiblingChild.focus();
            nextSiblingChild.selectionStart = 0;
            nextSiblingChild.selectionEnd = 0;
        }
    }
}

const moveToPreviousInputIfNeeded = (target) => {
    const isAtBeginning = target.selectionStart == 0 && target.selectionEnd == 0;
    const previousSibling = target.previousElementSibling;
    const previousSiblingInput = previousSibling && target.previousElementSibling.nodeName === "INPUT";
    if (isAtBeginning && previousSiblingInput) {
        focusAtEnd(previousSibling);
    }
}

const visualValidation = (target) => {
    parent = target.parentElement;
    if (target.value == "") {
        parent.classList.remove("fr-input-group--valid")
        parent.classList.remove("fr-input-group--error")
    } else if (!target.value.match(/\d{3}$/) && !parent.classList.contains("fr-input-group--error")) {
        parent.classList.remove("fr-input-group--valid")
        parent.classList.add("fr-input-group--error")
    } else if (target.value.match(/\d{3}$/) && !parent.classList.contains("fr-input-group--valid")) {
        parent.classList.remove("fr-input-group--error")
        parent.classList.add("fr-input-group--valid")
    }
}

if (captchaIsNeeded) {
    captchaInput.addEventListener("keyup", (event) => {
        allowSubmitButton(event, captchaInput)
})
}

inputs.forEach((input) => {
    visualValidation(input);
    input.addEventListener("keyup", (event) => {
        if (input.value.length >= 3 && event.key.length == 1) {
            moveToNextInputIfNeeded(input);
        }
        if (event.key == "Backspace" || event.key == "ArrowLeft") {
            moveToPreviousInputIfNeeded(input);
        } else if (event.key == "ArrowRight") {
            moveToNextInputIfNeeded(input);
        }
        visualValidation(input);
        allowSubmitButton(event, input)
    })
    input.addEventListener('paste', (event) => {
        event.preventDefault()
        const pasteData = (event.clipboardData || window.clipboardData).getData('text');
        const chars = [pasteData.slice(0,3), pasteData.slice(3,6), pasteData.slice(6,9)];
        inputs.forEach((pastedInput, index) => {
            pastedInput.value = chars[index];
            visualValidation(pastedInput);
            if (pasteData.length <= 3 && index == 0) {
                focusAtEnd(pastedInput);
            } else if (pasteData.length > 3 && pasteData.length <= 6 && index == 1) {
                focusAtEnd(pastedInput);
            } else if (pasteData.length > 6 && index == 2) {
                focusAtEnd(pastedInput);
            }
        })
    });
})

const captchaValidation = async () => {
    let csrf_token = document.getElementsByName("csrf_token")[0].value;
    let captchaValidationResponse = false;
    const postData = {
        uuid: document.getElementById('captchetat-uuid').value,
        code: document.getElementById('captchaCode').value
    };
    try {
        const response = await fetch(window.captchaValidationUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json; charset=utf-8',
                'X-CSRFToken':csrf_token
            },
            body: JSON.stringify(postData)
        });
        const data = await response.json();
        if (data.success === false) {
            window.captchetatComponentModule.refreshCaptcha();
            captchaValidationResponse = false;
        } else {
            captchaValidationResponse = true;
        }
    } catch (error) {
        console.error('Erreur lors de la requête CAPTCHA :', error);
    }
    return captchaValidationResponse;
}
