"""Document chunking and lexical retrieval with citations."""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any, Iterable

TOKEN = re.compile(r"[a-z0-9]+")
STOP = {
    "the", "a", "an", "and", "or", "of", "to", "in", "for", "on", "with", "is", "are",
    "this", "that", "was", "be", "as", "at", "by", "from", "it", "patient", "member",
}


def chunk_text(text: str, size: int = 1800, overlap: int = 300) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    parts = re.split(r"\n{2,}", text)
    chunks: list[str] = []
    buf = ""
    for part in parts:
        if len(buf) + len(part) + 2 <= size:
            buf = f"{buf}\n\n{part}".strip()
            continue
        if buf:
            chunks.append(buf)
            tail = buf[-overlap:] if overlap and len(buf) > overlap else ""
            buf = f"{tail}\n\n{part}".strip()
        else:
            start = 0
            while start < len(part):
                chunks.append(part[start : start + size])
                start += max(1, size - overlap)
            buf = ""
    if buf:
        chunks.append(buf)
    return chunks


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN.findall((text or "").lower()) if t not in STOP and len(t) > 1]


def _idf(df: int, n: int) -> float:
    return math.log((n + 1) / (df + 1)) + 1.0


def search_chunks(
    query: str,
    chunks: list[dict[str, Any]],
    *,
    member_id: str | None = None,
    document_classes: Iterable[str] | None = None,
    limit: int = 6,
) -> list[dict[str, Any]]:
    q_tokens = tokenize(query)
    if not q_tokens:
        return []
    pool = chunks
    if member_id:
        mid = member_id.upper()
        pooled = [c for c in pool if (c.get("member_id") or "").upper() == mid]
        # For mixed clinical+regulatory questions keep global docs too
        global_docs = [c for c in pool if not c.get("member_id")]
        pool = pooled + global_docs
    if document_classes:
        allowed = {d.lower() for d in document_classes}
        pool = [c for c in pool if (c.get("document_class") or "").lower() in allowed]
    n = max(1, len(pool))
    df: Counter[str] = Counter()
    tok_docs: list[list[str]] = []
    for c in pool:
        toks = tokenize(c.get("text", ""))
        tok_docs.append(toks)
        df.update(set(toks))
    q_counts = Counter(q_tokens)
    scored: list[tuple[float, dict[str, Any]]] = []
    for c, toks in zip(pool, tok_docs):
        tf = Counter(toks)
        score = 0.0
        for term, qf in q_counts.items():
            if tf[term]:
                score += qf * (1 + math.log(tf[term])) * _idf(df[term], n)
        if (c.get("member_id") or "") and member_id and c.get("member_id") == member_id:
            score *= 1.15
        if score > 0:
            scored.append((score, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    out = []
    for score, c in scored[:limit]:
        item = dict(c)
        item["retrieval_score"] = round(score, 4)
        out.append(item)
    return out
