from database import get_db
from schemas import PaperCreate, PaperUpdate, PaperRead, CitationCreate, CitationRead


def paper_create(data: PaperCreate) -> PaperRead:
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO papers (title, authors, year, venue, abstract, doi) VALUES (?, ?, ?, ?, ?, ?)",
            (data.title, data.authors, data.year, data.venue, data.abstract, data.doi),
        )
        row = conn.execute("SELECT * FROM papers WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return PaperRead(**dict(row))


def paper_get(paper_id: int) -> PaperRead | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM papers WHERE id = ?", (paper_id,)).fetchone()
        if row is None:
            return None
        return PaperRead(**dict(row))


def paper_list(skip: int = 0, limit: int = 50, year: int | None = None, search: str | None = None) -> list[PaperRead]:
    with get_db() as conn:
        clauses: list[str] = []
        params: list = []
        if year is not None:
            clauses.append("year = ?")
            params.append(year)
        if search:
            clauses.append("(title LIKE ? OR authors LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        rows = conn.execute(
            f"SELECT * FROM papers{where} ORDER BY year DESC, id LIMIT ? OFFSET ?",
            params + [limit, skip],
        ).fetchall()
        return [PaperRead(**dict(r)) for r in rows]


def paper_update(paper_id: int, data: PaperUpdate) -> PaperRead | None:
    fields = {k: v for k, v in data.model_dump().items() if v is not None}
    if not fields:
        return paper_get(paper_id)
    sets = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [paper_id]
    with get_db() as conn:
        cursor = conn.execute(f"UPDATE papers SET {sets} WHERE id = ?", values)
        if cursor.rowcount == 0:
            return None
        row = conn.execute("SELECT * FROM papers WHERE id = ?", (paper_id,)).fetchone()
        return PaperRead(**dict(row))


def paper_delete(paper_id: int) -> bool:
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM papers WHERE id = ?", (paper_id,))
        return cursor.rowcount > 0


def citation_create(data: CitationCreate) -> CitationRead | str:
    if data.citing_paper_id == data.cited_paper_id:
        return "SELF_CITE"
    with get_db() as conn:
        p1 = conn.execute("SELECT 1 FROM papers WHERE id = ?", (data.citing_paper_id,)).fetchone()
        p2 = conn.execute("SELECT 1 FROM papers WHERE id = ?", (data.cited_paper_id,)).fetchone()
        if not p1 or not p2:
            return "NOT_FOUND"
        try:
            cursor = conn.execute(
                "INSERT INTO citations (citing_paper_id, cited_paper_id) VALUES (?, ?)",
                (data.citing_paper_id, data.cited_paper_id),
            )
        except Exception:
            return "DUPLICATE"
        row = conn.execute("SELECT * FROM citations WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return CitationRead(**dict(row))


def citation_delete(citing_id: int, cited_id: int) -> bool:
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM citations WHERE citing_paper_id = ? AND cited_paper_id = ?",
            (citing_id, cited_id),
        )
        return cursor.rowcount > 0


def citation_list_by_paper(paper_id: int) -> dict:
    with get_db() as conn:
        citing = conn.execute(
            "SELECT cited_paper_id FROM citations WHERE citing_paper_id = ?", (paper_id,)
        ).fetchall()
        cited_by = conn.execute(
            "SELECT citing_paper_id FROM citations WHERE cited_paper_id = ?", (paper_id,)
        ).fetchall()
        return {
            "paper_id": paper_id,
            "citing": [r["cited_paper_id"] for r in citing],
            "cited_by": [r["citing_paper_id"] for r in cited_by],
        }


def all_citations() -> list[tuple[int, int]]:
    with get_db() as conn:
        rows = conn.execute("SELECT citing_paper_id, cited_paper_id FROM citations").fetchall()
        return [(r["citing_paper_id"], r["cited_paper_id"]) for r in rows]


def all_paper_ids() -> set[int]:
    with get_db() as conn:
        rows = conn.execute("SELECT id FROM papers").fetchall()
        return {r["id"] for r in rows}
