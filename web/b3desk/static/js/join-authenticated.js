document.addEventListener('keyup', updatePreview);

/* Takes the user name from the form inputs,
 * and dynamically display the concatenation in the 'preview' form.
 */
function updatePreview(e) {
    const fullnameField = document.getElementById('fullname')
    const suffixField = document.getElementById('fullname_suffix')
    const previewArea = document.getElementById('namePreview')
    var namePreview = fullnameField.value
    if (suffixField.value.length) {
        namePreview += " - " + suffixField.value
    }
    previewArea.innerHTML = namePreview
}
updatePreview()
