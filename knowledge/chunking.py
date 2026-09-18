"""Bounded source spans. Paragraph boundaries are structure, not semantic judgments."""
import re


def character_spans(text, size=320, overlap=40):
    if not 0 <= overlap < size or size < 2:
        raise ValueError('Invalid chunk size or overlap')
    for offset in range(0, len(text), size-overlap):
        raw = text[offset:offset+size]
        fragment = raw.strip()
        if fragment:
            yield offset + len(raw)-len(raw.lstrip()), fragment


def paragraph_spans(text, size=1200, overlap=160):
    if not 0 <= overlap < size or size < 2:
        raise ValueError('Invalid chunk size or overlap')
    start = 0
    while start < len(text):
        limit = min(start + size, len(text))
        end = limit
        if limit < len(text):
            # Prefer a complete paragraph, then sentence, then word near the limit.
            lower = start + size // 2
            for pattern in (r'\n\s*\n', r'(?<=[.!?;])\s+', r'\s+'):
                boundaries = [m.end() for m in re.finditer(pattern, text[start:limit]) if start + m.end() >= lower]
                if boundaries:
                    end = start + boundaries[-1]
                    break
        raw = text[start:end]
        trimmed = raw.strip()
        if trimmed:
            exact_start = start + len(raw) - len(raw.lstrip())
            yield exact_start, trimmed
        if end == len(text):
            break
        next_start = max(start + 1, end - overlap)
        # Align overlap to a word boundary without moving past the prior end.
        boundary = re.search(r'\s+', text[next_start:end])
        if boundary:
            next_start += boundary.end()
        start = next_start


def retrieval_text(chunk, context='none'):
    if context == 'none':
        return chunk['text']
    if context != 'source-section':
        raise ValueError('Unknown document context format')
    return '\n'.join(value for value in (chunk['source_title'], chunk.get('section', ''), chunk['text']) if value)
