from google.cloud import kms
from google.protobuf import duration_pb2
import os
import datetime
import crcmod
import six
import time
import base64
import hashlib
from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes

"""
Encryption Decryption LifeCycle:

Day 0
generate key retention 

Key Rotations
Day 1
generate key K1
encrypt decrypt data with K1

Day 29 30min before day 30 => makes it almost impossible to brute force given that time and strength of encryption
encrypt decrypt data with retention

Day 30
generate key k2
decrypt with retention
encrypt decrypt data with K2

"""


class GoogleCloudKeyManagement:
    def __init__(self):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/sz3yan/Tommy-Destiny/Tommy-Destiny/google.json"

    # create once only when setup
    def create_key_ring(self, project_id, location_id, key_ring_id):
        """
        Creates a new key ring in Cloud KMS

        Args:
            project_id (string): Google Cloud project ID (e.g. 'my-project').
            location_id (string): Cloud KMS location (e.g. 'us-east1').
            key_ring_id (string): ID of the key ring to create (e.g. 'my-key-ring').

        Returns:
            KeyRing: Cloud KMS key ring.

        """

        # Import the client library.
        from google.cloud import kms

        # Create the client.
        client = kms.KeyManagementServiceClient()

        # Build the parent location name.
        location_name = f'projects/{project_id}/locations/{location_id}'

        # Build the key ring.
        key_ring = {}

        # Call the API.
        created_key_ring = client.create_key_ring(
            request={'parent': location_name, 'key_ring_id': key_ring_id, 'key_ring': key_ring})
        print('Created key ring: {}'.format(created_key_ring.name))
        return created_key_ring

    # for actively encrypting and decrypting data
    def create_key_rotation_schedule(self, project_id, location_id, key_ring_id, key_id):
        """
        Creates a new key in Cloud KMS that automatically rotates.

        Args:
            project_id (string): Google Cloud project ID (e.g. 'my-project').
            location_id (string): Cloud KMS location (e.g. 'us-east1').
            key_ring_id (string): ID of the Cloud KMS key ring (e.g. 'my-key-ring').
            key_id (string): ID of the key to create (e.g. 'my-rotating-key').

        Returns:
            CryptoKey: Cloud KMS key.

        """

        # Import the client library.
        from google.cloud import kms

        # Import time for getting the current time.
        import time

        # Create the client.
        client = kms.KeyManagementServiceClient()

        # Build the parent key ring name.
        key_ring_name = client.key_ring_path(project_id, location_id, key_ring_id)

        # Build the key.
        purpose = kms.CryptoKey.CryptoKeyPurpose.ENCRYPT_DECRYPT
        algorithm = kms.CryptoKeyVersion.CryptoKeyVersionAlgorithm.GOOGLE_SYMMETRIC_ENCRYPTION
        key = {
            'purpose': purpose,
            'version_template': {
                'algorithm': algorithm,
            },

            # Rotate the key every 30 days.
            'rotation_period': {
                'seconds': 60 * 60 * 24 * 30
            },

            # Start the first rotation in 24 hours.
            'next_rotation_time': {
                'seconds': int(time.time()) + 60 * 60 * 24
            }
        }

        # Call the API.
        created_key = client.create_crypto_key(
            request={'parent': key_ring_name, 'crypto_key_id': key_id, 'crypto_key': key})
        print('Created labeled key: {}'.format(created_key.name))
        return created_key

    # for key retention 
    def create_key(self, project_id, location_id, key_ring_id, key_id):
        client = kms.KeyManagementServiceClient()

        # Build the parent key ring name.
        key_ring_name = client.key_ring_path(project_id, location_id, key_ring_id)

        # Build the key.
        purpose = kms.CryptoKey.CryptoKeyPurpose.ENCRYPT_DECRYPT
        algorithm = kms.CryptoKeyVersion.CryptoKeyVersionAlgorithm.GOOGLE_SYMMETRIC_ENCRYPTION
        key = {
            'purpose': purpose,
            'version_template': {
                'algorithm': algorithm,
            }
        }

        # Call the API.
        created_key = client.create_crypto_key(
            request={'parent': key_ring_name, 'crypto_key_id': key_id, 'crypto_key': key})
        print('Created labeled key: {}'.format(created_key.name))
        return created_key

    # to encrypt and decrypt data
    def retrieve_key(self, project_id, location_id, key_ring_id, key_id):
        client = kms.KeyManagementServiceClient()

        key_name = client.crypto_key_path(project_id, location_id, key_ring_id, key_id)
        retrieved_key = client.get_crypto_key(request={'name': key_name})
        # print('Retrieved key: {}'.format(retrieved_key.name))
        return retrieved_key


