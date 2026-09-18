"""Paired review regression; authored labels are not expert legal judgments."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
import time

from pipeline import Encoder
from research import research
from reranker import Reranker


def validate_cases(cases, index):
    known = {c['source_id'] for c in index['chunks']}
    if not cases or not any(c['expect_evidence'] for c in cases) or not any(not c['expect_evidence'] for c in cases):
        raise ValueError('Positive and negative cases required')
    if len({c['id'] for c in cases}) != len(cases):
        raise ValueError('Duplicate case IDs')
    for case in cases:
        if bool(case['relevant_sources']) != case['expect_evidence'] or not set(case['relevant_sources']).issubset(known):
            raise ValueError('Missing or unknown source labels')


def summarize(rows):
    positive = [row for row in rows if row['expected']]
    negative = [row for row in rows if not row['expected']]
    latency = sorted(row['elapsed_ms'] for row in rows)
    return {'cases':len(rows), 'positive_cases':len(positive), 'negative_cases':len(negative),
        'target_top1':sum(row['candidate_top1'] in row['expected'] for row in positive),
        'target_top5':sum(bool(set(row['candidates']) & set(row['expected'])) for row in positive),
        'target_evidence_hits':sum(bool(set(row['evidence']) & set(row['expected'])) for row in positive),
        'false_evidence_cases':sum(bool(row['evidence']) for row in negative),
        'mean_positive_source_precision':sum(len(set(row['evidence']) & set(row['expected']))/len(row['evidence']) if row['evidence'] else 0 for row in positive)/len(positive),
        'latency_p50_ms':latency[math.ceil(len(latency)*.5)-1],
        'latency_p95_ms':latency[math.ceil(len(latency)*.95)-1]}


def evaluate(index, cases, encoder, reranker):
    validate_cases(cases, index)
    modes = {}
    for mode, ranker in [('hybrid',None), ('rerank',reranker)]:
        rows=[]
        for case in cases:
            start=time.perf_counter()
            result=research(index,case['query'],encoder,case.get('instrument','all'),reranker=ranker)
            candidates=[h['source_id'] for h in result['candidates']]
            rows.append({'id':case['id'], 'query':case['query'], 'expected':case['relevant_sources'],
                'candidates':candidates, 'candidate_top1':candidates[0] if candidates else None,
                'evidence':[h['source_id'] for h in result['evidence']],
                'scores':[{'source_id':h['source_id'],'rerank_score':h.get('rerank_score')} for h in result['candidates']],
                'elapsed_ms':round((time.perf_counter()-start)*1000,3)})
        modes[mode]={'summary':summarize(rows),'cases':rows}
    return {'scope':'author-labeled paired article retrieval; not legal correctness or customer effects',
        'created_at':datetime.now(timezone.utc).isoformat(),
        'corpus_sha256':index['manifest']['corpus_sha256'], 'ranking':reranker.manifest,
        'latency_scope':'warm loaded models; local CPU; no HTTP/database; baseline runs first', 'modes':modes}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--index',type=Path,required=True)
    parser.add_argument('--cases',type=Path,required=True)
    parser.add_argument('--frozen-manifest',type=Path)
    parser.add_argument('--cache-dir',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise ValueError('Existing evaluation preserved; choose a new output')
    case_bytes=args.cases.read_bytes();digest=sha256(case_bytes).hexdigest()
    if args.frozen_manifest:
        frozen=json.loads(args.frozen_manifest.read_text(encoding='utf-8'))
        if frozen['sha256']!=digest:raise ValueError('Frozen holdout changed')
    index=json.loads(args.index.read_text(encoding='utf-8'))
    cases=json.loads(case_bytes)
    cache=str(args.cache_dir) if args.cache_dir else None
    report=evaluate(index,cases,Encoder('en',cache),Reranker(cache))
    report['cases_sha256']=digest
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8') as handle:json.dump(report,handle,ensure_ascii=False,indent=2)
    print(json.dumps({k:v['summary'] for k,v in report['modes'].items()}))
