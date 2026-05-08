from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    authors = Column(Text)
    abstract = Column(Text)
    venue = Column(String(200))
    year = Column(Integer, index=True)
    doi = Column(String(100), unique=True, index=True)
    pdf_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    citations = relationship(
        "Citation",
        foreign_keys="Citation.citing_id",
        back_populates="citing_paper",
        cascade="all, delete-orphan"
    )
    cited_by = relationship(
        "Citation",
        foreign_keys="Citation.cited_id",
        back_populates="cited_paper",
        cascade="all, delete-orphan"
    )


class Citation(Base):
    __tablename__ = "citations"

    id = Column(Integer, primary_key=True, index=True)
    citing_id = Column(Integer, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True)
    cited_id = Column(Integer, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True)
    context = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    citing_paper = relationship("Paper", foreign_keys=[citing_id], back_populates="citations")
    cited_paper = relationship("Paper", foreign_keys=[cited_id], back_populates="cited_by")

    __table_args__ = (
        Index("ix_citations_citing_cited", "citing_id", "cited_id", unique=True),
    )
