from fastapi import FastAPI
from database import init_db
from routers import router as papers_router, citations_router
from graph_api import router as graph_router

app = FastAPI(
    title="Citation Graph API",
    description="学术引用图谱 REST API — 管理论文与引用关系，提供基于图的分析接口",
    version="1.0.0",
)


@app.on_event("startup")
def startup():
    init_db()


app.include_router(papers_router)
app.include_router(citations_router)
app.include_router(graph_router)


@app.get("/", tags=["root"])
def root():
    return {
        "service": "Citation Graph API",
        "docs": "/docs",
        "endpoints": {
            "papers": "/papers",
            "citations": "/citations",
            "graph_stats": "/graph/stats",
            "centrality": "/graph/centrality",
            "shortest_path": "/graph/shortest-path",
            "neighbors": "/graph/neighbors/{paper_id}",
            "top_cited": "/graph/top-cited",
        },
    }
