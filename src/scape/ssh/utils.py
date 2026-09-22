import io

from paramiko import Ed25519Key, RSAKey, ECDSAKey
from paramiko.pkey import PKey


crypto_type_list = [Ed25519Key, RSAKey, ECDSAKey]

def detect_key_crypto(key: io.StringIO) -> PKey | None:
    for crypto_type in crypto_type_list:
        try:
            crypto_key_obj = crypto_type.from_private_key(key)
            key.seek(0)
            return crypto_key_obj
        except Exception as ex:
            key.seek(0)
    return None