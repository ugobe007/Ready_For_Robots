"""
Ontological Scraper - Parse any URL for automation intent signals
Extracts semantic patterns indicating automation readiness
"""
import re
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
import time

from app.services.signal_classifier import classify_signals_with_fallback


class OntologicalScraper:
    """Parse any URL for automation intent signals using the shared signal classifier."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
    def scrape_url(self, url: str, delay: float = 1.0) -> Dict:
        """
        Parse a URL and extract all automation intent signals
        
        Args:
            url: Any web URL (company page, LinkedIn, news article, etc.)
            delay: Delay between requests (for rate limiting)
            
        Returns:
            Dict with company info and detected signals
        """
        time.sleep(delay)
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            text_raw = self._extract_text_raw(soup)
            text_content = text_raw.lower()
            
            # Extract company name (best guess)
            company_name = self._extract_company_name(soup, url)
            
            # Detect signals (preserve case for SemanticParser / rules)
            signals = self._detect_signals(text_raw, source_url=url)
            
            # Extract industry hints
            industry = self._extract_industry(text_content)
            
            return {
                'company_name': company_name,
                'url': url,
                'industry': industry,
                'signals': signals,
                'signal_count': len(signals),
                'scraped_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'url': url,
                'scraped_at': datetime.utcnow().isoformat()
            }
    
    def scrape_linkedin_company(self, company_slug: str) -> Dict:
        """
        Scrape LinkedIn company page
        Note: LinkedIn has aggressive anti-scraping. Use sparingly.
        
        Args:
            company_slug: LinkedIn company identifier (e.g., 'amazon')
            
        Returns:
            Dict with company info and signals
        """
        url = f"https://www.linkedin.com/company/{company_slug}/"
        
        # LinkedIn requires authentication - this is a placeholder
        # For production, you'd need LinkedIn API access or authenticated session
        print(f"⚠️  LinkedIn scraping requires authentication. URL: {url}")
        print("    Consider using LinkedIn Sales Navigator API or Phantombuster")
        
        return {
            'company_name': company_slug,
            'url': url,
            'note': 'LinkedIn requires authentication - use API for production',
            'scraped_at': datetime.utcnow().isoformat()
        }
    
    def _extract_text_raw(self, soup: BeautifulSoup) -> str:
        """Extract clean text from HTML (original casing for signal classifier)."""
        for script in soup(['script', 'style', 'nav', 'header', 'footer']):
            script.decompose()
        
        text = soup.get_text(separator=' ', strip=True)
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def _extract_company_name(self, soup: BeautifulSoup, url: str) -> str:
        """Extract company name from page"""
        # Try meta tags
        og_title = soup.find('meta', property='og:site_name')
        if og_title:
            return og_title.get('content', '').strip()
        
        # Try title tag
        title = soup.find('title')
        if title:
            title_text = title.get_text().strip()
            # Clean common suffixes
            title_text = re.sub(r'\s*[\|\-].*$', '', title_text)
            return title_text
        
        # Fallback to domain
        domain = re.search(r'https?://(?:www\.)?([^/]+)', url)
        if domain:
            return domain.group(1).split('.')[0].title()
        
        return 'Unknown Company'
    
    def _extract_industry(self, text: str) -> Optional[str]:
        """Detect industry from content"""
        industry_keywords = {
            'Logistics': ['logistics', 'warehouse', 'distribution', 'fulfillment', 'shipping'],
            'Healthcare': ['hospital', 'healthcare', 'medical', 'patient', 'clinic'],
            'Manufacturing': ['manufacturing', 'production', 'factory', 'assembly', 'plant'],
            'Hospitality': ['hotel', 'resort', 'restaurant', 'hospitality', 'lodging'],
            'Automotive': ['automotive', 'dealership', 'vehicle', 'car dealer'],
            'Food Service': ['restaurant', 'food service', 'catering', 'cafeteria'],
            'Retail': ['retail', 'store', 'shopping', 'ecommerce']
        }
        
        for industry, keywords in industry_keywords.items():
            if any(kw in text for kw in keywords):
                return industry
        
        return None
    
    def _detect_signals(self, text: str, *, source_url: str = "") -> List[Dict]:
        """
        Classify via ontology + rules engine + fallback (same path as intelligence / SERP scrapers).
        """
        if not (text or "").strip():
            return []

        types = classify_signals_with_fallback(text, article_url=source_url or "")
        if not types or types == ["news"]:
            return []

        signals: List[Dict] = []
        seen = set()
        snippet = text[:400].strip()
        lower_snippet = snippet.lower()

        for signal_type in types:
            if signal_type in seen:
                continue
            seen.add(signal_type)
            signals.append({
                'signal_type': signal_type,
                'strength': 0.75,
                'raw_text': lower_snippet or snippet,
                'keyword_matches': 1,
                'source_url': source_url or 'ontological_scraper',
            })

        return signals
    
    def scrape_multiple_urls(self, urls: List[str], delay: float = 2.0) -> List[Dict]:
        """
        Scrape multiple URLs with rate limiting
        
        Args:
            urls: List of URLs to scrape
            delay: Delay between requests (seconds)
            
        Returns:
            List of company dicts with signals
        """
        results = []
        
        for i, url in enumerate(urls):
            print(f"Scraping {i+1}/{len(urls)}: {url}")
            result = self.scrape_url(url, delay=delay)
            results.append(result)
            
            # Be respectful - delay between requests
            if i < len(urls) - 1:
                time.sleep(delay)
        
        return results


# Example usage
if __name__ == "__main__":
    scraper = OntologicalScraper()
    
    # Test URLs
    test_urls = [
        "https://www.amazon.com/about",
        "https://www.walmart.com/",
        "https://www.marriott.com/",
    ]
    
    print("🔍 Ontological Scraper - Testing")
    print("=" * 60)
    
    for url in test_urls:
        print(f"\nScraping: {url}")
        result = scraper.scrape_url(url, delay=1.0)
        
        if 'error' not in result:
            print(f"  Company: {result['company_name']}")
            print(f"  Industry: {result.get('industry', 'Unknown')}")
            print(f"  Signals: {result['signal_count']}")
            
            for signal in result.get('signals', [])[:3]:
                print(f"    • {signal['signal_type']}: {signal['raw_text'][:80]}...")
        else:
            print(f"  Error: {result['error']}")
