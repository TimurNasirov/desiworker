from sys import path
from os.path import dirname, abspath, exists
from os import _exit
SCRIPT_DIR = dirname(abspath(__file__))
path.append(dirname(SCRIPT_DIR))

from json import dump, load
from mods.timemod import dt, timedelta, utc_tz
from intuitlib.client import AuthClient
from intuitlib.enums import Scopes
from config import INTUIT_ID, INTUIT_URI, INTUIT_SECRET, INTUIT_REALM
from log import Log
from quickbooks import QuickBooks

# logdata = Log('rentacar.mods/intuit_refresh.py')
# print = logdata.print

def get_auth_client():
    print('got auth client')
    return AuthClient(
        client_id=INTUIT_ID,
        client_secret=INTUIT_SECRET,
        environment='production',
        redirect_uri=INTUIT_URI
    )

def update_tokens(auth_client):
    if not exists('intuit.json'):
        print('need refresh tokens')
        _exit(1)

    with open('intuit.json', 'r') as fl:
        tokens = load(fl)
        auth_client.access_token = tokens["access_token"]
        auth_client.refresh_token = tokens["refresh_token"]
        expires_at = dt.fromisoformat(tokens["expires_at"])
        auth_client.expires_in = (expires_at.astimezone(utc_tz) - dt.now(utc_tz)).total_seconds()

    if dt.now() >= expires_at:
        print("refreshing access token")
        auth_client.refresh()
        tokens["access_token"] = auth_client.access_token
        tokens["refresh_token"] = auth_client.refresh_token
        tokens["expires_at"] = (dt.now(utc_tz) + timedelta(seconds=auth_client.expires_in)).isoformat()
        with open('intuit.json', "w") as fl:
            dump(tokens, fl)
        print("token refreshed and saved")
    return auth_client

def get_qb_client(auth_client):
    return QuickBooks(
        auth_client=auth_client,
        refresh_token=auth_client.refresh_token,
        company_id=INTUIT_REALM
    )

def save_tokens(auth_client):
    with open('intuit.json', "w") as f:
        dump({
            "access_token": auth_client.access_token,
            "refresh_token": auth_client.refresh_token,
            "expires_at": (dt.now(utc_tz).astimezone(utc_tz) + timedelta(seconds=auth_client.expires_in)).isoformat()
        }, f)
    print('tokens saved.')

def load_tokens(auth_client):
    if not exists('intuit.json'):
        print('refresh bearer token required')
        _exit(1)
    with open('intuit.json') as f:
        tokens = load(f)
        auth_client.access_token = tokens["access_token"]
        auth_client.refresh_token = tokens["refresh_token"]
        auth_client.expires_in = (dt.fromisoformat(tokens["expires_at"]).astimezone(utc_tz) - dt.now(utc_tz)).total_seconds()
        print('tokens loaded')

def is_token_expired():
    with open('intuit.json') as f:
        tokens = load(f)
        expires_at = dt.fromisoformat(tokens["expires_at"])
        return dt.now(utc_tz) >= expires_at.astimezone(utc_tz)

def refresh_token(auth_client):
    with open('intuit.json') as f:
        tokens = load(f)
    global quick_client
    now = dt.now()
    if now >= dt.fromisoformat(tokens["expires_at"]):
        print("refreshing access token")
        auth_client.refresh()
        new_expires = now + timedelta(seconds=auth_client.expires_in)
        tokens.update({
            "access_token": auth_client.access_token,
            "refresh_token": auth_client.refresh_token,
            "expires_at": new_expires.isoformat()
        })
        with open('intuit.json', 'w') as fl:
            dump(tokens, fl)
        quick_client = QuickBooks(
            auth_client=auth_client,
            refresh_token=auth_client.refresh_token,
            company_id=INTUIT_REALM
        )
        print("token refreshed")


def refresh_bearer(auth_client):
    auth_url = auth_client.get_authorization_url([Scopes.ACCOUNTING])
    print("link:")
    print(auth_url)
    code = input("code: ")
    auth_client.get_bearer_token(code)
    save_tokens()