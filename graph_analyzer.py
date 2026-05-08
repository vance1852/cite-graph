from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Set
from collections import deque
from models import Paper, Citation
from schemas import PaperResponse
from crud import paper_to_response


def find_citation_path(
    db: Session,
    source_id: int,
    target_id: int,
    max_depth: int = 6
):
    if source_id == target_id:
        return None

    if max_depth < 1 or max_depth > 20:
        max_depth = 6

    visited = {source_id}
    queue = deque([(source_id, [source_id])])

    while queue:
        current, path = queue.popleft()

        if len(path) > max_depth:
            continue

        citations = db.query(Citation).filter(Citation.citing_id == current).all()

        for citation in citations:
            next_node = citation.cited_id

            if next_node == target_id:
                full_path = path + [next_node]
                papers = db.query(Paper).filter(Paper.id.in_(full_path)).all()
                paper_map = {p.id: p for p in papers}
                ordered_papers = [paper_map[pid] for pid in full_path if pid in paper_map]
                return {
                    "path": full_path,
                    "path_details": [paper_to_response(db, p) for p in ordered_papers]
                }

            if next_node not in visited:
                visited.add(next_node)
                queue.append((next_node, path + [next_node]))

    return None


def find_reverse_citation_path(
    db: Session,
    source_id: int,
    target_id: int,
    max_depth: int = 6
):
    if source_id == target_id:
        return None

    if max_depth < 1 or max_depth > 20:
        max_depth = 6

    visited = {source_id}
    queue = deque([(source_id, [source_id])])

    while queue:
        current, path = queue.popleft()

        if len(path) > max_depth:
            continue

        citations = db.query(Citation).filter(Citation.cited_id == current).all()

        for citation in citations:
            next_node = citation.citing_id

            if next_node == target_id:
                full_path = path + [next_node]
                papers = db.query(Paper).filter(Paper.id.in_(full_path)).all()
                paper_map = {p.id: p for p in papers}
                ordered_papers = [paper_map[pid] for pid in full_path if pid in paper_map]
                return {
                    "path": full_path,
                    "path_details": [paper_to_response(db, p) for p in ordered_papers]
                }

            if next_node not in visited:
                visited.add(next_node)
                queue.append((next_node, path + [next_node]))

    return None


def get_paper_influence(db: Session, paper_id: int):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        return None

    in_degree = db.query(Citation).filter(Citation.cited_id == paper_id).count()
    out_degree = db.query(Citation).filter(Citation.citing_id == paper_id).count()

    cited_by = db.query(Citation).filter(Citation.cited_id == paper_id).all()
    citing_ids = [c.citing_id for c in cited_by]

    second_level_citations = 0
    for citing_id in citing_ids:
        count = db.query(Citation).filter(Citation.cited_id == citing_id).count()
        second_level_citations += count

    h_index_approx = 0.0
    if in_degree > 0:
        citations_list = sorted([in_degree, second_level_citations], reverse=True)
        for i, count in enumerate(citations_list, 1):
            if count >= i:
                h_index_approx = i
            else:
                break

    return {
        "paper_id": paper_id,
        "title": paper.title,
        "in_degree": in_degree,
        "out_degree": out_degree,
        "h_index_approx": h_index_approx
    }


def get_influential_papers(db: Session, limit: int = 10):
    papers = db.query(Paper).all()
    influences = []

    for paper in papers:
        influence = get_paper_influence(db, paper.id)
        if influence and influence["in_degree"] > 0:
            influences.append(influence)

    influences.sort(key=lambda x: x["h_index_approx"], reverse=True)
    return influences[:limit]


def find_common_citations(db: Session, paper_a_id: int, paper_b_id: int):
    citations_a = db.query(Citation.cited_id).filter(
        Citation.citing_id == paper_a_id
    ).all()
    citations_b = db.query(Citation.cited_id).filter(
        Citation.citing_id == paper_b_id
    ).all()

    cited_a = {c[0] for c in citations_a}
    cited_b = {c[0] for c in citations_b}
    common_ids = cited_a & cited_b

    if not common_ids:
        return []

    papers = db.query(Paper).filter(Paper.id.in_(common_ids)).all()
    return [paper_to_response(db, p) for p in papers]


