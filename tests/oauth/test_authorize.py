from app.oauth.views.authorize import get_host_name_and_scheme


def test_get_host_name_and_scheme():
    assert get_host_name_and_scheme("http://localhost:8000?a=b") == (
        "localhost",
        "http",
    )

    assert get_host_name_and_scheme(
        "https://www.bubblecode.net/en/2016/01/22/understanding-oauth2/#Implicit_Grant"
    ) == ("www.bubblecode.net", "https")
