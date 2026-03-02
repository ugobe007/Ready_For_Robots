"""
Enrichment Service
==================
Enriches company and contact data using the ContactScraper.

Functions
---------
enrich_company(company_id)   — run contact discovery + return summary
enrich_contact(contact_id)   — attempt to resolve email / LinkedIn for one contact
enrich_top25()               — enrich every company in the current top-25 list
handle_enrichment_errors(e)  — log + return structured error dict
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.company import Company
from app.models.contact import Contact

logger = logging.getLogger(__name__)


# ── Public helpers ────────────────────────────────────────────────────────────

def enrich_company(company_id: int, db: Optional[Session] = None) -> dict:
    """
    Run contact discovery for a single company.

    Parameters
    ----------
    company_id : int
        DB primary key of the company to enrich.
    db : Session, optional
        Existing DB session; a new one is created if not supplied.

    Returns
    -------
    dict  with keys: company_id, company_name, contacts_added, contacts_found
    """
    close = False
    if db is None:
        db = SessionLocal()
        close = True

    try:
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            return handle_enrichment_errors(ValueError(f"Company {company_id} not found"))

        from app.scrapers.contact_scraper import ContactScraper
        scraper = ContactScraper(db)
        results = scraper.run_company(company)

        return {
            "company_id":     company_id,
            "company_name":   company.name,
            "contacts_found": len(results),
            "contacts": [
                {
                    "name":       f"{r.first_name} {r.last_name}",
                    "title":      r.title,
                    "linkedin":   r.linkedin_url,
                    "confidence": r.confidence_score,
                }
                for r in results
            ],
        }
    except Exception as e:
        return handle_enrichment_errors(e)
    finally:
        if close:
            db.close()


def enrich_contact(contact_id: int, db: Optional[Session] = None) -> dict:
    """
    Attempt to improve data quality for a single stored contact.
    Currently tries to fill in a LinkedIn URL if missing.

    Returns
    -------
    dict  with keys: contact_id, updated, detail
    """
    close = False
    if db is None:
        db = SessionLocal()
        close = True

    try:
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            return handle_enrichment_errors(ValueError(f"Contact {contact_id} not found"))

        if contact.linkedin_url:
            return {"contact_id": contact_id, "updated": False, "detail": "already has LinkedIn URL"}

        company = db.query(Company).filter(Company.id == contact.company_id).first()
        if not company:
            return {"contact_id": contact_id, "updated": False, "detail": "company not found"}

        # Re-run a targeted LinkedIn search using the stored title
        from app.scrapers.contact_scraper import ContactScraper
        scraper = ContactScraper(db)
        candidates = scraper._search_linkedin(company, contact.title or "VP of Operations")

        # Look for a candidate whose first/last name matches this contact
        full = f"{contact.first_name} {contact.last_name}".lower()
        for c in candidates:
            if f"{c.first_name} {c.last_name}".lower() == full and c.linkedin_url:
                contact.linkedin_url = c.linkedin_url
                contact.confidence_score = max(contact.confidence_score or 0, c.confidence_score)
                db.commit()
                return {"contact_id": contact_id, "updated": True, "linkedin_url": c.linkedin_url}

        return {"contact_id": contact_id, "updated": False, "detail": "no LinkedIn match found"}

    except Exception as e:
        return handle_enrichment_errors(e)
    finally:
        if close:
            db.close()


def enrich_top25(db: Optional[Session] = None) -> dict:
    """
    Run contact discovery for all companies in the current top-25 HOT list.

    Returns
    -------
    dict  with keys: companies_enriched, contacts_found
    """
    close = False
    if db is None:
        db = SessionLocal()
        close = True

    try:
        from app.scrapers.contact_scraper import ContactScraper
        scraper = ContactScraper(db)
        total = scraper.run_top25()
        return {"companies_enriched": 25, "contacts_found": total}
    except Exception as e:
        return handle_enrichment_errors(e)
    finally:
        if close:
            db.close()


def handle_enrichment_errors(error: Exception) -> dict:
    """Log and return a structured error response."""
    logger.error("[enrichment] error: %s", error, exc_info=True)
    return {"error": True, "detail": str(error)}
