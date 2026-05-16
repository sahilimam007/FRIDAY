import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
import string
import subprocess
import hashlib
import secrets

def generate_password(length: int = 16, include_symbols: bool = True) -> str:
    chars = string.ascii_letters + string.digits
    if include_symbols:
        chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
    password = ''.join(secrets.choice(chars) for _ in range(length))
    # Copy to clipboard automatically
    subprocess.run(["pbcopy"], input=password.encode())
    return f"Generated password: {password} — copied to clipboard, Boss."

def generate_pin(length: int = 6) -> str:
    pin = ''.join(secrets.choice(string.digits) for _ in range(length))
    subprocess.run(["pbcopy"], input=pin.encode())
    return f"Generated PIN: {pin} — copied to clipboard, Boss."

def generate_passphrase(words: int = 4) -> str:
    wordlist = [
        "apple", "brave", "cloud", "delta", "eagle", "frost", "globe", "hotel",
        "india", "japan", "kilo", "lima", "mango", "noble", "ocean", "pilot",
        "queen", "radio", "sigma", "tango", "ultra", "victor", "whisky", "xray",
        "yankee", "zebra", "alpha", "bravo", "cyber", "debug", "elite", "force",
        "gamma", "hyper", "ivory", "joker", "karma", "lunar", "matrix", "nexus",
        "omega", "prime", "query", "razor", "solar", "titan", "unity", "vault",
        "width", "xenon", "yield", "zenit", "amber", "blaze", "coral", "drift"
    ]
    phrase = "-".join(secrets.choice(wordlist) for _ in range(words))
    subprocess.run(["pbcopy"], input=phrase.encode())
    return f"Generated passphrase: {phrase} — copied to clipboard, Boss."

def hash_text(text: str, algorithm: str = "sha256") -> str:
    algo = algorithm.lower()
    if algo == "md5":
        result = hashlib.md5(text.encode()).hexdigest()
    elif algo == "sha1":
        result = hashlib.sha1(text.encode()).hexdigest()
    elif algo == "sha256":
        result = hashlib.sha256(text.encode()).hexdigest()
    elif algo == "sha512":
        result = hashlib.sha512(text.encode()).hexdigest()
    else:
        result = hashlib.sha256(text.encode()).hexdigest()
        algo = "sha256"
    subprocess.run(["pbcopy"], input=result.encode())
    return f"{algo.upper()} hash: {result} — copied to clipboard, Boss."

def check_password_strength(password: str) -> str:
    score = 0
    feedback = []
    if len(password) >= 8:  score += 1
    if len(password) >= 12: score += 1
    if len(password) >= 16: score += 1
    if any(c.isupper() for c in password): score += 1
    if any(c.islower() for c in password): score += 1
    if any(c.isdigit() for c in password): score += 1
    if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password): score += 1

    if score <= 3:   strength = "Weak"
    elif score <= 5: strength = "Moderate"
    else:            strength = "Strong"

    return f"Password strength: {strength} (score {score}/7), Boss."

if __name__ == "__main__":
    print(generate_password(16))
    print(generate_pin(6))
    print(generate_passphrase(4))
    print(check_password_strength("hello123"))
    print(check_password_strength("Tr0ub4dor&3"))
