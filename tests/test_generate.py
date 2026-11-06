import csv

from tacticlens.data import generate_llm_sms as g


def test_clean_strips_preamble_and_quotes():
    assert g.clean('Here\'s an SMS:\n"Your parcel is held. Pay at <URL>"') == "Your parcel is held. Pay at <URL>"
    assert g.clean("Hey, running late!\nSee you soon") == "Hey, running late! See you soon"


def test_clean_replaces_placeholders():
    assert g.clean("Verify by visiting [fake link]. Expired.") == "Verify by visiting <URL>. Expired."
    assert g.clean("Call [phone number] now") == "Call <PHONE> now"
    assert g.clean("Hey [Name], quick - can you send the notes?") == "Hey, quick - can you send the notes?"
    assert g.clean("Shop at [www.shop.com](https://www.shop.com) now! **50% off**") == "Shop at https://www.shop.com now! 50% off"


def test_prompts_never_name_a_tactic():
    banned = ("urgen", "scarc", "authorit", "fear", "threat", "flatter", "reciproc", "guilt")
    for label, tmpl in g.PROMPTS.items():
        for sender, topic in g.SMISHING_TOPICS:
            p = tmpl.format(sender=sender, topic=topic).lower()
            assert not any(b in p for b in banned), (label, p)


def test_run_writes_and_resumes(tmp_path):
    calls = []

    def fake(model, prompt, seed):
        calls.append(model)
        return f"Message from {model} seed {seed}"

    out = tmp_path / "llm_sms.csv"
    counts = {"smishing": 3, "spam": 1, "ham": 2}
    assert g.run(out, ["m1", "m2"], counts, generate=fake, log=lambda *_: None) == 12
    assert g.run(out, ["m1", "m2"], counts, generate=fake, log=lambda *_: None) == 0  # resume: nothing left
    rows = list(csv.DictReader(open(out, encoding="utf-8")))
    assert len(rows) == 12 and {r["MODEL"] for r in rows} == {"m1", "m2"}
    assert {r["LABEL"] for r in rows} == {"smishing", "spam", "ham"}


def test_leaks_are_detected():
    assert g.is_leak("Apply now for a part time job training new scam detectors!")
    assert g.is_leak("Contact us via https://fakeurl.com")
    assert g.is_leak("This is fake. Delete this message.")
    assert not g.is_leak("Your parcel is held. Pay the fee at <URL> today.")
