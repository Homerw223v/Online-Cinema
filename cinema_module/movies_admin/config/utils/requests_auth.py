import http

import requests

from config.settings import AUTH_API_LOGIN_URL


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, username, password, request_id):
        self.request_id = request_id
        credentials = {"username": username, "password": password}
        response = requests.post(AUTH_API_LOGIN_URL, data=credentials, headers={"x-request-id": request_id})
        if response.status_code == http.HTTPStatus.OK:
            access_data = response.json()
            self.token = access_data.get("access_token")
        else:
            self.token = ""

    def __call__(self, req):
        req.headers["authorization"] = f"Bearer {self.token}"
        req.headers["x-request-id"] = self.request_id
        return req
