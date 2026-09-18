"""Reproducible, source-level retrieval evaluation without an LLM judge.

The report never contains corpus text. Labels are authored test hypotheses,
not expert judgments. Keep this distinction when presenting the metrics.
"""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
import statistics
import time

from pipeline import Encoder, evidence_answer, search


def validate_cases(cases, source_ids):
    if not isinstance(cases, list) or not cases:
        raise ValueError('Provide a nonempty case list')
    seen = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError('Every case must be an object')
        if not isinstance(case.get('id'), str) or not case['id'] or case['id'] in seen:
            raise ValueError('Case IDs must be nonempty and unique')
        seen.add(case['id'])
        if not isinstance(case.get('query'), str) or not case['query'].strip():
            raise ValueError('Case query required')
        expected = case.get('relevant_sources')
        if not isinstance(expected, list) or any(not isinstance(s, str) for s in expected):
            raise ValueError('relevant_sources must be a list of source IDs')
        if len(expected) != len(set(expected)) or not set(expected) <= source_ids:
            raise ValueError('Duplicate or unknown relevant source ID')
        if type(case.get('expect_evidence')) is not bool:
            raise ValueError('expect_evidence must be boolean')
        if case['expect_evidence'] and not expected:
            raise ValueError('Answerable cases need labeled sources')
        if not isinstance(case.get('category'), str) or not case['category']:
            raise ValueError('Case category required')


def score(case, hits, elapsed_ms):
    expected = set(case['relevant_sources'])
    found = {h['source_id'] for h in hits}
    ranks = [i + 1 for i, hit in enumerate(hits) if hit['source_id'] in expected]
    answer = evidence_answer(case['query'], hits)
    emitted = bool(answer['evidence'])
    evidence_sources = {h['source_id'] for h in answer['evidence']}
    region = case.get('jurisdiction')
    leaked = [h['source_id'] for h in hits if region and h.get('jurisdiction') not in ('全国', region)]
    return {
        'id': case['id'], 'category': case['category'],
        'query': case['query'], 'relevant_sources': sorted(expected),
        'retrieved_sources': [h['source_id'] for h in hits],
        'recall_at_k': len(found & expected) / len(expected) if expected else None,
        'reciprocal_rank': 1 / min(ranks) if ranks else (0.0 if expected else None),
        'hit_at_k': bool(ranks) if expected else None,
        'source_precision': len(found & expected) / len(found) if expected and found else (0.0 if expected else None),
        'expect_evidence': case['expect_evidence'], 'emitted_evidence': emitted,
        'evidence_policy_passed': emitted == case['expect_evidence'],
        'unlabeled_evidence_sources': sorted(evidence_sources - expected),
        'jurisdiction_leaks': leaked, 'elapsed_ms': round(elapsed_ms, 3),
    }


def summarize(rows):
    def mean(key):
        values = [float(row[key]) for row in rows if row[key] is not None]
        return round(statistics.mean(values), 6) if values else None
    negatives = [row for row in rows if not row['expect_evidence']]
    durations = sorted(row['elapsed_ms'] for row in rows)
    return {
        'cases': len(rows), 'retrieval_labeled_cases': sum(row['recall_at_k'] is not None for row in rows),
        'no_evidence_cases': len(negatives), 'recall_at_k': mean('recall_at_k'),
        'mrr_at_k': mean('reciprocal_rank'), 'hit_rate_at_k': mean('hit_at_k'),
        'mean_source_precision': mean('source_precision'),
        'evidence_policy_accuracy': mean('evidence_policy_passed'),
        'false_evidence_rate': round(sum(row['emitted_evidence'] for row in negatives) / len(negatives), 6) if negatives else None,
        'jurisdiction_leak_cases': sum(bool(row['jurisdiction_leaks']) for row in rows),
        'latency_p50_ms': round(statistics.median(durations), 3) if durations else None,
        'latency_p95_ms': durations[max(0, math.ceil(len(durations) * .95) - 1)] if durations else None,
    }


