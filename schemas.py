from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class PaperBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    authors: Optional[str] = None
    abstract: Optional[str] = None
    venue: Optional[str] = Field(None, max_length=200)
    year: Optional[int] = Field(None, ge=1000, le=9999)
    doi: Optional[str] = Field(None, max_length=100)
    pdf_url: Optional[str] = Field(None, max_length=500)


class PaperCreate(PaperBase):
    pass


class PaperUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    authors: Optional[str] = None
    abstract: Optional[str] = None
    venue: Optional[str] = Field(None, max_length=200)
    year: Optional[int] = Field(None, ge=1000, le=9999)
    doi: Optional[str] = Field(None, max_length=100)
    pdf_url: Optional[str] = Field(None, max_length=500)


class PaperResponse(PaperBase):
    id: int
    created_at: datetime
    updated_at: datetime
    citations_count: int = 0
    cited_by_count: int = 0

    class Config:
        from_attributes = True


class PaperDetailResponse(PaperResponse):
    citations: List["CitationResponse"] = []
    cited_by: List["CitationResponse"] = []


class CitationBase(BaseModel):
    citing_id: int = Field(..., ge=1)
    cited_id: int = Field(..., ge=1)
    context: Optional[str] = None


class CitationCreate(CitationBase):
    pass


class CitationResponse(BaseModel):
    id: int
    citing_id: int
    cited_id: int
    context: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CitationDetailResponse(CitationResponse):
    citing_paper: Optional[PaperResponse] = None
    cited_paper: Optional[PaperResponse] = None


PaperDetailResponse.model_rebuild()


class CitationPathResponse(BaseModel):
    path: List[int]
    path_details: List[PaperResponse]


class InfluenceResponse(BaseModel):
    paper_id: int
    title: str
    in_degree: int
    out_degree: int
    h_index_approx: float


class CoCitationResponse(BaseModel):
    paper_id: int
    title: str
    co_citation_count: int


class BatchCitationCreate(BaseModel):
    citations: List[CitationCreate]


class BatchCitationResponse(BaseModel):
    created: int
    failed: int
    errors: List[str]


class GraphStatsResponse(BaseModel):
    total_papers: int
    total_citations: int
    avg_citations_per_paper: float
    max_cited_paper: Optional[PaperResponse]
    max_citing_paper: Optional[PaperResponse]
