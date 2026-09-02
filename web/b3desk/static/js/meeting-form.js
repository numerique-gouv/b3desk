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
    const presentationToggle = document.getElementById("showPresentationOnJoin");
    const participantsToggle = document.getElementById("showParticipantsOnLogin");
    const chatToggle = document.getElementById("showPublicChatOnLogin");
    const infoToggle = document.getElementById("showSessionDetailsOnJoin");
    const previewImage = document.getElementById("meeting-preview-image");
    if (!presentationToggle || !participantsToggle || !chatToggle || !infoToggle) {
        return;
    }

    const updatePreviewImage = () => {
        if (!previewImage) {
            return;
        }
        const presentationPart = presentationToggle.checked ? "Presentation" : "nopresentation";
        const participantsPart = participantsToggle.checked ? "participants" : "noparticipants";
        const chatPart = chatToggle.checked ? "chat" : "nochat";
        const infoPart = infoToggle.checked ? "info" : "noinfo";
        previewImage.src = `${window.previewImagesBaseUrl}BBB-${presentationPart}-${participantsPart}-${chatPart}-${infoPart}.webp`;
    };

    const syncChatToggle = () => {
        chatToggle.disabled = !participantsToggle.checked;
        if (!participantsToggle.checked) {
            chatToggle.checked = false;
        }
        updatePreviewImage();
    };

    syncChatToggle();
    participantsToggle.addEventListener("change", syncChatToggle);
    [presentationToggle, chatToggle, infoToggle].forEach((toggle) => {
        toggle.addEventListener("change", updatePreviewImage);
    });
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
