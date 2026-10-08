"""Standing rule (2026-10-08): every YouTube title mixes English with the channel's own language
(Telugu or Hindi). Never pure Telugu / pure Hindi."""
import ast
import glob
import re

import pytest

FILES = (glob.glob("src/mahanavi/content/*.py") + glob.glob("channels/*/metadata.py")
         + glob.glob("channels/*/channel_config.py") + ["ramana/src/metadata.py"])


def _title_lists():
    for f in FILES:
        tree = ast.parse(open(f, encoding="utf-8").read())
        for n in ast.walk(tree):
            if isinstance(n, ast.Assign) and isinstance(n.value, (ast.List, ast.Tuple)):
                names = [t.id for t in n.targets if isinstance(t, ast.Name)]
                if any("TITLE" in x.upper() for x in names):
                    for e in n.value.elts:
                        if isinstance(e, ast.Constant) and isinstance(e.value, str):
                            yield f, names[0], e.value


@pytest.mark.parametrize("f,name,title", list(_title_lists()))
def test_title_has_english_word(f, name, title):
    assert re.search(r"[A-Za-z]{3,}", re.sub(r"\{[^}]*\}", "", title)), f"{f}:{name}: {title!r} has no English word"
