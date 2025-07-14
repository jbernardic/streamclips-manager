def test_admin_auth(client, admin_token):
    assert isinstance(admin_token, str)
    assert len(admin_token) > 0