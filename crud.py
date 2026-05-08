from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from models import Paper, Citation
from schemas import PaperCreate, PaperUpdate, CitationCreate
from fastapi import HTTPException, status


def get_paper(db: Session, paper_id: int):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper with id {paper_id} not found"
        )
    return paper


def get_papers(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    query: Optional[str] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    venue: Optional[str] = None,
    author: Optional[str] = None
):
    db_query = db.query(Paper)

    if query:
        db_query = db_query.filter(Paper.title.contains(query))
    if year_from:
        db_query = db_query.filter(Paper.year >= year_from)
    if year_to:
        db_query = db_query.filter(Paper.year <= year_to)
    if venue:
        db_query = db_query.filter(Paper.venue.contains(venue))
    if author:
        db_query = db_query.filter(Paper.authors.contains(author))

    return db_query.offset(skip).limit(limit).all()


def create_paper(db: Session, paper: PaperCreate):
    if paper.doi:
        existing = db.query(Paper).filter(Paper.doi == paper.doi).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Paper with DOI {paper.doi} already exists"
            )

    db_paper = Paper(**paper.model_dump())
    db.add(db_paper)
    db.commit()
    db.refresh(db_paper)
    return db_paper


def update_paper(db: Session, paper_id: int, paper: PaperUpdate):
    db_paper = get_paper(db, paper_id)
    update_data = paper.model_dump(exclude_unset=True)

    if paper.doi and paper.doi != db_paper.doi:
        existing = db.query(Paper).filter(Paper.doi == paper.doi).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Paper with DOI {paper.doi} already exists"
            )

    for key, value in update_data.items():
        setattr(db_paper, key, value)

    db.commit()
    db.refresh(db_paper)
    return db_paper


def delete_paper(db: Session, paper_id: int):
    db_paper = get_paper(db, paper_id)
    db.delete(db_paper)
    db.commit()
    return None


def paper_to_response(db: Session, paper: Paper):
    citations_count = db.query(Citation).filter(Citation.citing_id == paper.id).count()
    cited_by_count = db.query(Citation).filter(Citation.cited_id == paper.id).count()

    return {
        "id": paper.id,
        "title": paper.title,
        "authors": paper.authors,
        "abstract": paper.abstract,
        "venue": paper.venue,
        "year": paper.year,
        "doi": paper.doi,
        "pdf_url": paper.pdf_url,
        "created_at": paper.created_at,
        "updated_at": paper.updated_at,
        "citations_count": citations_count,
        "cited_by_count": cited_by_count
    }


def get_citation(db: Session, citation_id: int):
    citation = db.query(Citation).filter(Citation.id == citation_id).first()
    if not citation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Citation with id {citation_id} not found"
        )
    return citation


def get_citations(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    citing_id: Optional[int] = None,
    cited_id: Optional[int] = None
):
    db_query = db.query(Citation)

    if citing_id:
        db_query = db_query.filter(Citation.citing_id == citing_id)
    if cited_id:
        db_query = db_query.filter(Citation.cited_id == cited_id)

    return db_query.offset(skip).limit(limit).all()


def create_citation(db: Session, citation: CitationCreate):
    if citation.citing_id == citation.cited_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A paper cannot cite itself"
        )

    get_paper(db, citation.citing_id)
    get_paper(db, citation.cited_id)

    existing = db.query(Citation).filter(
        Citation.citing_id == citation.citing_id,
        Citation.cited_id == citation.cited_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Citation already exists"
        )

    db_citation = Citation(**citation.model_dump())
    db.add(db_citation)
    db.commit()
    db.refresh(db_citation)
    return db_citation


def batch_create_citations(db: Session, citations_data: List[CitationCreate]):
    created = 0
    failed = 0
    errors = []

    for idx, citation in enumerate(citations_data):
        try:
            if citation.citing_id == citation.cited_id:
                raise ValueError(f"Paper cannot cite itself")

            citing = db.query(Paper).filter(Paper.id == citation.citing_id).first()
            cited = db.query(Paper).filter(Paper.id == citation.cited_id).first()

            if not citing or not cited:
                raise ValueError(f"One or both papers do not exist")

            existing = db.query(Citation).filter(
                Citation.citing_id == citation.citing_id,
                Citation.cited_id == citation.cited_id
            ).first()
            if existing:
                raise ValueError(f"Citation already exists")

            db_citation = Citation(**citation.model_dump())
            db.add(db_citation)
            created += 1
        except Exception as e:
            failed += 1
            errors.append(f"Index {idx}: {str(e)}")

    db.commit()
    return {"created": created, "failed": failed, "errors": errors}


def delete_citation(db: Session, citation_id: int):
    db_citation = get_citation(db, citation_id)
    db.delete(db_citation)
    db.commit()
    return None
