from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
from cryptography.hazmat.primitives.serialization import PublicFormat
import base64

def generate_vapid_keys():
    # Generate a new private key
    private_key = ec.generate_private_key(
        ec.SECP256R1(), # This is the prime256v1 curve, required for Web Push
        None # No backend needed for generation
    )

    # Get the corresponding public key
    public_key = private_key.public_key()

    # Serialize the private key (PKCS8 format, no encryption)
    private_pem = private_key.private_bytes(
        Encoding.PEM,
        PrivateFormat.PKCS8,
        NoEncryption()
    )

    # Serialize the public key (SubjectPublicKeyInfo format, uncompressed point)
    # The public key needs to be base64url encoded *without padding* for VAPID
    public_der = public_key.public_bytes(
        Encoding.X962,
        PublicFormat.UncompressedPoint
    )
    public_base64url = base64.urlsafe_b64encode(public_der).rstrip(b'=').decode('ascii')


    return {
        "private_key_pem": private_pem.decode('ascii'),
        "public_key_base64url": public_base64url
    }

# To run this and get the keys:
vapid_keys = generate_vapid_keys()
print("Private Key (PEM format):\n")
print(vapid_keys["private_key_pem"])
print("\nPublic Key (Base64url format):\n")
print(vapid_keys["public_key_base64url"])
