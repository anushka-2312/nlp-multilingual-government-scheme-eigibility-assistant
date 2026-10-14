#!/usr/bin/env python3
"""Terminal chat:  python run_cli.py   (type 'quit' to exit, 'reset' to start over)."""
import sys

from app.dialogue import Assistant, Session
from app.i18n import t


def main():
    bot, s = Assistant(), Session()
    print(t("welcome", "en"), "\n")
    while True:
        try:
            msg = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if msg.lower() in {"quit", "exit", "q"}:
            break
        if msg:
            print("\nbot>", bot.handle(s, msg)["reply"], "\n")


if __name__ == "__main__":
    sys.exit(main())
