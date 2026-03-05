"""
RFP Marketplace & Government Tender Scraper
============================================
Scrapes automation RFP marketplaces and government procurement sites for direct buyer intent.

Target sites:
- Qviro.com - automation project marketplace
- JobToRob.com - global robotics tenders
- Automate America - factory automation RFQs
- RFPBot.com - RFP discovery platform
- SAM.gov - US federal contracts (HUGE budgets)
- GSA.gov - US government procurement
- TED.europa.eu - EU tenders (thousands yearly)
- TendersInfo.com - global government contracts
- Biddingo.com - worldwide procurement
- MERX.com - Canadian government contracts

These are HIGHEST-VALUE leads - government + enterprise contracts with confirmed budgets.
"""
import logging
from typing import List, Dict, Any
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from app.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class RFPMarketplaceScraper(BaseScraper):
    """
    Scrapes RFP/project marketplaces for automation buyer intent.
    """
    
    def __init__(self):
        super().__init__(name="rfp_marketplace")
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def scrape_qviro(self, url: str) -> List[Dict[str, Any]]:
        """
        Scrape Qviro automation project marketplace.
        Example: https://qviro.com/match/projects
        """
        results = []
        try:
            resp = requests.get(url, headers=self.headers, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Qviro-specific parsing logic
            # This is a placeholder - needs real scraping logic based on site structure
            projects = soup.find_all('div', class_='project-card')  # Example selector
            
            for project in projects[:10]:  # Limit to recent projects
                try:
                    title = project.find('h3')
                    description = project.find('p', class_='description')
                    company = project.find('span', class_='company-name')
                    
                    if title and description:
                        results.append({
                            'company_name': company.text.strip() if company else "Unknown Company",
                            'signal_type': 'rfp_posted',
                            'signal_text': f"RFP: {title.text.strip()} - {description.text.strip()}",
                            'url': url,
                            'detected_at': datetime.utcnow(),
                            'source': 'Qviro Project Marketplace',
                            'industry': 'Manufacturing',  # Derive from content
                            'confidence': 0.95,  # High confidence - direct RFP posting
                        })
                except Exception as e:
                    logger.warning(f"Failed to parse Qviro project: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Qviro scrape failed for {url}: {e}")
        
        return results
    
    def scrape_jobtorob(self, url: str) -> List[Dict[str, Any]]:
        """
        Scrape JobToRob robotics tender database.
        Example: https://jobtorob.com/global-robotics-command-center-tenders
        """
        results = []
        try:
            resp = requests.get(url, headers=self.headers, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # JobToRob-specific parsing
            tenders = soup.find_all('div', class_='tender-item')  # Example selector
            
            for tender in tenders[:10]:
                try:
                    title = tender.find('h3')
                    org = tender.find('span', class_='organization')
                    desc = tender.find('div', class_='tender-description')
                    
                    if title:
                        results.append({
                            'company_name': org.text.strip() if org else "Government Entity",
                            'signal_type': 'government_contract',
                            'signal_text': f"Robotics Tender: {title.text.strip()}",
                            'url': url,
                            'detected_at': datetime.utcnow(),
                            'source': 'JobToRob Tenders',
                            'industry': 'Government',
                            'confidence': 0.90,
                        })
                except Exception as e:
                    logger.warning(f"Failed to parse JobToRob tender: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"JobToRob scrape failed for {url}: {e}")
        
        return results
    
    def scrape_automate_america(self, url: str) -> List[Dict[str, Any]]:
        """
        Scrape Automate America RFQ board.
        Example: https://automateamerica.com/automation-rfqs-and-projects/
        """
        results = []
        try:
            resp = requests.get(url, headers=self.headers, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Automate America-specific parsing
            rfqs = soup.find_all('div', class_='rfq-listing')  # Example selector
            
            for rfq in rfqs[:10]:
                try:
                    title = rfq.find('h4')
                    company = rfq.find('span', class_='company')
                    details = rfq.find('p', class_='rfq-details')
                    
                    if title:
                        results.append({
                            'company_name': company.text.strip() if company else "Manufacturer",
                            'signal_type': 'factory_automation',
                            'signal_text': f"Factory Automation RFQ: {title.text.strip()}",
                            'url': url,
                            'detected_at': datetime.utcnow(),
                            'source': 'Automate America RFQs',
                            'industry': 'Manufacturing',
                            'confidence': 0.95,
                        })
                except Exception as e:
                    logger.warning(f"Failed to parse Automate America RFQ: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Automate America scrape failed for {url}: {e}")
        
        return results
    
    def scrape_government_tender(self, url: str, source_name: str) -> List[Dict[str, Any]]:
        """
        Generic scraper for government tender sites.
        Handles SAM.gov, GSA.gov, TED, TendersInfo, Biddingo, MERX, RFPBot.
        """
        results = []
        try:
            resp = requests.get(url, headers=self.headers, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Generic tender parsing - look for common patterns
            # Most tender sites use similar structures: title, agency/company, description, value
            tender_containers = (
                soup.find_all('div', class_=['tender', 'opportunity', 'listing', 'result']) or
                soup.find_all('article') or
                soup.find_all('li', class_=['item', 'result'])
            )
            
            for tender in tender_containers[:15]:  # Government sites have many results
                try:
                    # Try to find title/heading
                    title_elem = (
                        tender.find('h2') or tender.find('h3') or 
                        tender.find('h4') or tender.find('a', class_='title')
                    )
                    
                    # Try to find organization/agency
                    org_elem = (
                        tender.find(class_=['agency', 'organization', 'department', 'company']) or
                        tender.find('span', text=lambda t: t and ('Agency' in t or 'Dept' in t))
                    )
                    
                    # Try to find description
                    desc_elem = tender.find('p', class_=['description', 'summary', 'detail'])
                    
                    if title_elem:
                        title_text = title_elem.get_text(strip=True)
                        org_text = org_elem.get_text(strip=True) if org_elem else "Government Agency"
                        desc_text = desc_elem.get_text(strip=True)[:200] if desc_elem else ""
                        
                        # Only include if robotics/automation related
                        combined_text = f"{title_text} {desc_text}".lower()
                        automation_keywords = ['robot', 'automat', 'unmanned', 'autonomous', 'cobot', 'amr']
                        
                        if any(keyword in combined_text for keyword in automation_keywords):
                            results.append({
                                'company_name': org_text,
                                'signal_type': 'government_contract',
                                'signal_text': f"Gov Tender: {title_text}",
                                'url': url,
                                'detected_at': datetime.utcnow(),
                                'source': source_name,
                                'industry': 'Government',
                                'confidence': 0.95,  # Government = confirmed budget
                            })
                
                except Exception as e:
                    logger.debug(f"Failed to parse tender item: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"{source_name} scrape failed for {url}: {e}")
        
        return results
    
    def scrape(self, url: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Route to appropriate scraper based on URL.
        """
        if 'qviro.com' in url:
            return self.scrape_qviro(url)
        elif 'jobtorob.com' in url:
            return self.scrape_jobtorob(url)
        elif 'automateamerica.com' in url:
            return self.scrape_automate_america(url)
        elif 'rfpbot.com' in url:
            return self.scrape_government_tender(url, "RFPBot")
        elif 'sam.gov' in url:
            return self.scrape_government_tender(url, "SAM.gov Federal Contracts")
        elif 'gsa.gov' in url:
            return self.scrape_government_tender(url, "GSA.gov")
        elif 'ted.europa.eu' in url:
            return self.scrape_government_tender(url, "TED EU Tenders")
        elif 'tendersinfo.com' in url:
            return self.scrape_government_tender(url, "TendersInfo Global")
        elif 'biddingo.com' in url:
            return self.scrape_government_tender(url, "Biddingo")
        elif 'merx.com' in url:
            return self.scrape_government_tender(url, "MERX Canada")
        else:
            logger.warning(f"Unknown RFP marketplace: {url}")
            return []


def scrape_rfp_marketplaces() -> List[Dict[str, Any]]:
    """
    Scrape all RFP marketplace targets.
    Returns list of signals with direct buyer intent.
    """
    from app.scrapers.scrape_targets import get_targets
    
    scraper = RFPMarketplaceScraper()
    all_signals = []
    
    targets = get_targets(scraper="rfp_marketplace", active_only=True)
    logger.info(f"Scraping {len(targets)} RFP marketplace targets")
    
    for target in targets:
        try:
            logger.info(f"Scraping {target.label}: {target.url}")
            signals = scraper.scrape(target.url)
            all_signals.extend(signals)
            logger.info(f"Found {len(signals)} projects/RFPs from {target.label}")
        except Exception as e:
            logger.error(f"Failed to scrape {target.label}: {e}")
            continue
    
    logger.info(f"Total RFP signals found: {len(all_signals)}")
    return all_signals
