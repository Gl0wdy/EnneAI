from cryptography.fernet import Fernet

from enneai.config import ENCRYPTION_KEY


class Encryptor:
    def __init__(self, key: str = ENCRYPTION_KEY):
        self.fernet = Fernet(
            key.encode()
        )

    def encrypt(self, value: str) -> str:
        return self.fernet.encrypt(
            value.encode()
        ).decode()

    def decrypt(self, value: str) -> str:
        return self.fernet.decrypt(
            value.encode()
        ).decode()