from tacticlens.config import load_datasets_config
from tacticlens.data.loaders import (
    load_mentalmanip,
    load_p4g,
    load_psyscam,
    load_sms,
    parse_dialogue,
)
from tacticlens.taxonomy.mapping import load_taxonomy


def _setup(project):
    return load_datasets_config(project), load_taxonomy(project / "configs" / "taxonomy.yaml")


def test_p4g_turns_roles_spans_and_meta(project):
    cfg, tax = _setup(project)
    recs = load_p4g(cfg["datasets"]["p4g"], project, tax)
    ann = [r for r in recs if r.label_level == "turn"]
    assert ann and all(r.dataset == "p4g" and r.genre == "persuasion" for r in recs)
    er = [r for r in ann if r.role == "actor"]
    ee = [r for r in ann if r.role == "target"]
    assert er and ee and all(r.tactics == [] for r in ee)  # persuadee turns carry no tactics
    # two ER sentences per turn are joined into one turn; spans point at real sentences
    for r in er:
        r.validate()
        for s in r.spans:
            assert r.text[s.start:s.end].strip()
    assert any(r.meta.get("donation_ee") is not None for r in ann)
    # er_label_2 is read too: personal-story sentences also carry emotion-appeal (T4 + T2)
    assert any({"T4", "T2"} <= set(r.tactics) for r in er)
    unl = [r for r in recs if r.label_level == "none"]
    assert unl and all(r.tactics is None for r in unl)


def test_find_quote_ignores_case_spacing_punctuation():
    from tacticlens.data.loaders import find_quote
    text = "Dear user,\nyour account WILL be blocked -- verify now!"
    a, b = find_quote(text, "your account will be blocked, verify now")
    assert text[a:b] == "your account WILL be blocked -- verify now"
    assert find_quote(text, "something else entirely") is None


def test_parse_dialogue_formats():
    assert parse_dialogue("Person1: hi\nPerson2: hello there") == [("Person1", "hi"), ("Person2", "hello there")]
    assert parse_dialogue("Person1: hi Person2: hello") == [("Person1", "hi"), ("Person2", "hello")]


def test_mentalmanip_dialogue_level_labels(project):
    cfg, tax = _setup(project)
    recs = load_mentalmanip(cfg["datasets"]["mentalmanip"], project, tax)
    assert all(r.label_level == "dialogue" and r.tactics is None and r.role == "unknown" for r in recs)
    man = [r for r in recs if r.meta["manipulative"]]
    assert man and all(r.genre == "manipulation" and r.meta["dialogue_tactics"] for r in man)
    assert all(r.genre == "neutral" for r in recs if not r.meta["manipulative"])


def test_sms_both_formats(project):
    cfg, tax = _setup(project)
    h = load_sms("sms_human", cfg["datasets"]["sms_human"], project, tax)
    llm = load_sms("sms_llm", cfg["datasets"]["sms_llm"], project, tax)
    assert {r.meta["sms_label"] for r in h} <= {"ham", "spam", "smishing"}
    assert all(r.source == "human" for r in h) and all(r.source == "llm" for r in llm)
    assert all((r.genre == "neutral") == (r.meta["sms_label"] == "ham") for r in h + llm)
    assert any("<URL>" in r.text for r in h)


def test_generated_sms_is_cleaned_on_load(project):
    import pandas as pd
    cfg, tax = _setup(project)
    d = project / "data" / "raw" / "sms_llm_gen"
    pd.DataFrame([
        {"LABEL": "smishing", "TEXT": "Verify at [www.bank.com](https://www.bank.com) or [link] now", "MODEL": "m", "TOPIC": "t", "PROMPT_ID": "p1"},
        {"LABEL": "smishing", "TEXT": "Part-time job training new scam detectors, call now", "MODEL": "m", "TOPIC": "t", "PROMPT_ID": "p2"},
    ]).to_csv(d / "llm_sms.csv", index=False)
    recs = load_sms("sms_llm", cfg["datasets"]["sms_llm"], project, tax)
    assert [r.text for r in recs] == ["Verify at <URL> or <URL> now"]  # the leaking line is dropped


def test_psyscam_tactics_and_evidence_spans(project):
    cfg, tax = _setup(project)
    stats = {}
    recs = load_psyscam(cfg["datasets"]["psyscam"], project, tax, stats)
    assert recs and all(r.label_level == "turn" and r.tactics for r in recs)
    assert stats["evidence_found"] > 0 and stats["evidence_missing"] == 0
    for r in recs:
        r.validate()
        assert {s.tactic for s in r.spans} <= set(r.tactics)
        assert len(r.tactics) == 2 and r.dialogue_id.startswith("psyscam_9")
    # the two-fragment quote gives two spans for its tactic
    assert any(len([s for s in r.spans if s.tactic == r.spans[0].tactic]) >= 2 for r in recs)
