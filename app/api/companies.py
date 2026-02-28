from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.company import Company
from app.models.contact import Contact

router = APIRouter()

@router.get("/{company_id}")
def get_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return {"id": company.id, "name": company.name, "website": company.website, "industry": company.industry}

@router.get("/{company_id}/contacts")
def get_company_contacts(company_id: int, db: Session = Depends(get_db)):
    contacts = db.query(Contact).filter(Contact.company_id == company_id).all()
    return [{"id": c.id, "name": f"{c.first_name} {c.last_name}", "title": c.title, "email": c.email} for c in contacts]

@router.get("/")
def list_companies(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    companies = db.query(Company).offset(skip).limit(limit).all()
    return [{"id": c.id, "name": c.name, "website": c.website, "industry": c.industry} for c in companies]