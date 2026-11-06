from tacticlens.config import PROJECT_ROOT
from tacticlens.taxonomy.mapping import load_taxonomy
from tacticlens.taxonomy.roles import p4g_role


def tax():
    return load_taxonomy(PROJECT_ROOT / "configs" / "taxonomy.yaml")


def test_ten_tactics_in_three_groups():
    t = tax()
    assert t.tactic_ids == [f"T{i}" for i in range(1, 11)]
    assert {t.group(x) for x in t.tactic_ids} == {"legitimate", "pressure", "manipulative"}


def test_mapping_is_case_and_hyphen_insensitive():
    t = tax()
    assert t.map_labels("p4g", ["Logical_Appeal", "donation information"]) == ["T1"]
    assert t.map_labels("mentalmanip", ["Playing the Victim Role", "Intimidation"]) == ["T8", "T9"]
    assert t.map_labels("mentalmanip", ["Persuasion or Seduction"]) == ["T6", "T7"]
    assert t.map_labels("psyscam", ["Social Proof"]) == ["X_SOCIAL_PROOF"]
    # spellings used in the real released files
    assert t.map_labels("mentalmanip", ["Playing Victim Role", "Playing Servant Role"]) == ["T8"]
    assert t.map_labels("p4g", ["praise-user"]) == ["T7"]
    assert t.map_labels("psyscam", ["Urgency and Scarcity (continued)", "Scarcity and urgency"]) == ["T5"]
    assert t.map_labels("psyscam", ["Authority and Impersonation (additional)"]) == ["T3"]


def test_unmapped_labels_are_counted():
    t = tax()
    assert t.map_labels("p4g", ["made-up-label", "greeting"]) == []
    rows = t.unmapped_rows()
    assert {"dataset": "p4g", "label": "made up label", "count": 1} in rows
    assert all(r["label"] != "greeting" for r in rows)  # greeting maps to none on purpose


def test_p4g_roles():
    assert p4g_role(0) == "actor" and p4g_role("1") == "target" and p4g_role("EE") == "target"
    assert p4g_role("weird") == "unknown"
