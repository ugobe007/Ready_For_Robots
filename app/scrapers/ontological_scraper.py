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


# Comprehensive ontological keyword mappings
SIGNAL_ONTOLOGY = {
    # Manufacturing operational signals
    'quality_bottleneck': [
        'quality issues', 'defect rate', 'quality control problems', 'scrap rate',
        'rework', 'quality bottleneck', 'inspection backlog', 'QA shortage',
        'quality inspection delay', 'defective products', 'reject rate'
    ],
    'safety_incident': [
        'workplace accident', 'safety incident', 'OSHA violation', 'injury rate',
        'worker injury', 'safety concern', 'hazardous conditions', 'safety fine',
        'accident investigation', 'safety training', 'PPE compliance'
    ],
    'production_capacity': [
        'production capacity', 'throughput limit', 'capacity constraint',
        'production bottleneck', 'capacity expansion', 'output increase',
        'manufacturing capacity', 'production limit', 'capacity utilization',
        'production volume', 'max capacity', 'capacity shortage'
    ],
    'warehouse_throughput': [
        'warehouse throughput', 'shipping delay', 'fulfillment backlog',
        'picking efficiency', 'warehouse capacity', 'distribution bottleneck',
        'order fulfillment', 'picking speed', 'packing rate', 'warehouse productivity'
    ],
    'packaging_automation': [
        'packaging line', 'packaging automation', 'packing station',
        'packaging efficiency', 'packaging bottleneck', 'packing speed',
        'packaging workforce', 'manual packaging', 'packaging capacity'
    ],
    'repetitive_process': [
        'repetitive task', 'manual process', 'repetitive motion',
        'assembly line work', 'repetitive strain', 'monotonous work',
        'manual labor intensive', 'repetitive operations'
    ],
    'material_handling': [
        'material handling', 'forklift', 'material transport',
        'inventory movement', 'warehouse logistics', 'material flow',
        'parts delivery', 'material transfer', 'goods movement'
    ],
    
    # Labor signals
    'labor_shortage': [
        'hiring', 'labor shortage', 'workforce shortage', 'staff shortage',
        'worker shortage', 'recruitment challenges', 'staffing crisis',
        'understaffed', 'difficulty hiring', 'hard to fill positions',
        'vacancy rate', 'open positions', 'employment gap'
    ],
    'labor_pain': [
        'turnover rate', 'retention issues', 'attrition', 'employee burnout',
        'overtime costs', 'labor cost increase', 'wage pressure',
        'agency workers', 'temp workers', 'labor inflation'
    ],
    
    # Strategic signals
    'strategic_hire': [
        'appoints', 'names', 'announces', 'joins as', 'promoted to',
        'chief operating officer', 'VP operations', 'VP supply chain',
        'director of operations', 'head of logistics', 'COO', 'CFO',
        'new leadership', 'executive hire', 'joins executive team'
    ],
    'capex': [
        'invests', 'investment', 'capital expenditure', 'facility expansion',
        'new facility', 'plant expansion', 'warehouse expansion',
        'distribution center', 'manufacturing facility', 'opens facility',
        'breaks ground', 'construction', 'renovation', 'modernization'
    ],
    'expansion': [
        'expands', 'expansion', 'growth', 'scales', 'opens new',
        'new location', 'new market', 'international expansion',
        'adds capacity', 'increases footprint', 'new facility'
    ],
    'funding_round': [
        'raises', 'funding round', 'Series A', 'Series B', 'Series C',
        'venture capital', 'investment', 'secures funding', 'closes round',
        'led by', 'investors', 'valuation', 'capital raise'
    ],
    'ma_activity': [
        'acquires', 'acquisition', 'merger', 'merges with', 'buys',
        'purchased', 'takes over', 'deal', 'transaction', 'consolidation'
    ],
    
    # Operational signals
    'job_posting': [
        'hiring', 'now hiring', 'seeking', 'looking for', 'recruiting',
        'positions available', 'job opening', 'apply now', 'join our team',
        'careers', 'employment opportunity'
    ],
    'news': [
        'announces', 'launches', 'introduces', 'unveils', 'releases',
        'partners with', 'collaboration', 'strategic partnership'
    ]
}


class OntologicalScraper:
    """Parse any URL for automation intent signals using semantic pattern matching"""
    
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
            
            # Extract text content
            text_content = self._extract_text(soup)
            
            # Extract company name (best guess)
            company_name = self._extract_company_name(soup, url)
            
            # Detect signals
            signals = self._detect_signals(text_content)
            
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
    
    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extract clean text from HTML"""
        # Remove script and style elements
        for script in soup(['script', 'style', 'nav', 'header', 'footer']):
            script.decompose()
        
        # Get text
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.lower()
    
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
    
    def _detect_signals(self, text: str) -> List[Dict]:
        """Detect all signals in text using ontological keywords"""
        signals = []
        
        for signal_type, keywords in SIGNAL_ONTOLOGY.items():
            # Find all keyword matches
            matches = []
            for keyword in keywords:
                if keyword in text:
                    # Extract context (50 chars before and after)
                    for match in re.finditer(re.escape(keyword), text):
                        start = max(0, match.start() - 50)
                        end = min(len(text), match.end() + 50)
                        context = text[start:end].strip()
                        matches.append(context)
            
            # If we found matches, create signal
            if matches:
                # Calculate strength based on number of matches
                strength = min(0.95, 0.6 + (len(matches) * 0.05))
                
                # Get best context (longest one)
                best_context = max(matches, key=len) if matches else matches[0]
                
                signals.append({
                    'signal_type': signal_type,
                    'strength': strength,
                    'raw_text': best_context,
                    'keyword_matches': len(matches),
                    'source_url': 'ontological_scraper'
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
