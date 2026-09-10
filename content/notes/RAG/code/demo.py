import argparse
import json
from pathlib import Path
from ingest import load_corpus
from chunking import make_chunks
from retrieval import BGEEncoder, HybridRetriever, CrossEncoderReranker
from graph import build_graph, fixture_judge, fixture_answerer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    parser.add_argument("--llm", action="store_true", help="explicitly enable the configured paid/free API")
    parser.add_argument("--rerank", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    encoder = BGEEncoder()
    retriever = HybridRetriever(make_chunks(load_corpus(root), encoder.tokenizer), encoder)
    api = None
    try:
        if args.llm:
            from model_api import ChatAPI
            api = ChatAPI()
        graph = build_graph(retriever, api.judge if api else fixture_judge,
                            api.answer if api else fixture_answerer,
                            reranker=CrossEncoderReranker() if args.rerank else None)
        state = graph.invoke({"original_question": args.question, "history": [], "trace": []},
                             config={"recursion_limit": 20})
        print(json.dumps({"mode": "configured_llm" if api else "fixture_judge_and_extract_only",
                          "answer": state["answer"], "citations": state["citations"],
                          "trace": state["trace"]}, ensure_ascii=False, indent=2))
    finally:
        retriever.close()
        if api:
            api.close()


if __name__ == "__main__":
    main()
