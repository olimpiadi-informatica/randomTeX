#!/usr/bin/env python3

import argparse
import glob
import logging
import os
import secrets
import string

logger = logging.getLogger("gen_password")

sources = []

alphabet = set(string.ascii_lowercase) - set("lmn")


def load_data():
    # already loaded
    if sources:
        return

    here = os.path.dirname(os.path.abspath(__file__))
    files = glob.glob(here + "/password_data/*.txt")
    for path in sorted(files):
        logger.debug("Loading password data from %s", path)
        cur = []
        with open(path) as f:
            data = f.read().splitlines()
            for w in data:
                if all(c in alphabet for c in w) and 3 <= len(w) <= 8:
                    cur.append(w)
        sources.append(cur)


def gen_password(method="last"):
    load_data()
    if method == "last":
        parts = list(map(secrets.choice, [sources[-1]] * 5))
    elif method == "all":
        parts = list(map(secrets.choice, sources))
    else:
        raise ValueError("Unsupported method")
    return "-".join(parts)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "number", help="Number of passwords to generate", type=int, default=1, nargs="?"
    )
    parser.add_argument("--verbose", "-v", help="Verbose output", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    )

    for _ in range(args.number):
        print(gen_password())