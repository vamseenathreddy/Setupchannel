from channels.jesus import bank, metadata


def test_bank_has_60_unique_verses_with_all_fields():
    vs = bank.load_verses()
    assert len(vs) == 60
    assert len({v["ref_en"] for v in vs}) == 60
    for v in vs:
        for f in ("text_en", "text_te", "ref_en", "ref_te", "apply_en", "apply_te"):
            assert v[f].strip(), (v["id"], f)


def test_next_unused_never_repeats():
    seen, used = [], []
    while (v := bank.next_unused(used)) is not None:
        used.append(v["id"]); seen.append(v["id"])
    assert len(seen) == len(set(seen)) == 60


def test_quiz_row_has_correct_answer_among_four_distinct_options():
    for v in bank.load_verses()[:10]:
        row = bank.quiz_row(v)
        opts = [row[f"opt_{c}"][3:] for c in "abcd"]
        assert len(set(opts)) == 4 and v["ref_en"] in opts
        assert row["opt_" + row["correct_letter"].lower()][3:] == v["ref_en"]


def test_quiz_title_does_not_reveal_the_reference():
    v = bank.load_verses()[0]
    assert v["ref_en"] not in metadata.title(bank.quiz_row(v))
    assert v["ref_en"] in metadata.title(bank.quote_row(v))


def test_trivia_rows_valid():
    from channels.jesus import bank, metadata
    qs = bank.load_trivia()
    assert len(qs) >= 30
    for q in qs:
        assert q["answer"] in q["options"] and len(set(q["options"])) == 4
        r = bank.trivia_row(q)
        assert r[f"opt_{r['correct_letter'].lower()}"].endswith(q["answer"])
        assert len(metadata.title(r)) <= 100
