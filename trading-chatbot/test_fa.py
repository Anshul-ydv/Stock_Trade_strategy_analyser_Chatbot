import asyncio
import traceback
import sys
import os

from src.fa_engine import evaluate_fundamentals

if __name__ == "__main__":
    try:
        res = evaluate_fundamentals("RELIANCE")
        print(res)
    except Exception as e:
        traceback.print_exc()
        sys.exit(1)
