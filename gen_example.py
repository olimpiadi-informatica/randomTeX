#!/usr/bin/env python3

import argparse
import logging
import os
import random
import tempfile

import utils
import compilation

logger = logging.getLogger("gen_example")


def generate(args, work_dir, rnd):
    contest_dir = args.contest_dir
    all_mode = [None]
    if args.all:
        all_mode = list(range(4))

    for mode in all_mode:
        target = args.output
        if mode is not None:
            target_dir = os.path.dirname(target)
            name = os.path.splitext(os.path.basename(target))[0]
            name = "{}-{}.pdf".format(name, mode)
            target = os.path.join(target_dir, name)
        tex, sol, order = utils.render_contest(
            contest_dir, rnd, all=mode, spoiler=args.spoiler
        )

        compilation.setup(contest_dir, work_dir)
        compilation.compile(tex, target, work_dir)
        logger.info("Compiled file save at %s", target)
        logger.info("Solutions: %s", ", ".join(sol))
        logger.info("Order: %s", ", ".join(map(str, order)))

        if args.open:
            logger.info("Opening pdf...")
            utils.open_pdf(target)


def main(args):
    if args.seed is not None:
        logger.info("Using seed: %d", args.seed)
        rnd = random.Random(args.seed)
    else:
        rnd = random.Random()

    if args.work_dir:
        generate(args, args.work_dir, rnd)
    else:
        with tempfile.TemporaryDirectory() as work_dir:
            generate(args, work_dir, rnd)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a random pdf")
    parser.add_argument(
        "--seed",
        type=int,
        help="Seed to use for the question selection",
    )
    parser.add_argument(
        "--all",
        "-a",
        help="Generate all the possible combinations instead of a random one",
        action="store_true",
    )
    parser.add_argument(
        "--work-dir",
        "-w",
        help="Working directory for the compilation",
    )
    parser.add_argument(
        "--open",
        help="Open the compiled file after the compilation",
        action="store_true",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Path of where to save the compiled pdf",
        default="test.pdf",
    )
    parser.add_argument(
        "--spoiler", help="Add a final page with the solutions", action="store_true"
    )
    parser.add_argument("--verbose", "-v", help="Verbose output", action="store_true")
    parser.add_argument("contest_dir", help="Directory with the contest")

    args = parser.parse_args()

    if args.seed is not None and args.all:
        raise ValueError("Cannot combine --seed and --all")

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    )

    main(args)