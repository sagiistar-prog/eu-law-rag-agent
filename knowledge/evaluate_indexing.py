"""Compare source-identical indexing variants on previously observed regression sets."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import time
from pipeline import Encoder
from research import research
from evaluate_review import validate_cases, summarize


def evaluate(indexes, datasets, encoder):
    if not indexes or not datasets:
        raise ValueError('Indexes and regression datasets are required')
    first = next(iter(indexes.values()))
    if not first.get('sources'):
        raise ValueError('Source snapshots are required for paired evaluation')
    for index in indexes.values():
        if index.get('sources') != first.get('sources'):
            raise ValueError('Index variants must contain identical source snapshots')
        if any(index['manifest'].get(key)!=first['manifest'].get(key) for key in
               ('model_id','dimension','query_prefix','tokenizer_sha256')):
            raise ValueError('Index variants must use the same encoder')
    for index in indexes.values():
        for cases in datasets.values():validate_cases(cases,index)
    results = {}
    for name, index in indexes.items():
        results[name] = {'manifest': index['manifest'], 'chunks': len(index['chunks']), 'datasets': {}}
        for dataset, cases in datasets.items():
            validate_cases(cases, index)
            rows = []
            for case in cases:
                start = time.perf_counter()
                result = research(index, case['query'], encoder, case.get('instrument', 'all'))
                candidates = [h['source_id'] for h in result['candidates']]
                rows.append({'id': case['id'], 'query': case['query'], 'expected': case['relevant_sources'],
                    'candidates': candidates, 'candidate_top1': candidates[0] if candidates else None,
                    'evidence': [h['source_id'] for h in result['evidence']],
                    'elapsed_ms': round((time.perf_counter()-start)*1000, 3)})
            results[name]['datasets'][dataset] = {'summary': summarize(rows), 'cases': rows}
    return {'created_at': datetime.now(timezone.utc).isoformat(),
        'scope': 'Previously observed author-labeled regression. Not independent evaluation, legal accuracy, or user outcomes.',
        'latency_scope': 'Warm model local CPU; includes query encoding; baseline runs first; no HTTP/database.',
        'results': results}


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--index', type=Path, action='append', required=True)
    p.add_argument('--cases', type=Path, action='append', required=True)
    p.add_argument('--cache-dir', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a=p.parse_args()
    if a.output.exists(): raise ValueError('Existing evaluation preserved')
    if len({x.stem for x in a.index}) != len(a.index) or len({x.stem for x in a.cases}) != len(a.cases):
        raise ValueError('Use distinct index and dataset names')
    indexes={path.stem:json.loads(path.read_text(encoding='utf-8')) for path in a.index}
    datasets={path.stem:json.loads(path.read_text(encoding='utf-8')) for path in a.cases}
    report=evaluate(indexes,datasets,Encoder('en',str(a.cache_dir) if a.cache_dir else None))
    report['case_files']={path.stem:sha256(path.read_bytes()).hexdigest() for path in a.cases}
    report['index_files']={path.stem:sha256(path.read_bytes()).hexdigest() for path in a.index}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x',encoding='utf-8') as file: json.dump(report,file,ensure_ascii=False,indent=2)
    print(json.dumps({name:{d:rows['summary'] for d,rows in result['datasets'].items()} for name,result in report['results'].items()}))
