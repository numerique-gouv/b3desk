function createNCFilePicker() {
    let ncPickerParams = {
        url: nc_locator,
        login: nc_login,
        accessToken: nc_token,
    };

    const ncfilepicker = window.createFilePicker('ncfilepicker', ncPickerParams);

    document.addEventListener('filepicker-manually-closed', (e) => {
        window.close();
    })

    document.addEventListener('get-files-path', (e) => {
        // the selection is an array with the nextcloud-relative paths of selected files.
            // we POST those data to visio-agent which will then call BBB

        var csrf_token = document.getElementsByName("csrf_token")[0].value
        var post_data = e.detail.selection.map(name => name.slice(1))
        JSON.stringify(post_data);
        fetch(insert_documents_url, {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-CSRFToken':csrf_token
            },
            body: JSON.stringify(post_data)
        })
            .then(res => {
                if (res.status == 200) {
                    return (res.json())
                } else {
                    throw 'ERROR'
                }

            })
            .then(data => {
                setTimeout(() => window.close(), 100);
            })
            .catch(e => console.log(e))

    })
    ncfilepicker.getFilesPath();

}
document.addEventListener('DOMContentLoaded', (event) => {
    import('/static/js/filePickerWrapper.js').then(() => {
        createNCFilePicker();
    });
})
