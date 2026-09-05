from bs4 import BeautifulSoup
from app.scrapers.base_scraper import BaseScraper

MULTI_BRAND_HOTELS = [
    "marriott", "hilton", "hyatt", "ihg", "wyndham",
    "best western", "radisson", "accor", "choice hotels"
]


class HotelDirectoryScraper(BaseScraper):
    """Scrapes hotel directories for hospitality robotics leads."""

    def parse(self, html: str, url: str):
        soup = BeautifulSoup(html, "html.parser")

        # Yellow Pages specific selectors
        listings = soup.select("div.result, div.v-card, article.result") or []

        # Generic fallback selectors
        if not listings:
            listings = (
                soup.select(".hotel-item, .property-card, .listing-item, article")
                or soup.select("div[class*='hotel'], div[class*='property']")
            )

        for item in listings:
            name_el = item.select_one("a.business-name, h2.n, h2, h3, h1, .hotel-name, .property-name")
            link_el = item.select_one("a.business-name[href], a[href]")
            location_el = item.select_one(".locality, .location, .address, .city, [class*='location']")
            rating_el = item.select_one(".stars, .rating, [class*='star'], [class*='rating']")
            rooms_el = item.select_one(".rooms, [class*='room']")

            name = name_el.get_text(strip=True) if name_el else None
            if not name:
                continue

            website = link_el["href"] if link_el else None
            location = location_el.get_text(strip=True) if location_el else ""
            rating_text = rating_el.get_text(strip=True) if rating_el else "0"
            rooms_text = rooms_el.get_text(strip=True) if rooms_el else "0"

            # Extract numeric values
            try:
                stars = float("".join(filter(lambda c: c.isdigit() or c == ".", rating_text)) or 0)
            except ValueError:
                stars = 0
            try:
                rooms = int("".join(filter(str.isdigit, rooms_text)) or 0)
            except ValueError:
                rooms = 0

            parts = location.split(",")
            city = parts[0].strip() if parts else location
            state = parts[1].strip() if len(parts) > 1 else ""

            is_brand = any(b in name.lower() for b in MULTI_BRAND_HOTELS)

            company = self.save_company({
                "name": name,
                "website": website,
                "industry": "Hospitality",
                "sub_industry": "Hotel",
                "employee_estimate": rooms if rooms else None,
                "location_city": city,
                "location_state": state,
                "location_country": "US",
                "source": url
            })

            # Create signals based on qualification criteria
            if stars >= 3 or rooms >= 100 or is_brand:
                strength = 0.3
                if stars >= 3:
                    strength += 0.2
                if rooms >= 100:
                    strength += 0.3
                if is_brand:
                    strength += 0.2
                strength = min(1.0, round(strength, 2))

                self.save_signal(company.id, {
                    "signal_type": "hospitality_fit",
                    "signal_text": f"{name} | Stars: {stars} | Rooms: {rooms} | Brand: {is_brand}",
                    "signal_strength": strength,
                    "source_url": url
                })