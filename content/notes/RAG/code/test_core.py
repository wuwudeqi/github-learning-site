"""Deterministic mechanism checks. Fixture vectors are ONLY used here, never in reported retrieval metrics."""
from pathlib import Path
import json
import numpy as np
import pytest
from ingest import Section, parse_html, load_corpus
from chunking import Chunk, make_chunks
from retrieval import Hit, HybridRetriever, rrf, lexical_tokens
from graph import build_graph, fixture_answerer, explicit_filters, resolve_filters, validate_citations, build_context
from evaluate import retrieval_metrics


class CharTokenizer:
    def encode(self, text, add_special_tokens=True):
        tokens = [ord(c) for c in text]
        return [1] + tokens + [2] if add_special_tokens else tokens
    def decode(self, tokens, **kwargs):
        return "".join(chr(c) for c in tokens)


class FixtureEncoder:
    tokenizer = CharTokenizer()
    def documents(self, texts):
        return np.array([[1.0, 0.0] if "current" in t else [0.0, 1.0] for t in texts])
    def query(self, text):
        return np.array([1.0, 0.0])


def chunk(key="A:s1:p0", text="current guide", **metadata):
    doc, section, _ = key.split(":")
    return Chunk(key, doc, section, text, text, {"status": "active", "version": "2.0", **metadata})


def test_html_excludes_navigation_and_keeps_table(tmp_path):
    path = tmp_path / "wiki.html"
    path.write_text('<nav>noise</nav><main><h2 id="s1">申请</h2><ol><li>填写项目</li><li>提交审批</li></ol><table><tr><td>只读</td><td>7天</td></tr></table><h2 id="s2">完成</h2><p>重新登录</p></main>')
    sections = parse_html(path, {"doc_id": "A", "title": "权限"})
    assert len(sections) == 2 and "noise" not in sections[0].text
    assert "填写项目" in sections[0].text and "7天" in sections[0].text
    assert "重新登录" not in sections[0].text


def test_html_preserves_anchor_destination_and_table_rows(tmp_path):
    path = tmp_path / "links.html"
    path.write_text('<main><h2 id="s1">申请</h2><p><a href="https://example.invalid/apply">申请入口</a></p>'
                    '<table><tr><th>权限</th><th>期限</th></tr><tr><td>只读</td><td>7天</td></tr></table>'
                    '<footer>page noise</footer></main>')
    text = parse_html(path, {"doc_id": "A", "title": "权限"})[0].text
    assert "https://example.invalid/apply" in text
    assert "权限 | 期限\n只读 | 7天" in text
    assert "page noise" not in text


def test_chunking_preserves_short_section_and_overlaps_long_one():
    tokenizer = CharTokenizer()
    sections = [Section("A", "s1", "T", "H", "abcdefghij" * 10)]
    chunks = make_chunks(sections, tokenizer, max_tokens=30, overlap_tokens=4)
    assert len(chunks) > 1
    assert chunks[0].body[-4:] == chunks[1].body[:4]
    assert all(len(tokenizer.encode(c.text)) <= 30 for c in chunks)
    assert len({c.chunk_id for c in chunks}) == len(chunks)


def test_rrf_uses_rank_and_deduplicates_within_a_list():
    a, b = Hit(chunk(), 99999, "dense"), Hit(chunk("B:s1:p0"), 0.01, "bm25")
    result = rrf([[a, b], [b, b, a]], limit=2)
    # Duplicate entry in one list must not add another vote.
    assert result[0].chunk.chunk_id == b.chunk.chunk_id
    assert result[0].score == pytest.approx(1 / 62 + 1 / 61)
    assert len(result) == 2


def test_real_qdrant_applies_same_filter_as_bm25():
    a = chunk(text="current guide")
    old = chunk("B:s1:p0", text="old guide", status="deprecated", version="1.0")
    retriever = HybridRetriever([a, old], FixtureEncoder())
    try:
        assert [h.chunk.doc_id for h in retriever.search("guide", "dense", filters={"version": ["1.0"]})] == ["B"]
        assert all(h.chunk.metadata["version"] == "1.0" for h in retriever.search("guide", filters={"version": ["1.0"]}))
    finally:
        retriever.close()


def test_identifiers_and_historical_versions_are_preserved():
    assert "cicd_403" in lexical_tokens("流水线报 CICD_403 怎么办")
    assert explicit_filters("1.0 版本怎样申请") == {"version": ["1.0"]}
    assert explicit_filters("旧版平台如何申请") == {}
    assert explicit_filters("现在如何申请") == {"status": ["active"]}


