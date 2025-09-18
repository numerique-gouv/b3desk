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

const updateSumbitButtonStatus = (event, input) => {
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
    if (visioCodeIsComplete()) {
        document.getElementById("visio-code-form").submit();
    } else {
        visualValidation(input);
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

if (window.shouldDisplayCaptcha) {
    captchaInput.addEventListener("keyup", (event) => {
        updateSumbitButtonStatus(event, captchaInput)
    })
}

inputs.forEach((input) => {
    visualValidation(input);

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

        visualValidation(input);
        updateSumbitButtonStatus(event, input)
    })

    input.addEventListener('paste', (event) => {
        event.preventDefault()
        const pasteData = (event.clipboardData || window.clipboardData).getData('text').replace(/\D/g, '');
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


document.getElementById("visio-code-form").addEventListener("submit", formValidateAndSubmit);
