"""Source review layer for an explicit publication snapshot, without legal conclusions."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re

from pipeline import Encoder, evidence_answer, search
ROOT=Path(__file__).resolve().parents[1]


def select_index(index, instrument='all'):
    available = {c.get('instrument_id') for c in index['chunks']} - {None}
    if instrument != 'all' and instrument not in available:
        raise ValueError('Unknown instrument')
    pairs = [(c, v) for c, v in zip(index['chunks'], index['vectors']) if instrument == 'all' or c.get('instrument_id') == instrument]
    return {**index, 'chunks': [c for c, _ in pairs], 'vectors': [v for _, v in pairs]}


def coverage(index):
    sources = index.get('sources', {})
    instruments = sorted({c.get('instrument_id') for c in index['chunks']} - {None})
    return {'sources': len({c['source_id'] for c in index['chunks']}), 'chunks': len(index['chunks']),
        'instruments': instruments, 'language': 'en',
        'document_versions': sorted({s.get('document_version', 'user_supplied') for s in sources.values()}),
        'corpus_sha256': index['manifest']['corpus_sha256'],
        'created_at': index['manifest'].get('created_at'),
        'source_catalog': [{k:s.get(k) for k in ('source_id','source_title','instrument_id','section','celex','publication_date','document_version','source_url')} for s in sources.values()]}


def validate_result(result):
    from jsonschema import Draft202012Validator
    Draft202012Validator(json.loads((ROOT/'schemas/evidence-review.schema.json').read_text(encoding='utf-8'))).validate(result)


def query_policy(query, index):
    if not isinstance(query, str) or not query.strip() or len(query) > 1000:
        raise ValueError('请输入 1 到 1000 字的问题。')
    if re.search(r'[\u4e00-\u9fff]', query):
        return 'english_required', '当前资料和模型为英文，请用英文查询。'
    if any(c.get('document_version') == 'original_oj' for c in index['chunks']):
        if re.search(r'\b(current|currently|latest|today|now|compliant|compliance verdict)\b|can (we|i) (launch|legally)', query, re.I):
            return 'version_review_required', '本库收录原始公报版本。请先核对修订与适用日期，再判断当前义务。可改问某条原文如何表述。'
    return None, None


def research(index, query, encoder, instrument='all', retriever=None):
    selected = select_index(index, instrument)
    reason, message = query_policy(query, selected)
    hits = [] if reason else (retriever(query, instrument) if retriever else search(selected, query, encoder, top_k=12))
    # Show distinct articles first, not five near-duplicate windows of one provision.
    distinct, seen = [], set()
    for hit in hits:
        if hit['source_id'] not in seen:
            distinct.append(hit); seen.add(hit['source_id'])
        if len(distinct) == 5:
            break
    result = evidence_answer(query, distinct)
    emitted={hit['source_id'] for hit in result['evidence']}
    if reason:
        result.update(answer_status='insufficient_evidence', reason=reason, next_step=message)
    result.update(schema_version='1.1', instrument=instrument,
        corpus_sha256=index['manifest']['corpus_sha256'],
        created_at=datetime.now(timezone.utc).isoformat(),
        version_scope='原始公报摘录，未核验修订及当前适用性。' if any(c.get('document_version') == 'original_oj' for c in selected['chunks']) else '调用者提供的资料。',
        review_candidates=[h for h in distinct if h['source_id'] not in emitted and
            ((h['keyword_score'] > 0 and h['review_status'] == 'pending') or
             (h['review_status'] == 'source_verified' and (h.get('cosine_similarity') or 0)>=.55))])
    validate_result(result)
    return result


def markdown(result):
    lines = ['# EU law source review', '', result['query'], '', result['version_scope'], '',
        f"Snapshot: {result['corpus_sha256']}", '', f"Scope: {result['instrument']}", '',
        '## Evidence', '']
    if not result['evidence']:
        lines += [result['next_step'], '']
    for hit in result['evidence']:
        lines += [f"### {hit['source_title']}", '', hit['text'], '',
            f"Source: {hit['source_url']}", f"CELEX: {hit.get('celex', 'not provided')}",
            f"Publication: {hit.get('publication_date', 'not provided')}",
            f"Retrieved: {hit['retrieved_at']}", f"Chunk: {hit['chunk_id']}", '']
    if result.get('review_candidates'):
        lines += ['## Related candidates, not supporting evidence', '']
        for hit in result['review_candidates']:
            lines += [f"- {hit['source_title']}: {hit['source_url']}"]
        lines.append('')
    lines += ['## Questions for review', '', '- Check amendments and corrigenda against the official record.',
        '- Confirm the facts, addressee, scope and application date.', '- Record unresolved points before making a decision.', '',
        'These are source extracts, not a legal conclusion or legal advice.', '']
    return '\n'.join(lines)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--index', type=Path, required=True)
    request=parser.add_mutually_exclusive_group(required=True)
    request.add_argument('--query')
    request.add_argument('--request', type=Path)
    parser.add_argument('--instrument', default='all')
    parser.add_argument('--cache-dir', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.request:
        from jsonschema import Draft202012Validator
        if args.request.stat().st_size>8192:raise ValueError('Request exceeds 8 KB')
        data=json.loads(args.request.read_text(encoding='utf-8-sig'))
        Draft202012Validator(json.loads((ROOT/'schemas/research-input.schema.json').read_text(encoding='utf-8'))).validate(data)
        args.query=data['query'];args.instrument=data.get('instrument','all')
    destination = args.output.resolve()
    allowed = Path(__file__).resolve().parents[1] / 'output'
    if destination == allowed or not destination.is_relative_to(allowed):
        raise ValueError('Choose a new directory inside output/')
    if destination.exists():
        raise ValueError('Existing review is preserved; choose a new directory')
    if not args.index.resolve().is_relative_to(ROOT):raise ValueError('Index must be inside the repository')
    index = json.loads(args.index.read_text(encoding='utf-8'))
    result = research(index, args.query, Encoder('en', str(args.cache_dir) if args.cache_dir else None), args.instrument)
    destination.mkdir(parents=True, exist_ok=False)
    (destination / 'evidence.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    (destination / 'review.md').write_text(markdown(result), encoding='utf-8')
    print(json.dumps({'status': result['answer_status'], 'sources': len(result['evidence'])}))
