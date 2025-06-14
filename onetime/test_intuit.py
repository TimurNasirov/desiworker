from os import _exit
from os.path import exists
from json import dump, load
from mods.timemod import dt, timedelta
from intuitlib.client import AuthClient
from quickbooks import QuickBooks
from quickbooks.objects.payment import Payment
from datetime import UTC

INTUIT_ID = "ABA2fRiqoLIH0299KQY5ElKX5pzE6018MiaQBRLrJK3KVQcem9"
INTUIT_SECRET = "pmf98c5Sz6maydrND3Ec6v09Zcx0rKq4Mc7b6iEJ"
INTUIT_URI = "https://developer.intuit.com/v2/OAuth2Playground/RedirectUrl"
INTUIT_REALM = "9130357731363236"

auth_client = AuthClient(
    client_id=INTUIT_ID,
    client_secret=INTUIT_SECRET,
    environment='production',
    redirect_uri=INTUIT_URI
)

if not exists('intuit.json'):
    print('need refresh tokens')
    _exit(1)
with open('intuit.json', 'r') as fl:
    tokens = load(fl)
    auth_client.access_token = tokens["access_token"]
    auth_client.refresh_token = tokens["refresh_token"]
    expires_at = dt.fromisoformat(tokens["expires_at"])
    auth_client.expires_in = (dt.fromisoformat(tokens["expires_at"]).astimezone(UTC) - dt.now(UTC)).total_seconds()

if dt.now(UTC) >= expires_at.astimezone(UTC):
    auth_client.refresh()
    with open('intuit.json', "w") as fl:
        dump({
            "access_token": auth_client.access_token,
            "refresh_token": auth_client.refresh_token,
            "expires_at": (dt.now() + timedelta(seconds=auth_client.expires_in)).isoformat()
        }, fl)

client = QuickBooks(
    auth_client=auth_client,
    refresh_token=auth_client.refresh_token,
    company_id=INTUIT_REALM
)

print(Payment.get('4299', qb=client).to_dict())