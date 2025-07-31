import base64

from app.models.email import Email


def decode_emails(service, messages) -> list[Email]:
    decoded_body_list = []
    for message in messages:
        msg_id = message['id']
        msg = service.users().messages().get(
            userId="me", id=msg_id, format='full').execute()
        parts = msg['payload']['parts']

        for part in parts:
            text_part = None
            nested_parts = part.get('parts', {})
            if not nested_parts:
                if part['mimeType'] == 'text/plain':
                    text_part = part

            for part in nested_parts:
                if part['mimeType'] == 'text/plain':
                    text_part = part

            if text_part:
                text = _decode_body(part)
                decoded_body_list.append(Email(id=msg_id, body=text))

    return decoded_body_list


def _decode_body(part) -> str:
    data = part['body']['data']
    byte_code = base64.urlsafe_b64decode(data)
    text = byte_code.decode("utf-8")
    return text
