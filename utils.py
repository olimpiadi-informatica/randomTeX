#!/usr/bin/env python3

import glob
import os.path
import shutil
import subprocess

import jinja2
import ruamel.yaml

categories = ["logica", "programmazione", "algoritmi"]
category_header = [
    "\\sezionelogicomatematica",
    "\\sezioneprogrammazione",
    "\\sezionealgoritmi",
]
open_question_macro = "\\rispostaaperta"
closed_question_macro = "\\rispostachiusa"
solutions_key = "__solutions__"
letters = "1234"

spoiler_template = r"""
\newpage
\sezione{Soluzioni}
\begin{tabularx}{\linewidth}{|>{\hsize=1.0\hsize\centering\arraybackslash}X|>{\hsize=1.0\hsize\centering\arraybackslash}X|}
\hline
\textbf{Domanda} & \textbf{Soluzione} \\
\hline
<{ for sol in solutions }>
    ${loop.index}$ & ${sol}$ \\
    \hline
<{ endfor }>
\end{tabularx}
"""

env = jinja2.Environment(
    loader=jinja2.BaseLoader,
    block_start_string="<{",
    block_end_string="}>",
    variable_start_string="${",
    variable_end_string="}$",
    comment_start_string="{########",
    comment_end_string="########}",
)

default_context = {
    "nome": "Romeo",
    "cognome": "Er meglio der colosseo",
    "codice_form": "persero-scacchi-sparta-poteva-portava",
    "link_form": "https://docs.google.com/forms/d/e/1FAIpQLSczm1x6rkFHl9JJiAdlo0wWf8TjPydUJWt55L1nLOfQED7uZw/viewform?entry.537375987=",
    "ora_inizio": "16:00",
    "ora_fine": "17:30",
}

contest_template_cache = None


def find_questions(base):
    if not all(os.path.exists(base + "/" + cat) for cat in categories):
        raise RuntimeError(
            "Invalid directory! There should be: %s" % ", ".join(categories)
        )
    questions = []
    for cat in categories:
        points = sorted(glob.glob(base + "/" + cat + "/*"))
        cat_exercises = []
        for point in points:
            exercises = list(glob.glob(point + "/*.tex"))
            cat_exercises.append(exercises)
        questions.append(cat_exercises)
    return questions


def split_header(path):
    with open(path) as f:
        content = f.read()
    splitted = [c.strip() for c in content.split("---", 2)]
    if len(splitted) == 2:
        return splitted[0], splitted[1]
    elif len(splitted) == 3:
        return splitted[1], splitted[2]
    else:
        raise ValueError(
            "Exercise at %s does not contain 2 or 3 sections delimited by ---" % path
        )


def parse_question(path):
    header, body = split_header(path)
    meta = ruamel.yaml.safe_load(header)
    if not isinstance(meta, dict):
        raise ValueError(
            "Exercise at %s is malformed: metadata should be an object" % path
        )
    if solutions_key in meta:
        expected_len = len(meta[solutions_key])
    else:
        expected_len = None
    for k, v in meta.items():
        if k.startswith("__") and k != solutions_key:
            raise ValueError(
                "Exercise at %s is malformed: unknown reserved key %s" % (path, k)
            )
        if not isinstance(v, list):
            raise ValueError(
                "Exercise at %s is malformed: %s should be a list" % (path, k)
            )
        if expected_len is None:
            expected_len = len(v)
        if len(v) != expected_len:
            raise ValueError(
                "Exercise at %s is malformed: %s should be %d items long"
                % (path, k, expected_len)
            )
    return meta, body, expected_len


def render_question(path, meta, body, correct_index):
    context = {}
    for k, v in meta.items():
        if not k.startswith("__"):
            context[k] = v[correct_index]

    is_open = open_question_macro in body
    is_close = closed_question_macro in body
    has_solutions = solutions_key in meta

    if not (is_open ^ is_close):
        raise ValueError(
            "Exercise at %s is malformed: should use either %s or %s"
            % (path, closed_question_macro, open_question_macro)
        )
    if is_open and not has_solutions:
        raise ValueError(
            "Exercise at %s is malformed: it uses %s, therefore should declare %s"
            % (path, open_question_macro, solutions_key)
        )
    if has_solutions:
        solution = str(meta[solutions_key][correct_index])
    else:
        solution = letters[correct_index]

    return env.from_string(body).render(context), solution


def render_spoiler(solutions):
    return env.from_string(spoiler_template).render(solutions=solutions)


def render_contest(directory, rnd, all=None, context=None, spoiler=False):
    if context is None:
        context = default_context
    contest_path = directory + "/contest.tex"
    if not os.path.exists(contest_path):
        raise FileNotFoundError(contest_path)
    questions = ""
    solutions = []
    all_questions = find_questions(directory)
    sorted_questions = list(sorted(sum(sum(all_questions, []), [])))
    questions_order = []
    for header, cat_questions in zip(category_header, all_questions):
        questions += header + "\n"
        for points_questions in cat_questions:
            if all is None:
                rnd.shuffle(points_questions)
            for question in points_questions:
                question_index = sorted_questions.index(question)
                questions_order.append(question_index)
                meta, body, num_combinations = parse_question(question)
                if all is not None:
                    if all < num_combinations:
                        correct_indexes = [all]
                    else:
                        correct_indexes = [rnd.randint(0, num_combinations - 1)]
                else:
                    correct_indexes = [rnd.randint(0, num_combinations - 1)]
                for correct_index in correct_indexes:
                    rendered, solution = render_question(
                        question, meta, body, correct_index
                    )
                    questions += rendered + "\n"
                    questions += "%" * 100
                    questions += "\n"
                    solutions.append(solution)

    if spoiler:
        solutions_page = render_spoiler(solutions)
    else:
        solutions_page = ""

    global contest_template_cache
    if contest_template_cache is None:
        with open(contest_path) as f:
            contest = f.read()
        contest_template_cache = env.from_string(contest)
    return (
        contest_template_cache.render(
            questions=questions,
            solutions=solutions_page,
            **context,
        ),
        solutions,
        questions_order,
    )


def open_pdf(path):
    if shutil.which("open"):
        cmd = "open"
    elif shutil.which("evince"):
        cmd = "evince"
    elif shutil.which("xdg-open"):
        cmd = "xdg-open"
    else:
        raise RuntimeError("Cannot find a proper program to open the pdf!")
    subprocess.check_call([cmd, path])


def encrypt_pdf(source, target, password):
    subprocess.check_call(
        ["pdftk", source, "output", target, "user_pw", password, "encrypt_128bit"]
    )
