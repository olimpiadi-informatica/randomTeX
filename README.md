# TODO for next year

- Generate the "answers sheet" in addition to each student's test.

---

# Usage `gen_example.py`

Installation:

    $ pipenv install

    $ pipenv run gen_example example

See the available options:

    $ pipenv run gen_example --help

# Format of the contest folder

The contest folder (For example, see the `example` folder) must contain:

- A file named `contest.tex` with the contest template
- The folders `algoritmi`, `logica` and `programmazione` each one containing:
    - A subfolder for each score value (e.g. `1pt`, `2pt`, ...). These will be used in lexicographical order.
    - Each of these folders should contain:
      - One `.tex` file for each exercise in that category/score. The order of the tasks within the folder will be automatically randomized.

## Format of problems

### Numeric answer Problem

If the problem requires to compute a numeric answer, you must include `__solutions__` in the problem's metadata. All the other elements of the metadata must be arrays having the same length.

```
---
num1: [2, 10, 6, 1]
num2: [5, 12, 6, 1]
__solutions__: [7, 22, 12, 2]
---

\begin{esercizio}{3}
What's the sum of {{num1}} and {{num2}}?

\rispostaaperta
\end{esercizio}
```

### Multiple-choice Problem

If the problem is a multiple-choice one, all metadata should be arrays of length **4**.

```
---
num1: [2, 10, 6, 1]
num2: [5, 12, 6, 1]
---

\begin{esercizio}{3}
What's the sum of {{num1}} and {{num2}}?

\rispostachiusa{7}{22}{12}{2}
\end{esercizio}
```