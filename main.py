from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional

from database import engine, get_db
import models
import schemas
import crud
import graph_analyzer

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Academic Citation Graph API",
    description="REST API for managing academic papers and their citation relationships",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
def root():
    return {
        "name": "Academic Citation Graph API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "papers": "/api/v1/papers",
            "citations": "/api/v1/citations",
            "graph": "/api/v1/graph"
        }
    }


@app.post("/api/v1/papers/", response_model=schemas.PaperResponse, tags=["Papers"])
def create_paper(paper: schemas.PaperCreate, db: Session = Depends(get_db)):
    db_paper = crud.create_paper(db, paper)
    return crud.paper_to_response(db, db_paper)


@app.get("/api/v1/papers/", response_model=List[schemas.PaperResponse], tags=["Papers"])
def read_papers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    query: Optional[str] = Query(None, description="Search in title"),
    year_from: Optional[int] = Query(None, ge=1000),
    year_to: Optional[int] = Query(None, le=9999),
    venue: Optional[str] = None,
    author: Optional[str] = None,
    db: Session = Depends(get_db)
):
    papers = crud.get_papers(db, skip, limit, query, year_from, year_to, venue, author)
    return [crud.paper_to_response(db, paper) for paper in papers]


@app.get("/api/v1/papers/{paper_id}", response_model=schemas.PaperDetailResponse, tags=["Papers"])
def read_paper(paper_id: int, db: Session = Depends(get_db)):
    db_paper = crud.get_paper(db, paper_id)
    response_data = crud.paper_to_response(db, db_paper)
    response_data["citations"] = db_paper.citations
    response_data["cited_by"] = db_paper.cited_by
    return response_data


@app.patch("/api/v1/papers/{paper_id}", response_model=schemas.PaperResponse, tags=["Papers"])
def update_paper(
    paper_id: int,
    paper: schemas.PaperUpdate,
    db: Session = Depends(get_db)
):
    db_paper = crud.update_paper(db, paper_id, paper)
    return crud.paper_to_response(db, db_paper)


@app.delete("/api/v1/papers/{paper_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Papers"])
def delete_paper(paper_id: int, db: Session = Depends(get_db)):
    crud.delete_paper(db, paper_id)
    return None


@app.post("/api/v1/citations/", response_model=schemas.CitationDetailResponse, tags=["Citations"])
def create_citation(citation: schemas.CitationCreate, db: Session = Depends(get_db)):
    db_citation = crud.create_citation(db, citation)
    return {
        "id": db_citation.id,
        "citing_id": db_citation.citing_id,
        "cited_id": db_citation.cited_id,
        "context": db_citation.context,
        "created_at": db_citation.created_at,
        "citing_paper": crud.paper_to_response(db, db_citation.citing_paper),
        "cited_paper": crud.paper_to_response(db, db_citation.cited_paper)
    }


@app.post("/api/v1/citations/batch/", response_model=schemas.BatchCitationResponse, tags=["Citations"])
def batch_create_citations(citations: schemas.BatchCitationCreate, db: Session = Depends(get_db)):
    result = crud.batch_create_citations(db, citations.citations)
    return result


@app.get("/api/v1/citations/", response_model=List[schemas.CitationResponse], tags=["Citations"])
def read_citations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    citing_id: Optional[int] = Query(None, ge=1),
    cited_id: Optional[int] = Query(None, ge=1),
    db: Session = Depends(get_db)
):
    citations = crud.get_citations(db, skip, limit, citing_id, cited_id)
    return citations


@app.get("/api/v1/citations/{citation_id}", response_model=schemas.CitationDetailResponse, tags=["Citations"])
def read_citation(citation_id: int, db: Session = Depends(get_db)):
    db_citation = crud.get_citation(db, citation_id)
    return {
        "id": db_citation.id,
        "citing_id": db_citation.citing_id,
        "cited_id": db_citation.cited_id,
        "context": db_citation.context,
        "created_at": db_citation.created_at,
        "citing_paper": crud.paper_to_response(db, db_citation.citing_paper),
        "cited_paper": crud.paper_to_response(db, db_citation.cited_paper)
    }


@app.delete("/api/v1/citations/{citation_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Citations"])
def delete_citation(citation_id: int, db: Session = Depends(get_db)):
    crud.delete_citation(db, citation_id)
    return None


@app.get("/api/v1/graph/path", tags=["Graph Analysis"])
def find_citation_path(
    source_id: int = Query(..., ge=1),
    target_id: int = Query(..., ge=1),
    max_depth: int = Query(6, ge=1, le=20),
    reverse: bool = Query(False, description="Find reverse path (who cited whom)"),
    db: Session = Depends(get_db)
):
    crud.get_paper(db, source_id)
    crud.get_paper(db, target_id)

    if reverse:
        result = graph_analyzer.find_reverse_citation_path(db, source_id, target_id, max_depth)
    else:
        result = graph_analyzer.find_citation_path(db, source_id, target_id, max_depth)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No citation path found between paper {source_id} and {target_id}"
        )
    return result


@app.get("/api/v1/graph/influence/{paper_id}", response_model=schemas.InfluenceResponse, tags=["Graph Analysis"])
def get_paper_influence(paper_id: int, db: Session = Depends(get_db)):
    result = graph_analyzer.get_paper_influence(db, paper_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper with id {paper_id} not found"
        )
    return result


@app.get("/api/v1/graph/influential", response_model=List[schemas.InfluenceResponse], tags=["Graph Analysis"])
def get_influential_papers(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return graph_analyzer.get_influential_papers(db, limit)


@app.get("/api/v1/graph/common-citations", response_model=List[schemas.PaperResponse], tags=["Graph Analysis"])
def find_common_citations(
    paper_a: int = Query(..., ge=1),
    paper_b: int = Query(..., ge=1),
    db: Session = Depends(get_db)
):
    crud.get_paper(db, paper_a)
    crud.get_paper(db, paper_b)
    return graph_analyzer.find_common_citations(db, paper_a, paper_b)


@app.get("/api/v1/graph/co-citing", response_model=List[schemas.PaperResponse], tags=["Graph Analysis"])
def find_co_citing_papers(
    paper_a: int = Query(..., ge=1),
    paper_b: int = Query(..., ge=1),
    db: Session = Depends(get_db)
):
    crud.get_paper(db, paper_a)
    crud.get_paper(db, paper_b)
    return graph_analyzer.find_co_citing_papers(db, paper_a, paper_b)


@app.get("/api/v1/graph/references-cascade/{paper_id}", tags=["Graph Analysis"])
def get_references_cascade(
    paper_id: int,
    depth: int = Query(2, ge=1, le=5),
    db: Session = Depends(get_db)
):
    crud.get_paper(db, paper_id)
    return graph_analyzer.get_references_cascade(db, paper_id, depth)


@app.get("/api/v1/graph/citations-cascade/{paper_id}", tags=["Graph Analysis"])
def get_citations_cascade(
    paper_id: int,
    depth: int = Query(2, ge=1, le=5),
    db: Session = Depends(get_db)
):
    crud.get_paper(db, paper_id)
    return graph_analyzer.get_citations_cascade(db, paper_id, depth)


@app.get("/api/v1/graph/stats", response_model=schemas.GraphStatsResponse, tags=["Graph Analysis"])
def get_graph_statistics(db: Session = Depends(get_db)):
    return graph_analyzer.get_graph_statistics(db)


@app.get("/api/v1/graph/subgraph", tags=["Graph Analysis"])
def search_subgraph(
    keyword: str = Query(...),
    max_nodes: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    return graph_analyzer.search_subgraph(db, keyword, max_nodes)