def evaluate(index, cases, encoder, top_k=3):
    if not 1 <= top_k <= 20:
        raise ValueError('top_k must be 1..20')
    validate_cases(cases, {c['source_id'] for c in index['chunks']})
    results = {}
    for mode in ('keyword', 'dense', 'hybrid'):
        rows = []
        for case in cases:
            filtered = index
            if case.get('jurisdiction'):
                pairs = [(c, v) for c, v in zip(index['chunks'], index['vectors']) if c.get('jurisdiction') in ('全国', case['jurisdiction'])]
                filtered = {**index, 'chunks': [c for c, _ in pairs], 'vectors': [v for _, v in pairs]}
            started = time.perf_counter()
            hits = search(filtered, case['query'], encoder, top_k, mode)
            rows.append(score(case, hits, (time.perf_counter() - started) * 1000))
        results[mode] = {'summary': summarize(rows), 'categories': {
            category: summarize([row for row in rows if row['category'] == category])
            for category in sorted({row['category'] for row in rows})}, 'cases': rows}
    return {
        'schema_version': 1, 'created_at': datetime.now(timezone.utc).isoformat(),
        'scope': 'authored component regression set; not expert accuracy, user outcomes, or web E2E',
        'top_k': top_k, 'corpus_sha256': index['manifest']['corpus_sha256'],
        'cases_sha256': sha256(json.dumps(cases, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
        'model': index['manifest']['model_id'], 'dimension': index['manifest']['dimension'],
        'latency_scope': 'model loaded; dense/hybrid include query inference, keyword does not; no web/database latency or hardware isolation',
        'metrics_scope': 'source IDs labeled relevant; source hit does not prove passage relevance',
        'results': results,
    }


def release_gate(report, min_hit_rate=None, max_false_evidence_rate=None, mode='hybrid'):
    thresholds={'hit_rate_at_k':min_hit_rate,'false_evidence_rate':max_false_evidence_rate}
    if all(value is None for value in thresholds.values()):return None
    if any(value is not None and (not math.isfinite(value) or not 0 <= value <= 1) for value in thresholds.values()):
        raise ValueError('Gate thresholds must be finite values in 0..1')
    summary=report['results'][mode]['summary'];checks=[]
    for metric, threshold in thresholds.items():
        if threshold is None:continue
        observed=summary[metric]
        passed=observed is not None and (observed >= threshold if metric=='hit_rate_at_k' else observed <= threshold)
        checks.append({'metric':metric,'threshold':threshold,'observed':observed,'passed':passed})
    checks.append({'metric':'jurisdiction_leak_cases','threshold':0,'observed':summary['jurisdiction_leak_cases'],'passed':summary['jurisdiction_leak_cases']==0})
    return {'mode':mode,'passed':all(check['passed'] for check in checks),'checks':checks}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--index', type=Path, required=True)
    parser.add_argument('--cases', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--language', choices=['zh', 'en'], default='zh')
    parser.add_argument('--cache-dir', type=Path)
    parser.add_argument('--top-k', type=int, default=3)
    parser.add_argument('--min-hit-rate', type=float)
    parser.add_argument('--max-false-evidence-rate', type=float)
    parser.add_argument('--gate-mode', choices=['keyword','dense','hybrid'], default='hybrid')
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Choose a new report filename; previous results are preserved')
    index = json.loads(args.index.read_text(encoding='utf-8-sig'))
    cases = json.loads(args.cases.read_text(encoding='utf-8-sig'))
    # Validate before downloading or loading a model.
    validate_cases(cases, {c['source_id'] for c in index['chunks']})
    report = evaluate(index, cases, Encoder(args.language, str(args.cache_dir) if args.cache_dir else None), args.top_k)
    report['release_gate']=release_gate(report,args.min_hit_rate,args.max_false_evidence_rate,args.gate_mode)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as output:
        json.dump(report, output, ensure_ascii=False, indent=2, allow_nan=False)
    print(json.dumps({mode: value['summary'] for mode, value in report['results'].items()}, ensure_ascii=False))
    if report['release_gate'] and not report['release_gate']['passed']:raise SystemExit(2)


if __name__ == '__main__':
    main()
