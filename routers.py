from fastapi import APIRouter, HTTPException, Query
from schemas import PaperCreate, PaperUpdate, PaperRead, CitationCreate, CitationRead
import crud

router = APIRouter(prefix="/papers", tags=["papers"])


@router.post("", response_model=PaperRead, status_code=201)
def create_paper(data: PaperCreate):
    return crud.paper_create(data)


@router.get("", response_model=list[PaperRead])
def list_papers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    year: int | None = None,
    search: str | None = None,
):
    return crud.paper_list(skip=skip, limit=limit, year=year, search=search)


@router.get("/{paper_id}", response_model=PaperRead)
def get_paper(paper_id: int):
    p = crud.paper_get(paper_id)
    if p is None:
        raise HTTPException(404, "Paper not found")
    return p


@router.put("/{paper_id}", response_model=PaperRead)
def update_paper(paper_id: int, data: PaperUpdate):
    p = crud.paper_update(paper_id, data)
    if p is None:
        raise HTTPException(404, "Paper not found")
    return p


@router.delete("/{paper_id}", status_code=204)
def delete_paper(paper_id: int):
    if not crud.paper_delete(paper_id):
        raise HTTPException(404, "Paper not found")


@router.get("/{paper_id}/citations")
def get_paper_citations(paper_id: int):
    if crud.paper_get(paper_id) is None:
        raise HTTPException(404, "Paper not found")
    return crud.citation_list_by_paper(paper_id)


citations_router = APIRouter(prefix="/citations", tags=["citations"])


@citations_router.post("", response_model=CitationRead, status_code=201)
def create_citation(data: CitationCreate):
    result = crud.citation_create(data)
    if isinstance(result, str):
        if result == "SELF_CITE":
            raise HTTPException(400, "Cannot cite self")
        if result == "NOT_FOUND":
            raise HTTPException(404, "One or both papers not found")
        if result == "DUPLICATE":
            raise HTTPException(409, "Citation already exists")
    return result


@citations_router.delete("", status_code=204)
def delete_citation(citing_paper_id: int = Query(...), cited_paper_id: int = Query(...)):
    if not crud.citation_delete(citing_paper_id, cited_paper_id):
        raise HTTPException(404, "Citation not found")
