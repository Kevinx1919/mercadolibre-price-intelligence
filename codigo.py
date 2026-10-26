import os, base64, hashlib

# Generar code_verifier
code_verifier = base64.urlsafe_b64encode(os.urandom(64)).decode('utf-8').rstrip('=')

# Generar code_challenge
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode('utf-8')).digest()
).decode('utf-8').rstrip('=')

print("Code Verifier:", code_verifier)
print("Code Challenge:", code_challenge)