class preparing_data_for_newKey:
    def __init__(self):
        self.googleCloudKeyManagement = GoogleCloudKeyManagement()

    def retrieve_key(self):
        # naming of key got a bit problem but it doesnt affect anything.
        return self.googleCloudKeyManagement.retrieve_key('tommy-destiny', 'global', 'my-key-ring', 'key-rotation') 


class AES_GCM:
    def __init__(self):
        self.HASH_NAME = "SHA512"
        self.IV_LENGTH = 12
        self.ITERATION_COUNT = 65536
        self.KEY_LENGTH = 32
        self.SALT_LENGTH = 16
        self.TAG_LENGTH = 16
        self.key = None

    def get_iv(self):
        return get_random_bytes(self.IV_LENGTH)

    def get_key(self):
        return self.key

    def encrypt(self, password, plain_message):
        salt = get_random_bytes(self.SALT_LENGTH)
        key = self.get_secret_key(password, salt)
        self.key = key

        iv = self.get_iv()
        cipher = AES.new(key, AES.MODE_GCM, iv)

        encrypted_message_byte, tag = cipher.encrypt_and_digest(plain_message)
        cipher_byte = iv + salt + encrypted_message_byte + tag

        encoded_cipher_byte = base64.b64encode(cipher_byte)
        return bytes.decode(encoded_cipher_byte)

    def decrypt(self, password, cipher_message):
        decoded_cipher_byte = base64.b64decode(cipher_message)

        iv = decoded_cipher_byte[:self.IV_LENGTH]
        salt = decoded_cipher_byte[self.IV_LENGTH:(self.IV_LENGTH + self.SALT_LENGTH)]
        encrypted_message_byte = decoded_cipher_byte[(self.IV_LENGTH + self.SALT_LENGTH):-self.TAG_LENGTH]
        tag = decoded_cipher_byte[-self.TAG_LENGTH:]

        key = self.get_secret_key(password, salt)
        cipher = AES.new(key, AES.MODE_GCM, iv)

        decrypted_message_byte = cipher.decrypt_and_verify(encrypted_message_byte, tag)
        return decrypted_message_byte.decode("utf-8")

    def get_secret_key(self, password, salt):
        return hashlib.pbkdf2_hmac(self.HASH_NAME, password.encode(), salt, self.ITERATION_COUNT, self.KEY_LENGTH)


from argon2 import PasswordHasher, Type, exceptions

class Argon2ID:
    """
        provides a balanced approach to resisting both side-channel and GPU-based attacks
        Argon2id should use one of the following configuration settings as a base minimum which includes 
        the minimum memory size (m), the minimum number of iterations (t) and the degree of parallelism (p).
        m=37 MiB, t=1, p=1
    """
    def __init__(self):
        # time_cost for the cpu to run the algorithm
        # memory_cost for the memory to run the algorithm
        # parallelism for the number of threads to run the algorithm
        self.hasher = PasswordHasher(time_cost=20, memory_cost=65536 , parallelism=5, type=Type.ID)

    def hash_password(self, password):
        return self.hasher.hash(password)

    def verify_password(self, hash, password):
        try:
            return self.hasher.verify(hash, password)
        except exceptions.VerifyMismatchError:
            return "The secret does not match the hash"


# if __name__ == '__main__':    
#     # import os
#     # os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/sz3yan/Tommy-Destiny/google.json"

#     # a = GoogleCloudKeyManagement()
#     # rotating = a.create_key_rotation_schedule('tommy-destiny', 'global', 'my-key-ring', 'key_id')
    
#     # key_retention = a.retrieve_key('tommy-destiny', 'global', 'my-key-ring', 'key-rotation')
#     # keep_rotating = a.retrieve_key('tommy-destiny', 'global', 'my-key-ring', 'key_id')

#     b = Argon2ID()
#     password = "password"
#     hash = b.hash_password(password)
#     print(hash)