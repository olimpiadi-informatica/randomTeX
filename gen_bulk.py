#!/usr/bin/env python3

import argparse
import csv
import datetime
import json
import logging
import multiprocessing.dummy as mp
import os
import random
import shutil
import tempfile

import progressbar

import compilation
import utils

progressbar.streams.wrap_stderr()
logger = logging.getLogger("gen_bulk")


def process_user(user, args, work_dir):
    contest_dir = args.contest_dir

    rnd = random.Random(int(user["seed"]))
    tex, sol, order = utils.render_contest(contest_dir, rnd, context=user)
    user["solutions"] = ":".join(sol)
    user["questions_order"] = ":".join(map(str, order))

    filename = user["filename"]
    password = user["pdf_password"]
    target = os.path.join(args.output_pdf, filename)
    if os.path.exists(target):
        logger.warning("File %s already present, skipping...", target)
        return user

    with tempfile.NamedTemporaryFile(prefix=filename) as f:
        compilation.compile(tex, f.name, work_dir)
        if args.no_enc:
            shutil.move(f.name, target)
        else:
            logger.info("Encrypting PDF %s -> %s", f.name, target)
            utils.encrypt_pdf(f.name, target, password)

    return user


def generate(args, work_dir, users):
    contest_dir = args.contest_dir

    compilation.setup(contest_dir, work_dir)
    os.makedirs(args.output_pdf, exist_ok=True)

    def process(user):
        return process_user(user, args, work_dir)

    result = []
    widgets = [
        "[",
        progressbar.SimpleProgress(),
        " / ",
        progressbar.Percentage(),
        "] ",
        progressbar.Bar(),
        " ",
        progressbar.Timer(),
        " | ",
        progressbar.AdaptiveETA(samples=datetime.timedelta(seconds=10)),
    ]
    with mp.Pool(args.num_cores) as pool:
        for res in progressbar.progressbar(
            pool.imap_unordered(process, users),
            max_value=len(users),
            redirect_stdout=True,
            widgets=widgets,
        ):
            if res:
                result.append(res)
    headers = list(result[0].keys())
    with open(args.output_csv, "w") as f:
        writer = csv.DictWriter(f, headers)
        writer.writeheader()
        writer.writerows(result)


def main(args):
    with open(args.users_csv) as f:
        reader = csv.DictReader(f)
        users = list(reader)

    if args.work_dir:
        generate(args, args.work_dir, users)
    else:
        with tempfile.TemporaryDirectory() as work_dir:
            generate(args, work_dir, users)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-dir",
        "-w",
        help="Working directory for the compilation",
    )
    parser.add_argument(
        "--num-cores",
        "-j",
        help="Number of parallel compilations",
        type=int,
    )
    parser.add_argument("--verbose", "-v", help="Verbose output", action="store_true")
    parser.add_argument("--no-enc", help="Do not encrypt the pdfs", action="store_true")
    parser.add_argument("contest_dir", help="Directory with the contest")
    parser.add_argument("users_csv", help="Path to the csv file with the students data")
    parser.add_argument(
        "output_pdf",
        help="Directory of where to save the compiled pdf files",
    )
    parser.add_argument(
        "output_csv",
        help="Path where to save the CSV with the solutions",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    )

    main(args)