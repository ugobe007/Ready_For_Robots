# Ready_For_Robots
Robot opportunity scout — a web scraper that discovers robot sales opportunities from eBay and Craigslist.

## Features
- Searches **eBay** (Buy It Now listings) and **Craigslist** (multiple cities) for robots
- Configurable keywords, sources, cities, and result limits
- Outputs to **stdout**, **JSON**, or **CSV**
- Deduplicates listings across keyword runs

## Requirements
- Python 3.9+

## Installation
```bash
pip install -r requirements.txt
```

## Usage
```bash
# Print results to stdout (searches eBay + Craigslist with default keywords)
python main.py

# Custom keywords
python main.py --keywords "robot,robotic arm,KUKA,Fanuc"

# Only scrape eBay, save to JSON
python main.py --sources ebay --output results.json

# Save to CSV with a higher result limit
python main.py --max 100 --output results.csv

# Specific Craigslist cities
python main.py --sources craigslist --cities "https://sfbay.craigslist.org,https://seattle.craigslist.org"
```

### Options
| Flag | Description | Default |
|------|-------------|---------|
| `--keywords` | Comma-separated search terms | `robot,robotic arm,industrial robot` |
| `--sources` | Sources to scrape: `ebay`, `craigslist` | `ebay,craigslist` |
| `--max` | Max results per source | `50` |
| `--output` | Output file (`.json` or `.csv`). Omit to print to stdout | stdout |
| `--cities` | Comma-separated Craigslist base URLs | 5 major US cities |

## Project Structure
```
.
├── main.py                        # CLI entry point
├── requirements.txt
├── scraper/
│   ├── scrapers/
│   │   ├── base.py                # BaseScraper + Listing dataclass
│   │   ├── ebay.py                # eBay scraper
│   │   └── craigslist.py          # Craigslist scraper
│   └── utils.py                   # save_json / save_csv / print helpers
└── tests/
    └── test_scraper.py            # pytest test suite
```

## Running Tests
```bash
python -m pytest tests/ -v
```
