#!/usr/bin/env python3
"""
Key-only test: Mistral API (chat + embeddings) + JWT secret key.

.env vars expected (see .env.mistral.example for a template):
    MISTRAL_API_KEY=...
    MISTRAL_API_BASE=https://api.mistral.ai/v1/
    MISTRAL_CHAT_MODEL=mistral-small-latest
    MISTRAL_EMBEDDING_MODEL=mistral-embed
    SECRET_KEY=...
    ALGORITHM=HS256

Install:
    pip install python-dotenv openai pyjwt --break-system-packages

Run:
    python test_keys_mistral.py

No Docker needed — this only talks to the external Mistral API and does
local JWT encode/decode.
"""

import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"

results = []


def report(name, ok, detail):
    status = f"{GREEN}PASS{RESET}" if ok else f"{RED}FAIL{RESET}"
    print(f"[{status}] {name}")
    print(f"        {detail}\n")
    results.append((name, ok))


def test_mistral_chat():
    name = "Mistral Chat API (MISTRAL_API_KEY / MISTRAL_CHAT_MODEL)"
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=os.environ["MISTRAL_API_KEY"],
            base_url=os.environ.get("MISTRAL_API_BASE", "https://api.mistral.ai/v1/"),
        )
        model = os.environ.get("MISTRAL_CHAT_MODEL", "mistral-small-latest")
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Reply with exactly: OK"}],
            max_tokens=5,
        )
        text = resp.choices[0].message.content
        report(name, True, f"Model '{model}' responded: {text!r}")
    except Exception as e:
        report(name, False, f"{type(e).__name__}: {e}")


def test_mistral_embedding():
    name = "Mistral Embedding API (MISTRAL_API_KEY / MISTRAL_EMBEDDING_MODEL)"
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=os.environ["MISTRAL_API_KEY"],
            base_url=os.environ.get("MISTRAL_API_BASE", "https://api.mistral.ai/v1/"),
        )
        model = os.environ.get("MISTRAL_EMBEDDING_MODEL", "mistral-embed")
        resp = client.embeddings.create(model=model, input="connectivity test")
        dims = len(resp.data[0].embedding)
        report(name, True, f"Model '{model}' returned a {dims}-dimensional vector")
    except Exception as e:
        report(name, False, f"{type(e).__name__}: {e}")


def test_jwt():
    name = "JWT signing (SECRET_KEY / ALGORITHM)"
    try:
        import jwt
        secret = os.environ["SECRET_KEY"]
        algorithm = os.environ.get("ALGORITHM", "HS256")
        payload = {"sub": "test-user", "iat": datetime.now(timezone.utc)}
        token = jwt.encode(payload, secret, algorithm=algorithm)
        decoded = jwt.decode(token, secret, algorithms=[algorithm])
        ok = decoded["sub"] == "test-user"
        report(name, ok, f"Token encoded and decoded successfully using {algorithm}")
    except Exception as e:
        report(name, False, f"{type(e).__name__}: {e}")


def main():
    print(f"{BOLD}Key-only connectivity test (Mistral API + JWT){RESET}")
    print("=" * 55 + "\n")

    test_mistral_chat()
    test_mistral_embedding()
    test_jwt()

    print("=" * 55)
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    color = GREEN if passed == total else (YELLOW if passed else RED)
    print(f"{color}{BOLD}{passed}/{total} checks passed{RESET}")

    if passed != total:
        sys.exit(1)


if __name__ == "__main__":
    main()