import abc
import datetime
import json

try:
    from django.utils import timezone
except ImportError:
    is_django_available = False
else:
    is_django_available = True

import jwt
from jwt import InvalidSignatureError
from jwt.algorithms import RSAAlgorithm

import requests


class Validator(abc.ABC):
    @property
    @abc.abstractmethod
    def discovery_url(self):
        raise NotImplementedError


    @staticmethod
    @abc.abstractmethod
    def _verify_jwk(token, jwk_sets, audience):
        """
        Sets of JWK, already in dict with a "keys" property listing JWK public
        keys
        """
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def _discover(discovery_url=None):
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def validate(token, email, audience):
        raise NotImplementedError


class Google(Validator):

    discovery_url = 'https://accounts.google.com/.well-known/openid-configuration'  # noqa

    @staticmethod
    def _verify_jwk(token, jwk_sets, audience):
        claim = None

        for cert in jwk_sets['keys']:
            key = RSAAlgorithm.from_jwk(json.dumps(cert))
            try:
                claim = jwt.decode(
                    token, key=key, algorithms=['RS256'], audience=audience
                )
            except InvalidSignatureError:
                continue

        if not claim:
            raise ValueError('No valid public key for this token')

        return claim

    @staticmethod
    def _discover(discovery_url=None):
        if discovery_url is None:
            discovery_url = Google.discovery_url
        r = requests.get(discovery_url)

        if r.status_code != 200:
            raise ValueError('Discovery not returning 200')

        try:
            parsed_json = r.json()
        except Exception:
            raise ValueError('Failed to decode JSON/data')

        try:
            jwks_url = parsed_json['jwks_uri']
        except KeyError:
            raise ValueError('jwks_uri not found in discovery data')

        r = requests.get(jwks_url)

        try:
            parsed_json = r.json()
        except Exception:
            raise ValueError('Failed to decode public keys')
        try:
            keys = parsed_json['keys']
        except Exception:
            raise ValueError(f'Failed to get public keys. Data {parsed_json}')

        return parsed_json

    @staticmethod
    def validate(token, email, audience):
        jwk_sets = Google._discover()
        claim = Google._verify_jwk(token, jwk_sets, audience)

        if claim['iss'] != 'https://accounts.google.com':
            raise ValueError('Invalid issuer, malicious request')

        if claim['email'] != email:
            raise ValueError('Invalid email, malicious request')

        if not claim['email_verified']:
            raise ValueError('Invalid email (not verified), malicious request')

        expired = datetime.datetime.fromtimestamp(claim['exp'])

        if is_django_available:
            now = timezone.now()
            expired = timezone.make_aware(expired)
        else:
            now = datetime.datetime.now()

        if now > expired:
            raise ValueError('Token has expired')

        return True
