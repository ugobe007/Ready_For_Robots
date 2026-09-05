from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Contact(Base):
    __tablename__ = 'contacts'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    title = Column(String)
    email = Column(String, index=True)
    linkedin_url = Column(String)
    confidence_score = Column(Integer)

    company = relationship("Company", back_populates="contacts")