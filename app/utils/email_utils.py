import base64

def decode_emails(service, messages):
    decoded_body_list = []
    for message in messages:
        msg_id = message['id']
        msg = service.users().messages().get(userId="me", id=msg_id, format='full').execute()
        parts = msg['payload']['parts']
        
        for part in parts:
            nested_parts = part.get('parts')
            if not nested_parts:
                if part['mimeType'] == 'text/plain':
                    decoded_body_list.append(_decode_body(part))
            else:
                # If there are nested parts, iterate through them
                for part in nested_parts:
                    if part['mimeType'] == 'text/plain':
                        decoded_body_list.append(_decode_body(part))
                        break
    return decoded_body_list


def _decode_body(part) -> str:
    data = part['body']['data']
    byte_code = base64.urlsafe_b64decode(data)
    text = byte_code.decode("utf-8")
    print(text)
    return text


