# pylint:disable=C0302,C0114,C0115,C0116,E1101,R0914,C0301,R0915,C0103,W0612,W0613,W0621,R1732

import logging

import pytest
from django.conf import settings
from django.utils.crypto import get_random_string
from jose import jwk
from pytest_http.drivers.django import DjangoDriver
from rest_framework.test import APIClient

from common.auth import default_key_store
from common.utils import generate_private_rsa_key_pem, generate_token

logger = logging.getLogger(__name__)

USERS = {
    "user@api.demeter.org": {
        "identifier": "1",
        "first_name": "Staszek",
        "last_name": "Fistaszek",
        "password": get_random_string(),
        "roles": [
            "offline_access",
            settings.SERVICE_ACCESS_ROLE_NAME,
            "uma_authorization",
        ],
    },
    "banned_user@api.demeter.org": {
        "identifier": "2",
        "first_name": "Bandyta",
        "last_name": "Zbanowany",
        "password": get_random_string(),
        "roles": [
            "offline_access",
            "uma_authorization",
        ],
    },
    "admin@api.demeter.org": {
        "identifier": "2",
        "first_name": "Adam",
        "last_name": "Administracyjny",
        "password": get_random_string(),
        "roles": [
            "offline_access",
            settings.SERVICE_ACCESS_ROLE_NAME,
            settings.SERVICE_ADMIN_ROLE_NAME,
            "uma_authorization",
        ],
    },
}


@pytest.fixture(scope="function")
def client_factory(db, settings):  # noqa
    settings.AUTH_OPENID_PROVIDER = settings.AUTH_FAKE_OPENID_PROVIDER
    settings.AUTH_CLIENT_ID = "sta-cli"
    settings.AUTH_AUD = "sta-demeter.apps.paas-dev.psnc.pl/api"

    issuer = settings.AUTH_OPENID_PROVIDER
    kid = get_random_string()
    key = jwk.RSAKey(generate_private_rsa_key_pem(), "RS256")

    default_key_store.add(kid, issuer, key.public_key().to_dict(), timeout=None)

    def provider(user=None, **kwargs):

        if user is not None:
            user_data = USERS[user]
            identifier = user_data["identifier"]
            first_name = user_data["first_name"]
            last_name = user_data["last_name"]
            roles = user_data["roles"]
            token = generate_token(
                issuer,
                kid,
                key.to_dict(),
                **{
                    settings.AUTH_USERNAME_CLAIM: user,
                    settings.AUTH_SUBJECT_CLAIM: identifier,
                    settings.AUTH_FIRST_NAME_CLAIM: first_name,
                    settings.AUTH_LAST_NAME_CLAIM: last_name,
                    settings.AUTH_AUDIENCE_CLAIM: settings.AUTH_AUD,
                    settings.AUTH_RESOURCES_ACCESS_CLAIM: {settings.AUTH_CLIENT_ID: {settings.AUTH_ROLES_CLAIM: roles}},
                },
                **kwargs,
            )
            headers = {"Authorization": settings.AUTH_HEADER_PREFIX + " " + token}
        else:
            headers = {}

        return DjangoDriver(client=APIClient(), headers=headers)

    yield provider
