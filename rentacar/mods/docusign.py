from docusign_esign import ApiClient, EnvelopesApi, Document, Signer, SignHere, Recipients, EnvelopeDefinition
import base64
from rentacar.config import USER_ID, INTEGRATION_KEY
from rentacar.log import Log
logdata = Log('docusign.py')
print = logdata.print

def sign(name: str, email: str, document: str):
    print(f'sending email to {email}')
    api_client = ApiClient()
    api_client.set_oauth_host_name("account.docusign.com")

    try:
        with open('private_key.pem', "r") as key_file:
            private_key = key_file.read()

        token_response = api_client.request_jwt_user_token(
            client_id=INTEGRATION_KEY,
            user_id=USER_ID,
            oauth_host_name="account.docusign.com",
            private_key_bytes=private_key,
            expires_in=3600,
            scopes=["signature", "impersonation"]
        )
        access_token = token_response.access_token
        user_info = api_client.get_user_info(access_token)
        account = user_info.accounts[0]
        account_id = account.account_id
        base_uri = account.base_uri
        api_client.host = base_uri + "/restapi"
        api_client.set_default_header("Authorization", f"Bearer {access_token}")

    except Exception as e:
        print(f"auth error: {str(e)}")

    try:
        with open(document, "rb") as file:
            document_base64 = base64.b64encode(file.read()).decode("utf-8")
    except Exception as e:
        print(f"document read error: {str(e)}")

    document = Document(
        document_base64=document_base64,
        name="Vehicle Lease Agreement",
        file_extension="docx",
        document_id="1"
    )
    sign_here_lessee = SignHere(
        document_id="1",
        recipient_id="1",
        anchor_string="{{signature}}",
        anchor_units="pixels",
        anchor_x_offset="0",
        anchor_y_offset="0",
        anchor_ignore_if_not_present="false",
        anchor_match_whole_word="true",
        anchor_case_sensitive="true"
    )
    signer_lessee = Signer(
        email=email,
        name=name,
        recipient_id="1",
        routing_order="1",
        tabs={"signHereTabs": [sign_here_lessee]}
    )
    envelope_definition = EnvelopeDefinition(
        email_subject="Please sign the Vehicle Lease Agreement",
        documents=[document],
        recipients=Recipients(signers=[signer_lessee]),
        status="sent"
    )
    try:
        envelopes_api = EnvelopesApi(api_client)
        envelope_summary = envelopes_api.create_envelope(
            account_id=account_id,
            envelope_definition=envelope_definition
        )
        print(f"Document sent. Envelope ID: {envelope_summary.envelope_id}")
    except Exception as e:
        print(f"document send error: {str(e)}")
    try:
        status = envelopes_api.get_envelope(account_id=account_id, envelope_id=envelope_summary.envelope_id)
        print(f"Envelope status: {status.status}")
    except Exception as e:
        print(f"Error status checking: {str(e)}")

