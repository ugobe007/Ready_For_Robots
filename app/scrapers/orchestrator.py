"""
Scraper Orchestrator - Production Data Pipeline
===============================================
Coordinates all scrapers, data processing, and lead generation
Similar to pythh.ai's investor/startup discovery pipeline
"""
import logging
import sys
from pathlib import Path

# Allow `python3 app/scrapers/orchestrator.py` from repo root (same as `python3 -m app.scrapers.orchestrator`).
_root = Path(__file__).resolve().parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import SessionLocal
from app.models.company import Company
from app.models.signal import Signal
from app.models.score import Score
from app.services.scoring_engine import compute_scores
from app.scrapers.news_scraper_enhanced import EnhancedNewsScraper as NewsScraper
from app.scrapers.job_board_scraper_enhanced import EnhancedJobBoardScraper as JobBoardScraper
from app.scrapers.serp_scraper_enhanced import EnhancedSerpScraper as SerpScraper
from app.scrapers.serp_scraper import EXPANSION_QUERIES
from app.scrapers.scrape_targets import get_urls, get_news_queries, get_oem_discovery_queries, OEM_INTELLIGENCE_TARGETS
from app.services.oem_need_scorer import score as oem_need_score, OEMNeedScore
from app.services.lead_filter import is_junk

logger = logging.getLogger(__name__)


