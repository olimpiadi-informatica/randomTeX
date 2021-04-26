#!/usr/bin/env python3

import glob
import logging
import os
import os.path
import random
import shutil
import string
import subprocess

logger = logging.getLogger("compilation")


def setup(contest_dir, work_dir):
    logger.info("Setting up work_dir: %s", work_dir)
    contest_files = glob.glob(contest_dir + "/**/*", recursive=True)
    for path in contest_files:
        if not os.path.isfile(path):
            continue
        relpath = path[len(contest_dir) + 1 :]
        work_path = os.path.join(work_dir, relpath)
        os.makedirs(os.path.dirname(work_path), exist_ok=True)
        logger.debug("Copying %s -> %s", path, work_path)
        shutil.copy(path, work_path)


def compile(tex_content, target, work_dir):
    seed = "".join(random.choices(string.ascii_letters, k=12))
    name = seed + "-" + os.path.splitext(os.path.basename(target))[0]
    tex_path = os.path.join(work_dir, name + ".tex")
    pdf_path = os.path.join(work_dir, name + ".pdf")

    logger.info("Starting compilation of %s", name)
    with open(tex_path, "w") as f:
        f.write(tex_content)
    res = subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", tex_path],
        cwd=work_dir,
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        logger.error(
            "Failed to compile %s:\nstderr:\n%s\n\nstdout:\n%s",
            tex_path,
            res.stderr,
            res.stdout,
        )
        raise RuntimeError("Failed to compile %s" % tex_path)
    logger.info("Compilation of %s completed" % name)
    shutil.move(pdf_path, target)

    garbage = glob.glob(work_dir + "/" + seed + "*")
    for path in garbage:
        logger.debug("Removing garbage file: %s", path)
        os.remove(path)
