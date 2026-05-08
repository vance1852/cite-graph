import networkx as nx
from fastapi import APIRouter, HTTPException, Query
from schemas import ShortestPathResult, NodeCentrality, GraphStats
import crud

router = APIRouter(prefix="/graph", tags=["graph analysis"])


def _build_graph() -> nx.DiGraph:
    g = nx.DiGraph()
    edges = crud.all_citations()
    for src, dst in edges:
        g.add_edge(src, dst)
    for pid in crud.all_paper_ids():
        if pid not in g:
            g.add_node(pid)
    return g


@router.get("/stats", response_model=GraphStats)
def graph_stats():
    g = _build_graph()
    if g.number_of_nodes() == 0:
        return GraphStats(
            node_count=0, edge_count=0, density=0.0,
            avg_clustering=0.0, is_weakly_connected=False,
            strongly_connected_components=0,
        )
    return GraphStats(
        node_count=g.number_of_nodes(),
        edge_count=g.number_of_edges(),
        density=round(nx.density(g), 6),
        avg_clustering=round(nx.average_clustering(g.to_undirected()), 6),
        is_weakly_connected=nx.is_weakly_connected(g),
        strongly_connected_components=nx.number_strongly_connected_components(g),
    )


@router.get("/shortest-path", response_model=ShortestPathResult)
def shortest_path(source: int = Query(...), target: int = Query(...)):
    g = _build_graph()
    if source not in g or target not in g:
        raise HTTPException(404, "Source or target paper not found in graph")
    try:
        path = nx.shortest_path(g, source=source, target=target)
    except nx.NetworkXNoPath:
        raise HTTPException(404, "No path exists between source and target")
    return ShortestPathResult(
        source_id=source, target_id=target, path=path, distance=len(path) - 1
    )


@router.get("/centrality", response_model=list[NodeCentrality])
def centrality(top_k: int = Query(20, ge=1, le=200)):
    g = _build_graph()
    if g.number_of_nodes() == 0:
        return []
    deg = nx.degree_centrality(g)
    in_deg = nx.in_degree_centrality(g)
    out_deg = nx.out_degree_centrality(g)
    bet = nx.betweenness_centrality(g, normalized=True)
    clo = nx.closeness_centrality(g)
    results = []
    for node in g.nodes():
        p = crud.paper_get(int(node))
        title = p.title if p else f"Paper#{node}"
        results.append(NodeCentrality(
            paper_id=int(node), title=title,
            degree_centrality=round(deg.get(node, 0), 6),
            in_degree_centrality=round(in_deg.get(node, 0), 6),
            out_degree_centrality=round(out_deg.get(node, 0), 6),
            betweenness_centrality=round(bet.get(node, 0), 6),
            closeness_centrality=round(clo.get(node, 0), 6),
        ))
    results.sort(key=lambda x: x.degree_centrality, reverse=True)
    return results[:top_k]


@router.get("/neighbors/{paper_id}")
def paper_neighbors(paper_id: int, depth: int = Query(1, ge=1, le=5)):
    if crud.paper_get(paper_id) is None:
        raise HTTPException(404, "Paper not found")
    g = _build_graph()
    if paper_id not in g:
        return {"paper_id": paper_id, "depth": depth, "nodes": [], "edges": []}
    visited_edges = set()
    visited_nodes = {paper_id}
    frontier = {paper_id}
    for _ in range(depth):
        next_frontier = set()
        for node in frontier:
            for succ in g.successors(node):
                edge = (node, succ)
                if edge not in visited_edges:
                    visited_edges.add(edge)
                    visited_nodes.add(succ)
                    next_frontier.add(succ)
            for pred in g.predecessors(node):
                edge = (pred, node)
                if edge not in visited_edges:
                    visited_edges.add(edge)
                    visited_nodes.add(pred)
                    next_frontier.add(pred)
        frontier = next_frontier
    return {
        "paper_id": paper_id,
        "depth": depth,
        "nodes": list(visited_nodes),
        "edges": [list(e) for e in visited_edges],
    }


@router.get("/top-cited", response_model=list[dict])
def top_cited(top_k: int = Query(10, ge=1, le=100)):
    g = _build_graph()
    if g.number_of_nodes() == 0:
        return []
    in_degrees = dict(g.in_degree())
    sorted_nodes = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)[:top_k]
    results = []
    for node, count in sorted_nodes:
        p = crud.paper_get(int(node))
        results.append({
            "paper_id": int(node),
            "title": p.title if p else f"Paper#{node}",
            "cited_count": count,
        })
    return results
