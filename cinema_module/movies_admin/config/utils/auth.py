import http
import logging
from operator import itemgetter

import jwt
import requests
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend

from config.settings import AUTH_API_USER_INFO_URL
from config.utils.constants import Roles
from config.utils.requests_auth import BearerAuth

User = get_user_model()


class CustomBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        auth = BearerAuth(username, password, request.headers.get("x-request-id"))
        try:
            token_data = jwt.decode(auth.token, options={"verify_signature": False})
        except Exception:
            logging.warning("Token error, user %s", username)
            return None
        url = f"{AUTH_API_USER_INFO_URL}/{token_data['sub']}"
        response = requests.get(url, auth=auth)
        if response.status_code != http.HTTPStatus.OK:
            return None
        data = response.json()

        user, created = User.objects.get_or_create(id=data["id"])
        user.username = data.get("username")
        user.email = data.get("email")
        user.first_name = data.get("first_name")
        user.last_name = data.get("last_name")
        user.is_admin = Roles.ADMIN in map(itemgetter("name"), data.get("roles", []))
        user.is_staff = user.is_admin
        user.is_active = True
        user.save()

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
