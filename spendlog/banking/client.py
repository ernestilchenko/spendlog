import json
import time
import urllib.error
import urllib.parse
import urllib.request

import jwt

API_URL = 'https://api.enablebanking.com'


class EnableBankingError(Exception):
    def __init__(self, status, detail):
        super().__init__(f'{status or "network"}: {detail}')
        self.status = status


class EnableBankingClient:
    def __init__(self, app_id, private_key, timeout=30):
        self._app_id = app_id
        self._private_key = private_key
        self._timeout = timeout

    def _token(self):
        now = int(time.time())
        claims = {'iss': 'enablebanking.com', 'aud': 'api.enablebanking.com', 'iat': now, 'exp': now + 3600}
        return jwt.encode(claims, self._private_key, algorithm='RS256', headers={'kid': self._app_id})

    def _request(self, method, path, params=None, body=None):
        query = urllib.parse.urlencode({key: value for key, value in (params or {}).items() if value is not None})
        request = urllib.request.Request(
            f'{API_URL}{path}{"?" + query if query else ""}',
            data=json.dumps(body).encode() if body is not None else None,
            method=method,
            headers={
                'Authorization': f'Bearer {self._token()}',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                return json.loads(response.read() or b'{}')
        except urllib.error.HTTPError as exc:
            raise EnableBankingError(exc.code, exc.read().decode(errors='replace')[:400]) from exc
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            raise EnableBankingError(None, type(exc).__name__) from exc

    def aspsps(self, country):
        return self._request('GET', '/aspsps', {'country': country}).get('aspsps', [])

    def start_auth(self, aspsp_name, country, redirect_url, state, valid_until):
        body = {
            'access': {'valid_until': valid_until.isoformat()},
            'aspsp': {'name': aspsp_name, 'country': country},
            'state': state,
            'redirect_url': redirect_url,
            'psu_type': 'personal',
        }
        return self._request('POST', '/auth', body=body)['url']

    def create_session(self, code):
        return self._request('POST', '/sessions', body={'code': code})

    def transactions(self, account_uid, date_from):
        result, continuation_key = [], None
        while True:
            page = self._request(
                'GET',
                f'/accounts/{account_uid}/transactions',
                {'date_from': date_from.isoformat(), 'continuation_key': continuation_key},
            )
            result.extend(page.get('transactions') or [])
            continuation_key = page.get('continuation_key')
            if not continuation_key:
                return result

    def balances(self, account_uid):
        return self._request('GET', f'/accounts/{account_uid}/balances').get('balances', [])
