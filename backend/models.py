from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class QRToken(Base):
    __tablename__ = "qr_tokens"
    
    id = Column(Integer, primary_key=True)
    token = Column(String, unique=True, index=True)
    patient_id = Column(String)
    hospital_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    used = Column(Boolean, default=False)
    used_at = Column(DateTime, nullable=True)
    
    documents = relationship("Document", back_populates="qr_token")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True)
    qr_token_id = Column(Integer, ForeignKey("qr_tokens.id"))
    document_id = Column(String, unique=True)
    patient_id = Column(String)
    document_type = Column(String)
    file_path = Column(String)
    source = Column(String)
    retrieved_at = Column(DateTime, default=datetime.utcnow)
    extracted_data = Column(Text, nullable=True)
    
    qr_token = relationship("QRToken", back_populates="documents")
    findings = relationship("Finding", back_populates="document")

class Finding(Base):
    __tablename__ = "findings"
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    category = Column(String)
    severity = Column(String)
    billed_item = Column(String)
    description = Column(Text)
    expected_value = Column(String, nullable=True)
    observed_value = Column(String, nullable=True)
    evidence = Column(Text)
    suggested_question = Column(Text)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    document = relationship("Document", back_populates="findings")

class BillItem(Base):
    __tablename__ = "bill_items"
    
    id = Column(Integer, primary_key=True)
    patient_id = Column(String)
    description = Column(String)
    quantity = Column(Float)
    unit_price = Column(Float)
    total = Column(Float)
    date = Column(DateTime)
    document_id = Column(Integer, ForeignKey("documents.id"))
