import jwt
from jwt import DecodeError
from jwt.algorithms import RSAAlgorithm
from ..settings import rest_microservice_settings
from django.core.cache import caches
from django.contrib.auth import authenticate
import requests
import json


def get_username_from_payload_handler(payload):
    username = payload.get('sub')
    authenticate(remote_user=username)
    return username


def get_pub_keys():
    """Get cognito public keys from cache or retrieve from AWS."""
    cache = caches['default']
    pub_keys = cache.get('cognito_pub_keys')

    if pub_keys is None:
        pub_keys = {key['kid']: json.dumps(key) for key in requests.get(
        f"https://cognito-idp.{rest_microservice_settings.IDP['REGION']}.amazonaws.com/{rest_microservice_settings.IDP['USER_POOL']}/.well-known/jwks.json").json().get('keys')}
        cache.set('cognito_pub_keys', pub_keys, 86000)

    return pub_keys


def decode_token(token, audience=None):
    """
    Verify AWS Cognito JWT token.
    """
    unverified_header = jwt.get_unverified_header(token)

    if 'kid' not in unverified_header:
        raise DecodeError('Incorrect authentication credentials.')

    kid = unverified_header['kid']
    alg = unverified_header['alg']

    try:
        # pick a proper public key according to `kid` from token header
        public_key = RSAAlgorithm.from_jwk(get_pub_keys()[kid])
    except KeyError:
        # in this place we could refresh cached jwks and try again
        raise DecodeError('Can\'t find proper public key in jwks')
    else:
        return jwt.decode(
            jwt=token,
            key=public_key,
            verify=True,
            audience=audience,
            algorithms=alg
        )
