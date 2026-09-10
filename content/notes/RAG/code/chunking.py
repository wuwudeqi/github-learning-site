"""Chunk a heading section, preserving identity and recording the exact indexed text."""
from dataclasses import dataclass, field
import hashlib
from ingest import Section


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc_id: str
    section_id: str
    text: str
    body: str
    metadata: dict = field(default_factory=dict)


def make_chunks(sections: list[Section], tokenizer, max_tokens: int = 384,
                overlap_tokens: int = 48) -> list[Chunk]:
    chunks = []
    for section in sections:
        prefix = f"{section.title}\n{section.heading}\n"
        prefix_ids = tokenizer.encode(prefix, add_special_tokens=False)
        if callable(tokenizer):
            # Tokenize the whole section for offsets; only bounded windows are sent to the model.
            encoded = tokenizer(section.text, add_special_tokens=False, return_offsets_mapping=True, verbose=False)
            body_ids, offsets = encoded["input_ids"], encoded["offset_mapping"]
        else:
            body_ids, offsets = tokenizer.encode(section.text, add_special_tokens=False), None
        room = max_tokens - len(prefix_ids) - 2  # BGE adds CLS/SEP.
        if room <= overlap_tokens:
            raise ValueError("title too long for this token budget")
        position, part = 0, 0
        while position < len(body_ids):
            window = body_ids[position:position + room]
            # Preserve original text exactly when the whole section fits.
            if len(body_ids) <= room:
                body = section.text
            elif offsets is not None:
                # Fast tokenizer offsets keep the original Chinese spacing and punctuation.
                body = section.text[offsets[position][0]:offsets[min(position + room, len(body_ids)) - 1][1]]
            else:
                body = tokenizer.decode(window, skip_special_tokens=True)
            text = prefix + body
            if len(tokenizer.encode(text, add_special_tokens=True)) > max_tokens:
                raise ValueError("re-tokenized chunk exceeds budget; inspect tokenizer normalization")
            revision = hashlib.sha256(text.encode()).hexdigest()[:12]
            chunk_id = f"{section.doc_id}:{section.section_id}:p{part}"
            chunks.append(Chunk(chunk_id, section.doc_id, section.section_id, text, body,
                                {**section.metadata, "heading": section.heading,
                                 "revision": revision, "token_count": len(tokenizer.encode(text))}))
            if position + room >= len(body_ids):
                break
            position += room - overlap_tokens
            part += 1
    return chunks