def find_co_citing_papers(db: Session, paper_a_id: int, paper_b_id: int):
    citations_a = db.query(Citation.citing_id).filter(
        Citation.cited_id == paper_a_id
    ).all()
    citations_b = db.query(Citation.citing_id).filter(
        Citation.cited_id == paper_b_id
    ).all()

    citing_a = {c[0] for c in citations_a}
    citing_b = {c[0] for c in citations_b}
    common_ids = citing_a & citing_b

    if not common_ids:
        return []

    papers = db.query(Paper).filter(Paper.id.in_(common_ids)).all()
    return [paper_to_response(db, p) for p in papers]


def get_references_cascade(db: Session, paper_id: int, depth: int = 2):
    if depth < 1 or depth > 5:
        depth = 2

    result = {"paper_id": paper_id, "levels": []}
    current_level = {paper_id}
    visited = {paper_id}

    for level in range(depth):
        next_level = set()

        for pid in current_level:
            citations = db.query(Citation).filter(Citation.citing_id == pid).all()
            for citation in citations:
                next_level.add(citation.cited_id)

        next_level = next_level - visited
        visited.update(next_level)

        if next_level:
            papers = db.query(Paper).filter(Paper.id.in_(next_level)).all()
            result["levels"].append({
                "depth": level + 1,
                "papers": [paper_to_response(db, p) for p in papers]
            })

        current_level = next_level
        if not current_level:
            break

    return result


def get_citations_cascade(db: Session, paper_id: int, depth: int = 2):
    if depth < 1 or depth > 5:
        depth = 2

    result = {"paper_id": paper_id, "levels": []}
    current_level = {paper_id}
    visited = {paper_id}

    for level in range(depth):
        next_level = set()

        for pid in current_level:
            citations = db.query(Citation).filter(Citation.cited_id == pid).all()
            for citation in citations:
                next_level.add(citation.citing_id)

        next_level = next_level - visited
        visited.update(next_level)

        if next_level:
            papers = db.query(Paper).filter(Paper.id.in_(next_level)).all()
            result["levels"].append({
                "depth": level + 1,
                "papers": [paper_to_response(db, p) for p in papers]
            })

        current_level = next_level
        if not current_level:
            break

    return result


def get_graph_statistics(db: Session):
    total_papers = db.query(Paper).count()
    total_citations = db.query(Citation).count()
    avg_citations = total_citations / total_papers if total_papers > 0 else 0.0

    in_degree_counts = db.query(
        Citation.cited_id,
        func.count(Citation.id)
    ).group_by(Citation.cited_id).all()

    out_degree_counts = db.query(
        Citation.citing_id,
        func.count(Citation.id)
    ).group_by(Citation.citing_id).all()

    max_cited = max(in_degree_counts, key=lambda x: x[1])[0] if in_degree_counts else None
    max_citing = max(out_degree_counts, key=lambda x: x[1])[0] if out_degree_counts else None

    max_cited_paper = None
    max_citing_paper = None

    if max_cited:
        paper = db.query(Paper).filter(Paper.id == max_cited).first()
        if paper:
            max_cited_paper = paper_to_response(db, paper)

    if max_citing:
        paper = db.query(Paper).filter(Paper.id == max_citing).first()
        if paper:
            max_citing_paper = paper_to_response(db, paper)

    return {
        "total_papers": total_papers,
        "total_citations": total_citations,
        "avg_citations_per_paper": round(avg_citations, 2),
        "max_cited_paper": max_cited_paper,
        "max_citing_paper": max_citing_paper
    }


def search_subgraph(db: Session, keyword: str, max_nodes: int = 50):
    matched_papers = db.query(Paper).filter(
        (Paper.title.contains(keyword)) |
        (Paper.abstract.contains(keyword) if Paper.abstract else False)
    ).limit(max_nodes).all()

    if not matched_papers:
        return {"nodes": [], "edges": []}

    paper_ids = {p.id for p in matched_papers}

    citations = db.query(Citation).filter(
        (Citation.citing_id.in_(paper_ids)) &
        (Citation.cited_id.in_(paper_ids))
    ).all()

    return {
        "nodes": [paper_to_response(db, p) for p in matched_papers],
        "edges": [
            {"id": c.id, "source": c.citing_id, "target": c.cited_id, "context": c.context}
            for c in citations
        ]
    }
