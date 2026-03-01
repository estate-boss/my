"""
Helper: read .env and print `replit secrets set` commands for easy copy/paste.
Usage:
  1. Install Replit CLI: `npm i -g @replit/replit-cli`
  2. Login: `replit login`
  3. Run this script in repo root: `python scripts/print_replit_commands.py`
  4. Copy output lines and run them in your shell to set secrets for the Repl.

Note: Keep your .env secret. This script only helps formatting commands; it does not transmit keys anywhere.
"""
import os
from pathlib import Path

DOTENV_PATH = Path.cwd() / '.env'

if not DOTENV_PATH.exists():
    print('# .env not found in repo root. Create .env first with your keys.')
    exit(1)

# Keys to export to Replit (only sensitive keys / required vars)
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

# Read .env
env = {}
with open(DOTENV_PATH, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            continue
        k, v = line.split('=', 1)
        env[k.strip()] = v.strip()

print('# Copy and run these commands after `replit login` and while in your Repl shell')
print('# Example: replit secrets set TELEGRAM_TOKEN "<value>"')
print()
for k in KEYS:
    v = env.get(k)
    if v is None or v == '':
        print(f'# SKIP {k}: not set in .env')
    else:
        # Escape double quotes
        safe = v.replace('"', '\\"')
        print(f'replit secrets set {k} "{safe}"')

print()
print('# After running the above, restart your Repl. The bot will read env vars at runtime.')
