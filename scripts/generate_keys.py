"""Generate local Ed25519 keys in .env."""

from ledger.crypto import generate_keypair


def main() -> None:
    keys = generate_keypair()
    lines = []
    try:
        with open(".env", encoding="utf-8") as env_file:
            lines = [line.rstrip("\n") for line in env_file if not line.startswith(("PRIVATE_KEY_HEX=", "PUBLIC_KEY_HEX="))]
    except FileNotFoundError:
        pass
    with open(".env", "w", encoding="utf-8") as env_file:
        env_file.write("\n".join(lines + [f"PRIVATE_KEY_HEX={keys['private_key']}", f"PUBLIC_KEY_HEX={keys['public_key']}"]) + "\n")
    print("Generated Ed25519 keypair and saved it to .env")


if __name__ == "__main__":
    main()
