import os
from typing import Optional

import nacl.encoding
import nacl.signing

def create_signing_key_if_not_exists() -> None:
    """
    create a new pair of sign and verify key, but only if they not already exist in the current working directory

    :return: None

    """

    if not (os.path.isfile("signing_key.key") and os.path.isfile("verify_key.key")):
        signing_key = nacl.signing.SigningKey.generate()
        verify_key = signing_key.verify_key

        signing_key_b64 = signing_key.encode(nacl.encoding.Base64Encoder)  # encode in base64 to get ascii utf8-compatible characters
        verify_key_b64 = verify_key.encode(nacl.encoding.Base64Encoder)

        with open("signing_key.key", "w") as fp:
            fp.write(signing_key_b64.decode("utf8"))
        with open("verify_key.key", "w") as fp:
            fp.write(verify_key_b64.decode("utf8"))

def get_signing_key() -> Optional[nacl.signing.SigningKey]:
    """
    read the signing key from the file

    :return: the signing key object, or None if it does not exist or the file cant be read

    """

    if os.path.isfile("signing_key.key"):
        with open("signing_key.key", "r") as fp:
            signing_key_b64 = fp.read().encode("utf8")
            return nacl.signing.SigningKey(signing_key_b64, encoder=nacl.encoding.Base64Encoder)
    else:
        return None

def get_verify_key() -> Optional[nacl.signing.VerifyKey]:
    """
    read the verify key from the file

    :return: the verify key object, or None if it does not exist or the file cant be read

    """

    if os.path.isfile("verify_key.key"):
        with open("verify_key.key", "r") as fp:
            verify_key_b64 = fp.read().encode("utf8")
            return nacl.signing.VerifyKey(verify_key_b64, encoder=nacl.encoding.Base64Encoder)
    else:
        return None


if __name__ == "__main__":  # file is accessed standalone as well as imported
    create_signing_key_if_not_exists()
