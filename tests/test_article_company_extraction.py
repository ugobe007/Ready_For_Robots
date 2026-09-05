"""Company extraction from multi-company headlines (actor vs comparison clause)."""

from app.scrapers.news_scraper import NewsScraper, extract_company_from_article_text

NIKE_TYSON_HEADLINE = (
    "Nike Axes 775 Warehouse Jobs As Robots Replace Workers "
    "— Joining GM and Tyson in Automation Wave"
)


def test_nike_headline_not_attributed_to_tyson_in_comparison_clause():
    db_lookup = {
        "tyson": ("Tyson", "Food Processing & Manufacturing"),
        "tyson foods": ("Tyson Foods", "Food Processing & Manufacturing"),
    }
    name, industry = extract_company_from_article_text(NIKE_TYSON_HEADLINE, db_lookup=db_lookup)
    assert name == "Nike"
    assert industry == "Retail"


def test_news_scraper_wrapper_uses_same_logic():
    scraper = NewsScraper.__new__(NewsScraper)
    scraper._db_company_lookup = {"tyson": ("Tyson", "Food Processing & Manufacturing")}
    name, _ = scraper._extract_company_from_text(NIKE_TYSON_HEADLINE)
    assert name == "Nike"
