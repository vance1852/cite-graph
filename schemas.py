from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class PaperCreate(BaseModel):
    title: str = Field(..., max_length=500)
    authors: str = Field(..., max_length=1000)
    year: int = Field(..., ge=1000, le=2100)
    venue: Optional[str] = Field(None, max_length=300)
    abstract: Optional[str] = None
    doi: Optional[str] = Field(None, max_length=200)


class PaperUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    authors: Optional[str] = Field(None, max_length=1000)
    year: Optional[int] = Field(None, ge=1000, le=2100)
    venue: Optional[str] = Field(None, max_length=300)
    abstract: Optional[str] = None
    doi: Optional[str] = Field(None, max_length=200)


class PaperRead(BaseModel):
    id: int
    title: str
    authors: str
    year: int
    venue: Optional[str]
    abstract: Optional[str]
    doi: Optional[str]

    model_config = {"from_attributes": True}


class CitationCreate(BaseModel):
    citing_paper_id: int
    cited_paper_id: int


class CitationRead(BaseModel):
    id: int
    citing_paper_id: int
    cited_paper_id: int

    model_config = {"from_attributes": True}


class ShortestPathResult(BaseModel):
    source_id: int
    target_id: int
    path: list[int]
    distance: int


class NodeCentrality(BaseModel):
    paper_id: int
    title: str
    degree_centrality: float
    in_degree_centrality: float
    out_degree_centrality: float
    betweenness_centrality: float
    closeness_centrality: float


class GraphStats(BaseModel):
    node_count: int
    edge_count: int
    density: float
    avg_clustering: float
    is_weakly_connected: bool
    strongly_connected_components: int
