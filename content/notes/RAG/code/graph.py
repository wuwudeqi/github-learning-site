"""LangGraph orchestration. Judge/answerer are injected so control flow can be tested independently."""
from typing import TypedDict, Annotated, Callable
import operator
import re
from time import perf_counter
from langgraph.graph import StateGraph, START, END
from retrieval import Hit


class RAGState(TypedDict, total=False):
    original_question: str
    history: list[dict]
    query: str
    filters: dict
    candidates: list[Hit]                  # no reducer: a new round replaces old candidates
    context: list[Hit]
    previous_ids: list[str]
    retry_count: int
    action: str
    reason: str
    missing: list[str]
    answer: str
    citations: list[str]
    trace: Annotated[list[dict], operator.add]  # only the trace is appended


def prepare_question(question: str, history: list[dict] | None = None) -> str:
    """Small follow-up baseline: include the latest user question, never a previous generated answer."""
    prior = [m["content"] for m in (history or []) if m.get("role") == "user"]
    if prior:
        return f"上文问题：{prior[-1]}\n本轮问题（条件冲突时以本轮为准）：{question}"
    return question


def explicit_filters(question: str) -> dict:
    versions = sorted(set(re.findall(r"(?<![\d.])([12]\.0)(?![\d.])", question)))
    # Unknown/unmentioned version defaults to current documents. Explicit comparisons retain both.
    if versions:
        return {"version": versions}
    if any(word in question for word in ("旧版", "历史版本", "以前版本", "升级前")):
        return {}
    return {"status": ["active"]}


def resolve_filters(question: str, history: list[dict] | None = None) -> dict:
    """Current version intent overrides history; otherwise inherit the latest user's scope."""
    explicit = explicit_filters(question)
    version_words = ("现在", "当前", "新版", "最新", "升级后", "旧版", "历史版本", "以前版本", "升级前")
    if "version" in explicit or any(word in question for word in version_words):
        return explicit
    prior = [m["content"] for m in (history or []) if m.get("role") == "user"]
    return explicit_filters(prior[-1]) if prior else explicit


def build_context(hits: list[Hit], tokenizer, budget: int = 1800) -> list[Hit]:
    selected, seen, used = [], set(), 0
    for hit in hits:
        identity = hit.chunk.chunk_id
        if identity in seen:
            continue
        seen.add(identity)
        # Citation labels and separators also occupy input tokens.
        size = len(tokenizer.encode(f"[{identity}]\n{hit.chunk.text}\n", add_special_tokens=False))
        if used + size <= budget:
            selected.append(hit)
            used += size
    return selected


def validate_citations(citations: list[str], context: list[Hit], text: str | None = None) -> None:
    allowed = {hit.chunk.chunk_id for hit in context}
    if not citations or not set(citations).issubset(allowed):
        raise ValueError("answer has missing or out-of-context citation IDs")
    if text is not None:
        markers = set(re.findall(r"\[([A-Za-z0-9_-]+:[A-Za-z0-9_-]+:p\d+)\]", text))
        if markers != set(citations):
            raise ValueError("inline citations and citation array disagree")
    # This verifies identity, not whether each claim follows from the cited text.


