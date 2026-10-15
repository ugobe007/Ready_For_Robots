from types import SimpleNamespace

from app.services.buyer_opportunity import industry_company_check as icc

HOME = "Welcome to Grand Lodge Resorts. We operate 40 hotels and resorts across the United States."
ABOUT = "Founded in 1950, our family runs full-service restaurants inside every property."


def _page(url, text, links=()):
    return SimpleNamespace(url=url, final_url=url, text=text, links=list(links))


def _fetcher(pages):
    calls = []

    def fetch(url):
        calls.append(url)
        return pages.get(url, _page(url, ""))

    fetch.calls = calls
    return fetch


def _company(**kw):
    base = dict(
        company_id=1, name="Grand Lodge", domain="grandlodge.com", raw_value="Hospitality",
        candidates=["hotel", "restaurant"], default=["hotel"],
    )
    return icc.CompanyToCheck(**{**base, **kw})


SITE = {
    "https://grandlodge.com/": _page(
        "https://grandlodge.com/", HOME,
        links=[("/about-us", "About us"), ("https://other.com/about", "About"), ("/careers", "Careers")],
    ),
    "https://grandlodge.com/about-us": _page("https://grandlodge.com/about-us", ABOUT),
}


def test_gathers_homepage_and_own_about_page():
    fetch = _fetcher(SITE)
    pages = icc.gather_site_pages("grandlodge.com", fetch)
    assert [p.url for p in pages] == ["https://grandlodge.com/", "https://grandlodge.com/about-us"]
    assert "https://other.com/about" not in fetch.calls


def test_pick_with_quote_on_the_page_is_decided():
    choose = lambda c, pages, t: {"picks": [  # noqa: E731
        {"industry": "hotel", "quote": "We operate 40 hotels and resorts"},
        {"industry": "restaurant", "quote": "runs full-service restaurants inside every property"},
    ]}
    d = icc.check_company(_company(), fetch=_fetcher(SITE), choose=choose)
    assert d.status == "decided"
    assert d.industries == ["hotel", "restaurant"]
    assert d.evidence[1] == {
        "industry": "restaurant",
        "quote": "runs full-service restaurants inside every property",
        "url": "https://grandlodge.com/about-us",
    }


def test_invented_short_or_off_list_picks_go_to_review():
    choose = lambda c, pages, t: {"picks": [  # noqa: E731
        {"industry": "hotel", "quote": "We run the best casinos in Nevada"},
        {"industry": "hotel", "quote": "hotels"},
        {"industry": "casino", "quote": "We operate 40 hotels and resorts"},
    ]}
    d = icc.check_company(_company(), fetch=_fetcher(SITE), choose=choose)
    assert d.status == "review" and d.industries == []
    assert d.suggestion == ["hotel"]
    assert [r["why"] for r in d.rejected] == [
        "quote not found on the fetched pages",
        f"quote shorter than {icc.MIN_QUOTE_WORDS} words",
        "not a candidate",
    ]
    assert d.reason == "no pick had a quote found on the site"


def test_no_pick_keeps_model_reason():
    choose = lambda c, pages, t: {"picks": [], "no_pick_reason": "Site only lists careers"}  # noqa: E731
    d = icc.check_company(_company(), fetch=_fetcher(SITE), choose=choose)
    assert d.status == "review" and d.reason == "Site only lists careers"


def test_no_website_or_unreadable_site_is_review_without_model_call():
    def choose(*_):
        raise AssertionError("model must not be called")

    assert icc.check_company(_company(domain=None), fetch=_fetcher({}), choose=choose).reason == "no website on record"
    d = icc.check_company(_company(), fetch=_fetcher({}), choose=choose)
    assert d.status == "review" and d.reason == "website returned no readable text"


def test_prompt_is_closed_to_the_row_candidates():
    pages = icc.gather_site_pages("grandlodge.com", _fetcher(SITE))
    prompt = icc.build_prompt(_company(notes="Pick per company"), pages, icc.load_taxonomy())
    assert "- hotel: Hotels and resorts" in prompt and "- casino:" not in prompt
    assert "Mapping note: Pick per company" in prompt
    assert icc._tool(["hotel", "restaurant"])["input_schema"]["properties"]["picks"]["items"]["properties"]["industry"]["enum"] == ["hotel", "restaurant"]


def test_review_markdown_lists_suggestion_and_quotes():
    choose = lambda c, pages, t: {"picks": [{"industry": "hotel", "quote": "We operate 40 hotels and resorts"}]}  # noqa: E731
    decided = icc.check_company(_company(), fetch=_fetcher(SITE), choose=choose)
    review = icc.check_company(_company(company_id=2, name="Mystery Co", domain=None), fetch=_fetcher({}), choose=choose)
    md = icc.render_review_markdown({"taxonomy_version": "v1.3", "model": "m", "decisions": [decided.as_dict(), review.as_dict()]})
    assert "- Mystery Co (no website, Hospitality): suggest hotel; candidates hotel, restaurant. no website on record" in md
    assert '  - hotel: "We operate 40 hotels and resorts" (https://grandlodge.com/)' in md
