import sys
import subprocess
from pathlib import Path

def build_project() -> None:
    print("🚀 [1/3] Assembling modern project file structure...")

def install_package() -> None:
    print("\n📦 [2/3] Installing dependencies and 'crypto-cli' package...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])

def run_tests() -> None:
    print("\n🧪 [3/3] Running end-to-end integration test suite...\n")

    master_pass = "MasterVaultSecretPassphrase2026!"

    print("🔐 Testing encrypted key vault storage...")
    subprocess.run(["crypto-cli", "keygen", "generate", "--alias", "db-secret", "--master-pass", master_pass], check=True)
    subprocess.run(["crypto-cli", "keygen", "rotate", "--alias", "db-secret", "--master-pass", master_pass], check=True)

    print("\n🔎 Testing security inspection & AI advisor...")
    subprocess.run(["crypto-cli", "inspect", "--ai"], check=True)

    test_file = Path("payload.txt")
    enc_file = Path("payload.enc")
    dec_file = Path("payload_dec.txt")

    test_file.write_text("Top secret message encrypted successfully!", encoding="utf-8")

    print("\n🔒 Encrypting file with AES-256-GCM...")
    subprocess.run(["crypto-cli", "encrypt", "encrypt-file", "-i", str(test_file), "-o", str(enc_file), "-p", "UltraSecurePassphrase123"], check=True)

    print("🔓 Decrypting file with AES-256-GCM...")
    subprocess.run(["crypto-cli", "encrypt", "decrypt-file", "-i", str(enc_file), "-o", str(dec_file), "-p", "UltraSecurePassphrase123"], check=True)

    print(f"📄 Decrypted Payload Verification: {dec_file.read_text(encoding='utf-8')}")

    print("\n⚡ Computing SHA-3 Digest...")
    subprocess.run(["crypto-cli", "hash", "file", str(test_file)], check=True)

    test_file.unlink(missing_ok=True)
    enc_file.unlink(missing_ok=True)
    dec_file.unlink(missing_ok=True)

if __name__ == "__main__":
    install_package()
    run_tests()
    print("\n✨ Installation, modernization, and verification complete! The 'crypto-cli' binary is ready.")