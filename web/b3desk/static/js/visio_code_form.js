const inputs = document.querySelectorAll(".visio-code-container .visio-code-input-container input");


let captchaInput = null;
let captchaDescription = null;
if (window.shouldDisplayCaptcha) {
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
    if (window.shouldDisplayCaptcha) {
        return captchaInput.value != "" && visioCodeIsComplete();
    } else {
        return visioCodeIsComplete();
    }
}

const formIsValid = async () => {
    var valid = true;
    var formData = new FormData(document.getElementById("visio-code-form"));
    const response = await fetch(window.visioCodeFormValidationUrl, {
        method: "POST",
        body: formData,
    })
    const data = await response.json();

    if ("visioCode" in data) {
        var existingError = document.getElementById("visioCodeError");
        if (existingError) {
            existingError.remove();
        }

        if (data.visioCode) {
            inputs.forEach((input) => {
                var parent = input.parentElement;
                parent.classList.add("fr-input-group--valid")
                parent.classList.remove("fr-input-group--error")
            })
        }
        else {
            inputs.forEach((input) => {
                var parent = input.parentElement;
                parent.classList.remove("fr-input-group--valid")
                parent.classList.add("fr-input-group--error")
            })

            var errorMessage = document.createElement("div");
            errorMessage.id = "visioCodeError";
            errorMessage.className = "visio-code-error fr-error-text";
            errorMessage.textContent = "Code de connexion incorrect";
            var container = inputs[0].parentElement.parentElement.parentElement;
            container.appendChild(errorMessage);
            valid = false;
        }
    }

    if ("captchaCode" in data){
        var parent = document.getElementById("captchaCode").parentElement;

        var existingError = document.getElementById("captchaCodeError");
        if (existingError) {
            existingError.remove();
        }

        if(data.captchaCode) {
            parent.classList.add("fr-input-group--valid")
            parent.classList.remove("fr-input-group--error")
        }
        else {
            parent.classList.remove("fr-input-group--valid")
            parent.classList.add("fr-input-group--error")

            var errorMessage = document.createElement("p");
            errorMessage.id = "captchaCodeError";
            errorMessage.className = "fr-error-text";
            errorMessage.textContent = "Code de sécurité incorrect";
            parent.appendChild(errorMessage);
            valid = false;
        }
    }
    return valid;
}

const updateSumbitButtonStatus = (event, input) => {
    document.getElementById("submit-visio-code").disabled = !formIsComplete();
}

const onFormValidate = async (event) => {
    event.preventDefault();
    if (formIsComplete() && await formIsValid(event)) {
        document.getElementById("visio-code-form").submit();
    }
}

const focusAtEnd = (input) => {
    input.focus();
    input.selectionStart = 3;
    input.selectionEnd = 3;
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
    const visioCodeId = target.dataset.visioCodeId;
    const previousSibling = document.getElementById("visio-code" + (visioCodeId - 1))

    if (isAtBeginning && previousSibling) {
        previousSibling.focus();
        previousSibling.selectionStart = 3;
        previousSibling.selectionEnd = 3;
    }
}

const updateVisioCodeVisualIndicator = (input) => {
    var is_numerical = input.value.match(/\d{3}$/);
    var parent = input.parentElement;
    if (input.value == "") {
        parent.classList.remove("fr-input-group--valid")
        parent.classList.remove("fr-input-group--error")
    } else if (!is_numerical && !parent.classList.contains("fr-input-group--error")) {
        parent.classList.remove("fr-input-group--valid")
        parent.classList.add("fr-input-group--error")
    } else if (is_numerical && !parent.classList.contains("fr-input-group--valid")) {
        parent.classList.remove("fr-input-group--error")
        parent.classList.add("fr-input-group--valid")
    }
}

if (window.shouldDisplayCaptcha) {
    captchaInput.addEventListener("keyup", (event) => {
        updateSumbitButtonStatus(event, captchaInput)
    })
}

inputs.forEach((input) => {
    updateVisioCodeVisualIndicator(input);

    // Forbid non-digits characters in inputs
    input.addEventListener("input", (event) => {
        input.value = input.value.replace(/\D/g, '')
    });

    input.addEventListener("keyup", (event) => {
        var alphanumerical_input = event.key.length == 1;
        if (input.value.length >= 3 && alphanumerical_input) {
            moveToNextInputIfNeeded(input);
        }

        if (event.key == "Backspace" || event.key == "ArrowLeft") {
            moveToPreviousInputIfNeeded(input);
        } else if (event.key == "ArrowRight") {
            moveToNextInputIfNeeded(input);
        }

        updateVisioCodeVisualIndicator(input);
        updateSumbitButtonStatus(event, input)
    })

    input.addEventListener('paste', (event) => {
        event.preventDefault()
        const pasteData = (event.clipboardData || window.clipboardData).getData('text').replace(/\D/g, '');
        const chars = [pasteData.slice(0,3), pasteData.slice(3,6), pasteData.slice(6,9)];
        inputs.forEach((pastedInput, index) => {
            pastedInput.value = chars[index];
            updateVisioCodeVisualIndicator(pastedInput);
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


document.getElementById("visio-code-form").addEventListener("submit", onFormValidate);
