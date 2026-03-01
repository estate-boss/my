# Replit Setup (Quick)

This file explains how to configure Replit secrets for this project and start the bot.

1. Install Replit CLI

```bash
npm i -g @replit/replit-cli
```

2. Login to Replit

```bash
replit login
```

3. In your local repo run the helper to produce `replit secrets set` commands:

```bash
python scripts/print_replit_commands.py
```

4. Copy the printed commands into your shell (while in your target Repl) and run them. Example:

```bash
replit secrets set TELEGRAM_TOKEN "7658..."
replit secrets set GEMINI_API_KEY "..."
# etc.
```

5. In Replit add a run command (or create `.replit`):

```
run = "python telegram_bybit_profit_hunter.py"
```

6. Start the Repl. Check the console logs and test in Telegram.

Notes:
- Use **testnet** Bybit keys when testing. Set `PAPER_MODE=true` for safe simulation.
- Replit Secrets are encrypted and not stored in the repo.
