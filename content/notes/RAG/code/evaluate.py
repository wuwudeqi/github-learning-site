"""Retrieval evaluation only. The questions file is opened here, never by the indexer."""
import argparse
import hashlib
import json
from pathlib import Path
from time import perf_counter
import platform
import numpy as np
from ingest import load_corpus
from chunking import make_chunks
from retrieval import BGEEncoder, HybridRetriever, CrossEncoderReranker
from graph import prepare_question, resolve_filters


CONFIG = {"chunk_tokens": 384, "overlap_tokens": 48, "candidate_pool": 20,
          "rerank_pool": 12, "k": 5, "rrf_constant": 60,
          "embedding": "BAAI/bge-small-zh-v1.5", "reranker": "BAAI/bge-reranker-base"}
CONFIG["embedding_revision"] = BGEEncoder.revision
CONFIG["reranker_revision"] = CrossEncoderReranker.revision


def retrieval_metrics(gold_evidence: list[dict], ranked_hits, k: int = 5) -> dict:
    gold = {(e["doc_id"], e["section_id"]) for e in gold_evidence}
    if not gold:
        raise ValueError("no-answer/clarification questions do not have ordinary retrieval recall")
    ranked = [(h.chunk.doc_id, h.chunk.section_id) for h in ranked_hits[:k]]
    found = set(ranked)
    gold_docs, found_docs = {g[0] for g in gold}, {g[0] for g in found}
    first = next((rank for rank, key in enumerate(ranked, 1) if key in gold), None)
    return {"section_recall": len(gold & found) / len(gold),
            "doc_recall": len(gold_docs & found_docs) / len(gold_docs),
            "mrr": 1 / first if first else 0.0,
            "all_evidence": float(gold <= found)}


def run_eval(root: Path, split: str, output: Path, rerank: bool = False):
    questions = [json.loads(line) for line in (root / "data/questions.jsonl").read_text().splitlines() if line]
    split_questions = [q for q in questions if q["split"] == split]
    excluded = {action: sum(q["expected_action"] == action for q in split_questions)
                for action in ("clarify", "abstain")}
    questions = [q for q in split_questions if q["expected_action"] == "answer"]
    encoder = BGEEncoder()
    chunks = make_chunks(load_corpus(root), encoder.tokenizer, CONFIG["chunk_tokens"], CONFIG["overlap_tokens"])
    indexed_text = json.dumps([{ "id": c.chunk_id, "text": c.text, "metadata": c.metadata}
                              for c in sorted(chunks, key=lambda c: c.chunk_id)],
                             ensure_ascii=False, sort_keys=True).encode()
    started = perf_counter()
    retriever = HybridRetriever(chunks, encoder)
    build_seconds = perf_counter() - started
    reranker = CrossEncoderReranker() if rerank else None
    modes = ["dense", "bm25", "hybrid"] + (["hybrid_rerank"] if rerank else [])
    rows = []
    for position, q in enumerate(questions, 1):
        query = prepare_question(q["question"], q.get("history", []))
        # A new explicit version in the current turn supersedes a prior version.
        filters = resolve_filters(q["question"], q.get("history", []))
        for mode in modes:
            started = perf_counter()
            hits = retriever.search(query, mode="hybrid" if mode == "hybrid_rerank" else mode,
                                    limit=CONFIG["rerank_pool"] if mode == "hybrid_rerank" else CONFIG["k"],
                                    filters=filters, candidates=CONFIG["candidate_pool"])
            if mode == "hybrid_rerank":
                hits = reranker.rerank(query, hits, CONFIG["k"])
            elapsed_ms = (perf_counter() - started) * 1000
            rows.append({"qid": q["qid"], "mode": mode, "category": q["category"],
                         "query": query, "filters": filters,
                         "retrieved": [h.chunk.chunk_id for h in hits],
                         "elapsed_ms": round(elapsed_ms, 2),
                         **retrieval_metrics(q["gold_evidence"], hits, CONFIG["k"])})
        if position % 10 == 0:
            print(f"EVALUATED {split} {position}/{len(questions)}", flush=True)
    summary = {}
    for mode in modes:
        group = [row for row in rows if row["mode"] == mode]
        summary[mode] = {key: round(float(np.mean([r[key] for r in group])), 6)
                         for key in ("section_recall", "doc_recall", "mrr", "all_evidence")}
        summary[mode]["latency_p50_ms"] = round(float(np.median([r["elapsed_ms"] for r in group])), 2)
        summary[mode]["latency_p95_ms"] = round(float(np.percentile([r["elapsed_ms"] for r in group], 95)), 2)
    record = {"kind": "real_retrieval_on_synthetic_corpus", "split": split, "answerable_questions": len(questions),
              "excluded_questions": excluded,
              "k": CONFIG["k"], "chunks": len(chunks), "config": CONFIG,
              "python": platform.python_version(), "platform": platform.platform(),
              "corpus_sha256": hashlib.sha256((root / "data/corpus.jsonl").read_bytes()).hexdigest(),
              "indexed_chunks_sha256": hashlib.sha256(indexed_text).hexdigest(),
              "source_code_sha256": hashlib.sha256(b"\n".join(
                  path.name.encode() + b"\n" + path.read_bytes()
                  for path in sorted(Path(__file__).parent.glob("*.py")))).hexdigest(),
              "questions_sha256": hashlib.sha256((root / "data/questions.jsonl").read_bytes()).hexdigest(),
              "index_build_seconds": round(build_seconds, 2), "summary": summary,
              "generation_evaluated": False, "judge_evaluated": False,
              "latency_note": "Sequential local CPU retrieval; warm/cache effects exist. Not production P95 or concurrent load.",
              "rows": rows}
    output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    retriever.close()
    print(json.dumps({"split": split, "questions": len(questions), "chunks": len(chunks), "summary": summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["dev", "test"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rerank", action="store_true")
    args = parser.parse_args()
    run_eval(Path(__file__).resolve().parent.parent, args.split, args.output, args.rerank)
