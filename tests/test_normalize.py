from tacticlens.data.normalize import dedupe_key, normalize


def test_masks_url_email_phone():
    t = normalize("Pay at http://sbi-kyc.xyz/login or mail help@bank.co.in, call +91 98765 43210 NOW!")
    assert "<URL>" in t and "<EMAIL>" in t and "<PHONE>" in t
    assert "NOW!" in t  # case and punctuation kept


def test_bare_domain_and_shortener():
    assert normalize("visit bit.ly/abc today") == "visit <URL> today"
    assert normalize("go to prize-now.top") == "go to <URL>"


def test_money_is_not_a_phone():
    assert normalize("You won Rs 10,000 today") == "You won Rs 10,000 today"


def test_html_and_whitespace():
    assert normalize("<b>Hello</b>&nbsp;&amp;   bye\n") == "Hello & bye"


def test_unicode_nfc():
    assert normalize("café") == "café"


def test_none_and_dedupe_key():
    assert normalize(None) == ""
    assert dedupe_key("Hello, World!!") == dedupe_key("hello world")
