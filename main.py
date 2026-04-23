#!/usr/bin/env python3
import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

def main():
    try:
        if len(sys.argv) > 1 and sys.argv[1] in ["--minimal", "-m"]:
            import venture_minimal
            import asyncio
            asyncio.run(venture_minimal.run_minimal())
        else:
            import venture_tui
            venture_tui.main()
    except Exception as e:
        print(f"\033[31m[!] Venture Error: {e}\033[0m")
        sys.exit(1)

if __name__ == "__main__":
    main()
