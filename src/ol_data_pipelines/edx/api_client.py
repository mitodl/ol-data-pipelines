from typing import Dict, Generator, List, Text

import httpx


def get_access_token(  # noqa: S107
    client_id: Text, client_secret: Text, edx_url: Text, token_type: Text = "jwt"
) -> Text:
    """Retrieve an access token from an Open edX site via OAUTH2 credentials.

    :param client_id: OAUTH2 client ID for Open edX installation
    :type client_id: Text

    :param client_secret: OAUTH2 client secret for Open edX installation
    :type client_secret: Text

    :param edx_url: Base URL of edX instance being queried, including protocol.  e.g.
        https://lms.mitx.mit.edu
    :type edx_url: Text

    :param token_type: Whether to use a JWT or Bearer token.
    :type token_type: Text

    :returns: The retrieved JWT access token for authenticating requests to Open edX API

    :rtype: Text
    """
    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "token_type": token_type,
    }
    response = httpx.post(f"{edx_url}/oauth2/access_token", data=payload)
    response.raise_for_status()
    return response.json()["access_token"]


def _get_username(edx_url: Text, access_token: Text):
    response = httpx.get(
        f"{edx_url}/api/user/v1/me",
        headers={"Authorization": f"JWT {access_token}"},
    )
    response.raise_for_status()
    return response.json()["username"]


def _fetch_with_auth(edx_url: Text, access_token: Text):
    username = _get_username(edx_url, access_token)
    response = httpx.get(
        f"{edx_url}/api/courses/v1/courses/",
        headers={"Authorization": f"JWT {access_token}"},
        params={"username": username},
    )
    response.raise_for_status()
    return response.json()


def get_edx_course_ids(
    edx_url: Text, access_token: Text
) -> Generator[List[Dict], None, None]:
    """Retrieve all items from the edX courses REST API including pagination.

    :param edx_url: Base URL of edX instance being queried, including protocol.  e.g.
        https://lms.mitx.mit.edu
    :type edx_url: Text

    :param access_token: A valid JWT or Bearer access token for authenticating to the
        edX API
    :type access_token: Text

    :yield: A generator for walking the paginated list of courses returned from the
        API
    """
    response_data = _fetch_with_auth(edx_url, access_token)
    course_data = response_data["results"]
    next_page = response_data["pagination"].get("next")
    yield course_data
    while next_page:
        response_data = _fetch_with_auth(edx_url, access_token)
        next_page = response_data["pagination"].get("next")
        yield response_data["results"]