def test_current_turn_version_intent_overrides_history():
    old_history = [{"role": "user", "content": "1.0 怎么申请权限"}]
    assert resolve_filters("现在怎样申请？", old_history) == {"status": ["active"]}
    assert resolve_filters("外包人员呢？", old_history) == {"version": ["1.0"]}
    assert resolve_filters("2.0 怎样申请？", old_history) == {"version": ["2.0"]}
    assert resolve_filters("旧版怎样申请？", [{"role": "user", "content": "2.0 的申请步骤"}]) == {}


class SequencedRetriever:
    encoder = FixtureEncoder()
    def __init__(self):
        self.calls = 0
    def search(self, query, **kwargs):
        self.calls += 1
        return [Hit(chunk(f"D{self.calls}:s1:p0"), 1, "fixture")]


def test_graph_replaces_candidates_and_caps_retry():
    retriever = SequencedRetriever()
    judge = lambda *args: {"action": "insufficient", "reason": "missing procedure", "missing": ["步骤"]}
    graph = build_graph(retriever, judge, fixture_answerer)
    state = graph.invoke({"original_question": "怎样申请", "trace": []})
    assert retriever.calls == 2 and state["retry_count"] == 1
    assert state["action"] == "abstain" and state["citations"] == []
    assert [h.chunk.doc_id for h in state["candidates"]] == ["D2"]
    assert len([e for e in state["trace"] if e["node"] == "retrieve"]) == 2


def test_graph_clarifies_without_retrieval_loop():
    retriever = SequencedRetriever()
    judge = lambda *args: {"action": "clarify", "reason": "missing object", "missing": ["仓库名称"]}
    state = build_graph(retriever, judge, fixture_answerer).invoke({"original_question": "失败了", "trace": []})
    assert retriever.calls == 1 and state["action"] == "clarify"
    assert "仓库名称" in state["answer"] and state["original_question"] == "失败了"


def test_graph_generates_with_valid_source_ids():
    state = build_graph(SequencedRetriever(), lambda *args: {"action": "answer", "reason": "fixture"}, fixture_answerer).invoke(
        {"original_question": "如何创建仓库", "trace": []})
    assert state["citations"] == ["D1:s1:p0"] and "抽取替身" in state["answer"]


def test_citation_identity_does_not_allow_external_ids():
    hits = [Hit(chunk(), 1, "fixture")]
    with pytest.raises(ValueError):
        validate_citations(["fake:source:p0"], hits)
    with pytest.raises(ValueError):
        validate_citations([], hits)
    with pytest.raises(ValueError):
        validate_citations(["A:s1:p0"], hits, "这条答案没有正文引用")
    with pytest.raises(ValueError):
        validate_citations(["A:s1:p0"], hits, "答案 [B:s1:p0]")


def test_context_dedup_and_token_budget():
    hit = Hit(chunk(text="x" * 20), 1, "fixture")
    assert build_context([hit, hit], CharTokenizer(), budget=60) == [hit]
    assert build_context([hit], CharTokenizer(), budget=5) == []


def test_partial_evidence_is_not_full_coverage():
    gold = [{"doc_id": "A", "section_id": "s1"}, {"doc_id": "B", "section_id": "s1"}]
    scores = retrieval_metrics(gold, [Hit(chunk(), 1, "fixture")])
    assert scores == {"section_recall": 0.5, "doc_recall": 0.5, "mrr": 1.0, "all_evidence": 0.0}
    with pytest.raises(ValueError):
        retrieval_metrics([], [])


def test_corpus_and_evaluation_contract():
    root = Path(__file__).resolve().parent.parent
    sections = load_corpus(root)
    evidence = {(s.doc_id, s.section_id) for s in sections}
    questions = [json.loads(line) for line in (root / "data/questions.jsonl").read_text().splitlines()]
    assert len({q["qid"] for q in questions}) == len(questions)
    families = {}
    for q in questions:
        families.setdefault(q["family"], set()).add(q["split"])
        assert {(e["doc_id"], e["section_id"]) for e in q["gold_evidence"]} <= evidence
        if q["expected_action"] == "answer":
            assert q["gold_evidence"] and q["required_points"]
        else:
            assert not q["gold_evidence"]
    assert all(len(splits) == 1 for splits in families.values()), "one family leaked across dev/test"