def build_graph(retriever, judge: Callable, answerer: Callable,
                rewriter: Callable | None = None, reranker=None,
                candidate_limit: int = 12, context_budget: int = 1800):
    def prepare(state):
        query = prepare_question(state["original_question"], state.get("history", []))
        filters = resolve_filters(state["original_question"], state.get("history", []))
        return {"query": query, "filters": filters, "retry_count": 0,
                "candidates": [], "context": [], "previous_ids": [], "citations": [],
                "trace": [{"node": "prepare", "query": query}]}

    def retrieve(state):
        started = perf_counter()
        hits = retriever.search(state["query"], limit=candidate_limit, filters=state["filters"])
        return {"candidates": hits, "trace": [{"node": "retrieve", "round": state["retry_count"],
                 "ids": [h.chunk.chunk_id for h in hits], "elapsed_ms": round((perf_counter()-started)*1000, 2)}]}

    def rerank(state):
        hits = state["candidates"]
        ranked = reranker.rerank(state["query"], hits, limit=8) if reranker else hits[:8]
        context = build_context(ranked, retriever.encoder.tokenizer, context_budget)
        return {"context": context, "trace": [{"node": "context", "reranker": bool(reranker),
                                                "ids": [h.chunk.chunk_id for h in context]}]}

    def assess(state):
        result = judge(state["original_question"], state["context"], state.get("history", []))
        action = result.get("action")
        if action not in {"answer", "clarify", "insufficient"}:
            raise ValueError("judge returned an unsupported action")
        if action == "answer" and not state["context"]:
            action = "insufficient"
        same_ids = set(state["previous_ids"]) == {h.chunk.chunk_id for h in state["candidates"]}
        if action == "insufficient":
            action = "rewrite" if state["retry_count"] < 1 else "abstain"
        reason = str(result.get("reason", ""))
        if state["retry_count"] and same_ids and action == "abstain":
            reason += "；补检索没有带来新的候选证据"
        return {"action": action, "reason": reason, "missing": result.get("missing", []),
                "trace": [{"node": "assess", "action": action, "reason": reason}]}

    def rewrite(state):
        candidate = rewriter(state["query"], state["missing"]) if rewriter else state["query"] + " 操作步骤 适用条件"
        # Demonstrate a constraint for exact identifiers and explicit versions. This is not full semantic equivalence.
        protected = re.findall(r"[A-Z][A-Z0-9]*_[A-Z0-9_]+|\b[12]\.0\b", state["query"])
        if any(token not in candidate for token in protected):
            candidate = state["query"]
        return {"query": candidate, "retry_count": state["retry_count"] + 1,
                "previous_ids": [h.chunk.chunk_id for h in state["candidates"]],
                "trace": [{"node": "rewrite", "query": candidate}]}

    def generate(state):
        result = answerer(state["original_question"], state["context"], state.get("history", []))
        validate_citations(result["citations"], state["context"], result["text"])
        return {"answer": result["text"], "citations": result["citations"],
                "trace": [{"node": "generate", "citation_ids_valid": True}]}

    def clarify(state):
        missing = "、".join(state["missing"]) or "系统名称、操作步骤或报错信息"
        return {"answer": f"请补充：{missing}。已有问题会保留为下一轮上下文。", "citations": []}

    def abstain(state):
        return {"answer": "当前检索资料不足以给出有依据的处理步骤。" + state["reason"], "citations": []}

    graph = StateGraph(RAGState)
    for name, node in [("prepare", prepare), ("retrieve", retrieve), ("rerank", rerank),
                       ("assess", assess), ("rewrite", rewrite), ("generate", generate),
                       ("clarify", clarify), ("abstain", abstain)]:
        graph.add_node(name, node)
    graph.add_edge(START, "prepare")
    graph.add_edge("prepare", "retrieve")
    graph.add_edge("retrieve", "rerank")
    graph.add_edge("rerank", "assess")
    graph.add_conditional_edges("assess", lambda s: s["action"],
                                {"answer": "generate", "clarify": "clarify", "rewrite": "rewrite", "abstain": "abstain"})
    graph.add_edge("rewrite", "retrieve")
    for terminal in ["generate", "clarify", "abstain"]:
        graph.add_edge(terminal, END)
    return graph.compile()


def fixture_judge(question, context, history):
    """Control-flow substitute. NOT a learned relevance or answerability judge."""
    if question.strip() in {"流水线失败了", "权限怎么申请"}:
        return {"action": "clarify", "reason": "fixture rule: missing object", "missing": ["具体操作对象及报错"]}
    return {"action": "answer" if context else "insufficient", "reason": "fixture: nonempty context only", "missing": []}


def fixture_answerer(question, context, history):
    """Quotes two fragments to exercise source wiring. It does not synthesize an answer."""
    hits = context[:2]
    return {"text": "[抽取替身，非模型答案]\n" + "\n\n".join(f"[{h.chunk.chunk_id}] {h.chunk.body}" for h in hits),
            "citations": [h.chunk.chunk_id for h in hits]}
