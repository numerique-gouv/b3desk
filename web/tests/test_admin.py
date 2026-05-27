from b3desk.commands import bp


def test_admin_can_enter_admin_page(cli_runner, user, client_app, authenticated_user):
    """Test admin can enter admin page."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/home").follow()
    assert "Vous êtes administrateur." in res.text
    client_app.get("/admin/home", status=200)


def test_user_cannot_enter_admin_page(cli_runner, user, client_app, authenticated_user):
    """Test user non admin cannot enter admin page."""
    res = client_app.get("/home").follow()
    assert "Vous êtes administrateur." not in res.text
    client_app.get("/admin/home", status=403)


def test_admin_page_display_all_users(
    cli_runner, user, user_2, user_3, client_app, authenticated_user
):
    """Test admin page list all users."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/users", status=200)
    assert res.text.count("alice@domain.tld") == 1
    assert res.text.count("berenice@domain.tld") == 1
    assert res.text.count("charlie@domain.tld") == 1


def test_research_bar_with_letters_in_user_list_in_admin_page(
    cli_runner, user, user_2, user_3, client_app, authenticated_user
):
    """Test research bar in user list with 'ber'."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.post("/admin/users", status=200)
    form = res.form
    form["search"] = "ber"
    res = form.submit()
    assert res.text.count("alice@domain.tld") == 0
    assert res.text.count("berenice@domain.tld") == 1
    assert res.text.count("charlie@domain.tld") == 0


def test_research_bar_with_digit_in_user_list_in_admin_page(
    cli_runner, user, user_2, user_3, client_app, authenticated_user
):
    """Test research bar in user list with '1'."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.post("/admin/users", status=200)
    form = res.form
    form["search"] = "1"
    res = form.submit()
    assert res.text.count("alice@domain.tld") == 1
    assert res.text.count("berenice@domain.tld") == 0
    assert res.text.count("charlie@domain.tld") == 0


def test_research_bar_with_no_result_in_user_list_in_admin_page(
    cli_runner, user, user_2, user_3, client_app, authenticated_user
):
    """Test research bar in user list with 'zzzzzzzzzzzzzzzzz'."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.post("/admin/users", status=200)
    form = res.form
    form["search"] = "zzzzzzzzzzzzzzzzz"
    res = form.submit()
    assert res.text.count("alice@domain.tld") == 0
    assert res.text.count("berenice@domain.tld") == 0
    assert res.text.count("charlie@domain.tld") == 0
    assert res.text.count("Aucun utilisateur ne correspond à cette recherche.") == 1


def test_admin_can_read_user_infos_with_no_meeting(
    cli_runner, user, user_2, client_app, authenticated_user
):
    """Test read user infos for a user without meeting created."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/user/2", status=200)
    print(res.text)
    assert res.text.count("berenice@domain.tld") == 1
    assert res.text.count("False") == 1
    assert "Berenice Cooler n'a pas créé de réunion." in res.text


def test_admin_can_read_user_infos_with_meeting(
    cli_runner,
    user,
    user_2,
    meeting,
    meeting_2,
    meeting_3,
    meeting_1_user_2,
    shadow_meeting,
    client_app,
    authenticated_user,
):
    """Test read user infos for a user having meetings."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/user/1", status=200)
    assert res.text.count("alice@domain.tld") == 1
    assert res.text.count("Réunions déléguées") == 1
    assert res.text.count("922222222") == 1
    assert res.text.count("511111111") == 1
    assert res.text.count("911111111") == 1
    assert res.text.count("911111112") == 1
    assert res.text.count("911111113") == 1
    assert res.text.count("Réunion silencieuse (shadow_meeting)") == 1


def test_research_bar_with_letters_in_meeting_list_in_admin_page(
    cli_runner,
    user,
    user_2,
    meeting,
    meeting_2,
    meeting_3,
    meeting_1_user_2,
    shadow_meeting,
    client_app,
    authenticated_user,
):
    """Test admin page list all meetings."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/meetings", status=200)
    form = res.form
    form["search"] = "del"
    res = form.submit()
    assert res.text.count("Réunion silencieuse (shadow_meeting)") == 0
    assert res.text.count("922222222") == 1
    assert res.text.count("511111111") == 0
    assert res.text.count("911111111") == 0
    assert res.text.count("911111112") == 0
    assert res.text.count("911111113") == 0


def test_research_bar_with_digit_in_meeting_list_in_admin_page(
    cli_runner,
    user,
    user_2,
    meeting,
    meeting_2,
    meeting_3,
    meeting_1_user_2,
    shadow_meeting,
    client_app,
    authenticated_user,
):
    """Test research bar in meeting list with '1'."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/meetings", status=200)
    form = res.form
    form["search"] = "1"
    res = form.submit()
    assert res.text.count("Réunion silencieuse (shadow_meeting)") == 0
    assert res.text.count("922222222") == 0
    assert res.text.count("511111111") == 0
    assert res.text.count("911111111") == 1
    assert res.text.count("911111112") == 0
    assert res.text.count("911111113") == 0


def test_research_bar_with_visio_code_in_meeting_list_in_admin_page(
    cli_runner,
    user,
    user_2,
    meeting,
    meeting_2,
    meeting_3,
    meeting_1_user_2,
    shadow_meeting,
    client_app,
    authenticated_user,
):
    """Test research bar in meeting list with '511111111'."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/meetings", status=200)
    form = res.form
    form["search"] = "511111111"
    res = form.submit()
    assert res.text.count("Réunion silencieuse (shadow_meeting)") == 1
    assert res.text.count("922222222") == 0
    assert res.text.count("511111111") == 2
    assert res.text.count("911111111") == 0
    assert res.text.count("911111112") == 0
    assert res.text.count("911111113") == 0


def test_research_bar_with_no_result_in_meeting_list_in_admin_page(
    cli_runner,
    user,
    user_2,
    meeting,
    meeting_2,
    meeting_3,
    meeting_1_user_2,
    shadow_meeting,
    client_app,
    authenticated_user,
):
    """Test research bar in meeting list with 'zzzzzzzzzzzzzzzzz'."""
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/admin/meetings", status=200)
    form = res.form
    form["search"] = "zzzzzzzzzzzzzzzzz"
    res = form.submit()
    assert res.text.count("Réunion silencieuse (shadow_meeting)") == 0
    assert res.text.count("922222222") == 0
    assert res.text.count("511111111") == 0
    assert res.text.count("911111111") == 0
    assert res.text.count("911111112") == 0
    assert res.text.count("911111113") == 0
    assert res.text.count("Aucune réunion ne correspond à cette recherche.") == 1


def test_admin_can_edit_meeting_for_other_user(
    cli_runner, user, user_2, meeting_1_user_2, client_app, authenticated_user
):
    cli_runner.invoke(bp.cli, ["user-to-admin", "alice@domain.tld"])
    res = client_app.get("/meeting/edit/1?admin_mode=True", status=200)
    assert res.template == "meeting/wizard.html"
    res.forms[0]["logoutUrl"] = ""
    res = res.forms[0].submit()
    assert (
        "success",
        "delegated meeting modifications prises en compte",
    ) in res.flashes
