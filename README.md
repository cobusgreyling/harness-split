![harness-split](assets/header.png)

# harness-split

The model file is not the harness. A harness is the split across model, tools, memory, evals, and gates.

This CLI walks a directory and puts each file in one bucket. The first matching directory name, from the left, wins. If no directory matches, the filename stem is used. Anything else is unclassified and stays out of the split. No model is called.

On the checked-in fixture, tools are the largest bucket. The model bucket is 2 files and 19% of classified lines. Tools, memory, evals, and gates hold the other 81%.

## Run

From the repo root. Python 3.11 or newer. No install and no API key.

```bash
python3 -m harness_split fixtures/tiny-harness
python3 -m harness_split --verbose fixtures/tiny-harness
python3 -m unittest discover -s tests -v
```

## Score

```
Harness split: model 19% · tools 40% · memory 17% · evals 14% · gates 10%
Not the model: 81% of classified lines sit in tools, memory, evals, or gates.

bucket        files  lines  share
------------  -----  -----  -----
model         2      11     19%
tools         3      23     40%
memory        2      10     17%
evals         2      8      14%
gates         1      6      10%
unclassified  0      0      --
```

Lines are `splitlines()` counts on UTF-8 text. A file that is not UTF-8 counts as 0 lines and is still classified. Shares are integer percents of classified lines and sum to 100. Unclassified files are printed and left out of that split.

## Rules

Directory names, in order: `model` `models` `prompt` `prompts`, then `tool` `tools`, `memory` `memories`, `eval` `evals`, `gate` `gates`.

Stems, only when no directory matches: `model` `prompt` `system`, `tool` `tools`, `memory`, `eval` `evals`, `gate` `policy`.

Hidden files and `__pycache__` are skipped. `tools/model.json` is tools, because the directory wins.

## Fixture

`fixtures/tiny-harness` is a claim desk with no carrier and no model call. `prompt.md` and `model.json` sit at the root and count as model by stem. The other eight files sit in `tools/`, `memory/`, `evals/`, and `gates/`.

## License

MIT
