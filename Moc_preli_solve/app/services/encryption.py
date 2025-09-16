
from __future__ import annotations
import hashlib
from typing import List, Tuple

MODULUS = 2**61 - 1  # a big prime for toy homomorphic addition

def hash_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def verify_zkp(ciphertext: str, proof: str, voter_id: str) -> bool:
    """
    Toy "zero-knowledge": verify that proof == SHA256(voter_id|ciphertext) prefix.
    """
    expected = hash_str(voter_id + "|" + ciphertext)[:16]
    return proof == expected

def encrypt_plaintext(x: int, secret: str) -> str:
    # Toy "encryption": c = (x + H(secret)) mod P, encoded as hex
    k = int(hash_str(secret), 16) % MODULUS
    c = (x + k) % MODULUS
    return hex(c)

def decrypt_ciphertext(c_hex: str, secret: str) -> int:
    k = int(hash_str(secret), 16) % MODULUS
    c = int(c_hex, 16) % MODULUS
    return (c - k) % MODULUS

def homomorphic_add(ciphertexts: List[str]) -> str:
    total = 0
    for ch in ciphertexts:
        total = (total + int(ch, 16)) % MODULUS
    return hex(total)