class ScraperOrchestrator:
    """
    Orchestrates automated data pipeline for lead discovery
    
    Architecture (pythh.ai style):
    1. Scrape multiple sources in parallel
    2. Extract companies + signals
    3. Enrich with additional data
    4. Score using inference engine
    5. Classify as HOT/WARM/COLD
    6. Store in database
    """
    
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
        self.stats = {
            'companies_discovered': 0,
            'signals_detected': 0,
            'hot_leads_found': 0,
            'sources_scraped': 0,
            'errors': [],
            # OEM / XBOT pipeline stats
            'oem_prospects_found': 0,
            'oem_hot': 0,
            'oem_warm': 0,
        }
        
    def run_full_pipeline(self, max_sources: int = 100):
        """
        Run complete automated discovery pipeline
        
        Args:
            max_sources: Maximum number of sources to scrape
        """
        logger.info("=" * 60)
        logger.info("SCRAPER ORCHESTRATOR - Full Pipeline Starting")
        logger.info("=" * 60)
        
        start_time = datetime.now(timezone.utc)
        
        try:
            # Step 1: News scraping (highest value signals)
            self._run_news_pipeline()
            
            # Step 2: Job board scraping (labor signals)
            self._run_job_pipeline()
            
            # Step 3: SERP scraping (expansion signals)
            self._run_serp_pipeline()
            
            # Step 4: Company enrichment
            self._enrich_companies()
            
            # Step 5: Scoring & classification
            self._score_all_companies()
            
            # Step 6: Quality check
            self._quality_check()

            # Step 7: OEM / XBOT pipeline (robot company discovery for StageGate)
            self._run_oem_pipeline()

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            self.stats['errors'].append(str(e))
        
        finally:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            self._log_stats(duration)
            
    def _run_news_pipeline(self):
        """News scraping with manufacturing focus"""
        logger.info("→ Step 1: News Pipeline")
        
        try:
            scraper = NewsScraper(db=self.db)
            
            # Manufacturing-specific queries
            manufacturing_queries = [
                "quality control problems manufacturing 2026",
                "production bottleneck factory automation",
                "workplace safety incident manufacturing",
                "warehouse automation investment",
                "packaging line modernization",
                "manufacturing labor shortage 2026",
                "factory automation robotics",
                "material handling automation",
            ]
            
            # General high-value queries
            general_queries = get_news_queries()[:20]  # Top 20 queries
            
            all_queries = manufacturing_queries + general_queries
            
            scraper.run_intent_queries(queries=all_queries)
            
            self.stats['sources_scraped'] += len(all_queries)
            logger.info(f"  ✓ News pipeline completed: {len(all_queries)} queries")
            
        except Exception as e:
            logger.error(f"  ✗ News pipeline failed: {e}")
            self.stats['errors'].append(f"News: {e}")
    
    def _run_job_pipeline(self):
        """Job board scraping for labor signals"""
        logger.info("→ Step 2: Job Board Pipeline")
        
        try:
            scraper = JobBoardScraper(db=self.db)
            
            # Get top job board URLs
            urls = get_urls("job_board")[:30]  # Top 30 job boards
            
            scraper.run(urls)
            
            self.stats['sources_scraped'] += len(urls)
            logger.info(f"  ✓ Job pipeline completed: {len(urls)} boards")
            
        except Exception as e:
            logger.error(f"  ✗ Job pipeline failed: {e}")
            self.stats['errors'].append(f"Jobs: {e}")
    
    def _run_serp_pipeline(self):
        """SERP scraping for expansion signals"""
        logger.info("→ Step 3: SERP Pipeline")
        
        try:
            scraper = SerpScraper(db=self.db)
            scraper.run()
            self.stats['sources_scraped'] += len(EXPANSION_QUERIES)
            logger.info("  ✓ SERP pipeline completed (%d queries)", len(EXPANSION_QUERIES))
            
        except Exception as e:
            logger.error(f"  ✗ SERP pipeline failed: {e}")
            self.stats['errors'].append(f"SERP: {e}")
    
    def _enrich_companies(self):
        """Enrich company data with additional context"""
        logger.info("→ Step 4: Company Enrichment")
        
        try:
            # Find companies without employee counts
            companies = self.db.query(Company).filter(
                Company.employee_estimate == None
            ).limit(100).all()
            
            enriched = 0
            for company in companies:
                # TODO: Integrate with Clearbit, ZoomInfo, or similar API
                # For now, estimate based on industry + signals
                if company.industry == 'Logistics':
                    company.employee_estimate = 500  # Default estimate
                elif company.industry == 'Healthcare':
                    company.employee_estimate = 1000
                else:
                    company.employee_estimate = 250
                
                enriched += 1
            
            self.db.commit()
            logger.info(f"  ✓ Enriched {enriched} companies")
            
        except Exception as e:
            logger.error(f"  ✗ Enrichment failed: {e}")
            self.stats['errors'].append(f"Enrichment: {e}")
    
    def _score_all_companies(self):
        """Score all companies using inference engine"""
        logger.info("→ Step 5: Scoring & Classification")
        
        try:
            # Get companies without scores or stale scores (>24h old)
            cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            
            companies = self.db.query(Company).outerjoin(Score).filter(
                (Score.id == None) | (Score.last_calculated_at < cutoff)
            ).limit(200).all()
            
            scored = 0
            hot_count = 0
            
            for company in companies:
                try:
                    # Get company signals
                    signals = self.db.query(Signal).filter(
                        Signal.company_id == company.id
                    ).all()
                    
                    # Compute scores
                    score_data = compute_scores(company, signals)

                    score = self.db.query(Score).filter(
                        Score.company_id == company.id
                    ).first()

                    if not score:
                        score = Score(company_id=company.id)
                        self.db.add(score)

                    score.automation_score = float(score_data.get("automation_score", 0) or 0)
                    score.labor_pain_score = float(score_data.get("labor_pain_score", 0) or 0)
                    score.expansion_score = float(score_data.get("expansion_score", 0) or 0)
                    score.robotics_fit_score = float(score_data.get("robotics_fit_score", 0) or 0)
                    score.overall_intent_score = float(score_data.get("overall_intent_score", 0) or 0)

                    from app.services.lead_filter import classify_lead

                    junk, _jr, pri = classify_lead(company, score, signals)
                    if not junk and pri.tier == "HOT":
                        hot_count += 1

                    scored += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to score company {company.id}: {e}")
                    continue
            
            self.db.commit()
            
            self.stats['companies_discovered'] = scored
            self.stats['hot_leads_found'] = hot_count
            
            logger.info(f"  ✓ Scored {scored} companies ({hot_count} HOT)")
            
        except Exception as e:
            logger.error(f"  ✗ Scoring failed: {e}")
            self.stats['errors'].append(f"Scoring: {e}")
    
    def _quality_check(self):
        """Quality checks on discovered data"""
        logger.info("→ Step 6: Quality Check")
        
        try:
            # Count total signals
            signal_count = self.db.query(func.count(Signal.id)).scalar()
            
            # Count companies
            company_count = self.db.query(func.count(Company.id)).scalar()
            
            self.stats['signals_detected'] = signal_count

            logger.info("  ✓ Quality Check:")
            logger.info("    • Total Companies: %s", company_count)
            logger.info("    • Total Signals: %s", signal_count)
            logger.info(
                "    • HOT tier (this pipeline run classifier): %s",
                self.stats.get("hot_leads_found", 0),
            )
            
        except Exception as e:
            logger.error(f"  ✗ Quality check failed: {e}")
    
    def _run_oem_pipeline(self):
        """
        XBOT: Robot OEM company discovery for StageGate outreach.
        Delegates to oem_discovery service (persisted HOT/WARM prospects).
        """
        logger.info("→ Step 7: XBOT OEM Pipeline (StageGate prospect discovery)")
        try:
            from app.services.oem_discovery import run_oem_discovery

            stats = run_oem_discovery(self.db, max_queries=30)
            self.stats["oem_prospects_found"] = stats.get("oem_prospects_found", 0)
            self.stats["oem_hot"] = stats.get("oem_hot", 0)
            self.stats["oem_warm"] = stats.get("oem_warm", 0)
            logger.info(
                f"  ✓ OEM pipeline: {self.stats['oem_prospects_found']} prospects | "
                f"{self.stats['oem_hot']} HOT | {self.stats['oem_warm']} WARM | "
                f"{stats.get('companies_created', 0)} new companies"
            )
        except Exception as e:
            logger.error(f"  ✗ OEM pipeline failed: {e}")
            self.stats["errors"].append(f"OEM: {e}")

    def _log_stats(self, duration: float):
        """Log final pipeline statistics"""
        logger.info("=" * 60)
        logger.info("PIPELINE COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Duration: {duration:.1f}s")
        logger.info(f"Sources Scraped: {self.stats['sources_scraped']}")
        logger.info(f"Companies Discovered: {self.stats['companies_discovered']}")
        logger.info(f"Signals Detected: {self.stats['signals_detected']}")
        logger.info(f"HOT Leads Found: {self.stats['hot_leads_found']}")
        logger.info(f"OEM Prospects (XBOT): {self.stats['oem_prospects_found']} total | "
                    f"{self.stats['oem_hot']} HOT | {self.stats['oem_warm']} WARM")

        if self.stats['errors']:
            logger.warning(f"Errors: {len(self.stats['errors'])}")
            for error in self.stats['errors'][:5]:  # Show first 5 errors
                logger.warning(f"  • {error}")
        
        logger.info("=" * 60)
    
    def close(self):
        """Close database connection"""
        self.db.close()


# CLI runner
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    orchestrator = ScraperOrchestrator()
    
    try:
        orchestrator.run_full_pipeline()
    finally:
        orchestrator.close()
