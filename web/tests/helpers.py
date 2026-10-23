def form_with_action(response, action):
    """Return the form of the page whose action starts with ``action``."""
    return next(
        form for form in response.forms.values() if form.action.startswith(action)
    )
