"""Opt-in check with the real BGE tokenizer and weights. No evaluation labels are read."""
from pathlib import Path
from ingest import Section, load_corpus
from chunking import make_chunks
from retrieval import BGEEncoder

encoder = BGEEncoder()
body = ('遇到 CICD_ACCESS_DENIED 时先打开 https://codehub.example.invalid/Aa_Bb ，核对 release/HotFix 分支。\n') * 16
chunks = make_chunks([Section('OFFSET', 's01', '偏移验证', '链接与错误码', body)], encoder.tokenizer)
assert len(chunks) > 1
assert all(c.body in body for c in chunks)
assert all('CICD_ACCESS_DENIED' in c.body for c in chunks)
assert all(len(encoder.tokenizer.encode(c.text)) <= 384 for c in chunks)
vectors = encoder.documents([c.text for c in chunks])
assert vectors.shape == (len(chunks), 512)
real_chunks = make_chunks(load_corpus(Path(__file__).resolve().parent.parent), encoder.tokenizer)
assert len({c.chunk_id for c in real_chunks}) == len(real_chunks)
print(f'PASS: real tokenizer offsets and actual BGE encoding; {len(chunks)} long-document windows; vector shape {vectors.shape}')
print(f'PASS: source corpus -> {len(real_chunks)} chunks; maximum {max(c.metadata["token_count"] for c in real_chunks)} tokens')
