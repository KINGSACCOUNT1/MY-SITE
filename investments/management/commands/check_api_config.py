"""
Management command to verify that the Bybit API credentials are configured
and accepted by the Bybit v5 REST API.

Usage:
    python manage.py check_api_config

The command never prints actual credential values — it only shows:
  • Whether each environment variable is set
  • A masked preview (first 4 characters followed by asterisks)
  • Whether a live Bybit API call succeeds with those credentials
"""

import hashlib
import hmac
import json
import time
import urllib.parse
import urllib.request

from django.conf import settings
from django.core.management.base import BaseCommand


def _mask(value: str) -> str:
    """Return a safe masked version of a secret string."""
    if not value:
        return '<not set>'
    visible = value[:4]
    return f"{visible}{'*' * min(len(value) - 4, 20)}"


class Command(BaseCommand):
    help = 'Check that the Bybit API credentials are configured and accepted by Bybit.'

    def handle(self, *args, **options):
        api_key = getattr(settings, 'BYBIT_API_KEY', '')
        api_secret = getattr(settings, 'BYBIT_API_SECRET', '')

        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('=== Bybit API Configuration Check ==='))
        self.stdout.write('')

        # ── 1. Presence check ──────────────────────────────────────────────
        key_ok = bool(api_key)
        secret_ok = bool(api_secret)

        key_label = self.style.SUCCESS('SET') if key_ok else self.style.ERROR('NOT SET')
        secret_label = self.style.SUCCESS('SET') if secret_ok else self.style.ERROR('NOT SET')

        self.stdout.write(f'  BYBIT_API_KEY    : {key_label}  ({_mask(api_key)})')
        self.stdout.write(f'  BYBIT_API_SECRET : {secret_label}  ({_mask(api_secret)})')
        self.stdout.write('')

        if not key_ok or not secret_ok:
            self.stdout.write(
                self.style.ERROR(
                    '✗ One or more credentials are missing.\n'
                    '  Set BYBIT_API_KEY and BYBIT_API_SECRET in your environment\n'
                    '  (or in the Render dashboard under Environment Variables).'
                )
            )
            return

        # ── 2. Live connectivity test ──────────────────────────────────────
        self.stdout.write('  Testing live connection to Bybit v5 API …')
        ok, message = self._test_bybit(api_key, api_secret)
        self.stdout.write('')

        if ok:
            self.stdout.write(self.style.SUCCESS(f'  ✓ Bybit API credentials are VALID. {message}'))
        else:
            self.stdout.write(self.style.ERROR(f'  ✗ Bybit API call FAILED. {message}'))
            self.stdout.write('')
            self.stdout.write(
                '  Common causes:\n'
                '   • Wrong API key or secret — double-check them in the Bybit portal\n'
                '   • Key does not have "Read" permission for asset/deposit endpoints\n'
                '   • IP restriction on the key — add your server IP in Bybit\'s key settings\n'
                '   • Clock skew — ensure the server clock is accurate (NTP in sync)'
            )

        self.stdout.write('')

    # ── helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _test_bybit(api_key: str, api_secret: str) -> tuple[bool, str]:
        """
        Make a lightweight authenticated request to Bybit v5
        (query deposit address for BTC/BTC) and return (success, message).
        The message never contains the actual credential values.
        """
        recv_window = '5000'
        timestamp = str(int(time.time() * 1000))
        params = {'coin': 'BTC', 'chainType': 'BTC'}
        query_string = urllib.parse.urlencode(params)

        sign_payload = f'{timestamp}{api_key}{recv_window}{query_string}'
        signature = hmac.new(
            api_secret.encode('utf-8'),
            sign_payload.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()

        url = f'https://api.bybit.com/v5/asset/deposit/query-address?{query_string}'
        req = urllib.request.Request(url)
        req.add_header('X-BAPI-API-KEY', api_key)
        req.add_header('X-BAPI-SIGN', signature)
        req.add_header('X-BAPI-TIMESTAMP', timestamp)
        req.add_header('X-BAPI-RECV-WINDOW', recv_window)
        req.add_header('Content-Type', 'application/json')

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = json.loads(resp.read().decode('utf-8'))
            ret_code = body.get('retCode', -1)
            ret_msg = body.get('retMsg', 'unknown')
            if ret_code == 0:
                return True, f'(Bybit retCode=0, retMsg="{ret_msg}")'
            return False, f'Bybit returned retCode={ret_code}, retMsg="{ret_msg}"'
        except urllib.error.HTTPError as exc:
            return False, f'HTTP {exc.code} from Bybit API.'
        except urllib.error.URLError as exc:
            return False, f'Network error reaching Bybit API: {exc.reason}'
        except (json.JSONDecodeError, ValueError) as exc:
            return False, f'Could not parse Bybit response: {exc}'
        except OSError as exc:
            return False, f'OS/socket error contacting Bybit API: {exc}'
