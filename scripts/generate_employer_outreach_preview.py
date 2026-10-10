#!/usr/bin/env python3
"""
Generate personalized employer outreach emails for Hunter-stamped decision maker contacts.
"""
import os
import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root))

from dotenv import load_dotenv
load_dotenv(_root / ".env")

import app.models  # noqa: F401
from app.database import SessionLocal
from app.models.company import Company
from app.models.crm import CrmAccount
from app.services.employer_outreach_templates import (
    generate_raas_economics_email,
    generate_unfilled_robot_job_email,
    generate_no_capex_pilot_email,
)


def main():
    db = SessionLocal()
    try:
        # Fetch buyer accounts that have contacts
        accts = (
            db.query(CrmAccount)
            .filter(CrmAccount.account_type == "buyer", CrmAccount.contact_email.isnot(None))
            .all()
        )
        
        print(f"\n============================================================")
        print(f"   READY FOR ROBOTS - EMPLOYER OUTREACH TEMPLATE PREVIEW")
        print(f"============================================================\n")
        print(f"Found {len(accts)} Hunter-verified buyer accounts in CRM:\n")
        
        for acct in accts:
            company = db.query(Company).filter(Company.id == acct.company_id).first()
            company_name = company.name if company else "Target Employer"
            email = acct.contact_email
            
            # Extract meta if present
            meta = dict(company.crm_metadata or {}) if company else {}
            title = meta.get("outreach_contact_title") or "Operations Lead"
            name = meta.get("outreach_contact_name") or email.split("@")[0].replace(".", " ").title()
            
            print(f"------------------------------------------------------------")
            print(f"🏢 Company: {company_name}")
            print(f"👤 Contact: {name} [{title}] <{email}>")
            print(f"------------------------------------------------------------")
            
            # Generate Angle 1
            t1 = generate_raas_economics_email(company_name=company_name, contact_name=name, job_title=title)
            print(f"\n[ANGLE 1 - RaaS vs. CapEx Financials (CFO / VP Ops)]")
            print(f"SUBJECT: {t1['subject']}")
            print(f"\nBODY:\n{t1['body']}")
            
            # Generate Angle 2
            t2 = generate_unfilled_robot_job_email(company_name=company_name, contact_name=name, job_title=title)
            print(f"[ANGLE 2 - Unfilled Robot Jobs & Operations]")
            print(f"SUBJECT: {t2['subject']}")
            print(f"\nBODY:\n{t2['body']}")
            
            print("=" * 60 + "\n")
            
    finally:
        db.close()


if __name__ == "__main__":
    main()
