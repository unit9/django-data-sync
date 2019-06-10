import datetime
import json

import requests
import jwt
from django.utils import timezone
from jwt import InvalidSignatureError
from jwt.algorithms import RSAAlgorithm


class Google:

    discovery_url = 'https://accounts.google.com/.well-known/openid-configuration'  # noqa

    @staticmethod
    def verify_jwk(token, jwk_sets, audience):
        """
        Sets of JWK, already in dict with a "keys" property listing JWK public
        keys
        """

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
    def discover(discovery_url=None):
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
    def validate(token, audience):
        jwk_sets = Google.discover()
        claim = Google.verify_jwk(token, jwk_sets, audience)

        if claim['iss'] != 'https://accounts.google.com':
            raise ValueError('Invalid issuer, malicious request!')

        expired = datetime.datetime.fromtimestamp(claim['exp'])
        if timezone.now() > expired:
            raise ValueError('Token has expired')

        return True
