"""Upload .env values to Replit secrets automatically using the Replit CLI.

Usage:
  1. Ensure you have Replit CLI installed (`npm i -g @replit/replit-cli`).
  2. Run `replit login` to authenticate.
  3. From your repo root run:
         python scripts/upload_replit_secrets.py
  4. The script will iterate over sensible keys and call
         `replit secrets set KEY value` for each non-empty value.

This saves you from manually copying and pasting keys. It still requires the
CLI to be logged in and a Repl to be selected (run inside the cloned Repl
or supply `--repl owner/replname` as argument). For security the script does
NOT display secret values.
"""
import os
import subprocess
from pathlib import Path

DOTENV_PATH = Path.cwd() / '.env'

KEYS = [
    'TELEGRAM_TOKEN',
    'OWNER_TELEGRAM_ID',
    'GEMINI_API_KEY',
    'GROQ_API_KEY',
    'COINGECKO_API_URL',
    'PAPER_MODE',
    'MIN_BALANCE',
    'BYBIT_API_KEY',
    'BYBIT_API_SECRET',
    'PROFIT_WALLET_ADDRESS',
    'PROFIT_WITHDRAWAL_THRESHOLD'
]


def read_env(path: Path):
    env = {}
    if not path.exists():
        print(f".env file not found at {path}")
        return env
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip()
    return env


def main():
    env = read_env(DOTENV_PATH)
    if not env:
        return
    print("Uploading secrets to Replit (requires `replit` CLI and login)...")
    # allow non-interactive login via token if provided
    token = os.getenv('REPLIT_TOKEN')
    if token:
        print("Logging in with REPLIT_TOKEN...")
        subprocess.run(['replit', 'login', '--token', token], check=False)
    for key in KEYS:
        val = env.get(key, '')
        if not val:
            continue
        # call replit secrets set
        try:
            subprocess.run(['replit', 'secrets', 'set', key, val], check=True)
            print(f"Set {key}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to set {key}: {e}")
            # continue setting others

if __name__ == '__main__':
    main()
