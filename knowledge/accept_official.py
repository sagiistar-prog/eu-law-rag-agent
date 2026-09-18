"""Actual HTTP/database acceptance over the selected official publication snapshot."""
import argparse
import json
from pathlib import Path
import urllib.request
from research import validate_result


def accept(base, cases):
    if base not in ('http://127.0.0.1:8892','http://localhost:8892'):
        raise ValueError('Acceptance targets the isolated local service on port 8892')
    with urllib.request.urlopen(base+'/health') as response:health=json.load(response)
    if health['storage']!='postgres-pgvector':raise ValueError('Actual PostgreSQL service required')
    with urllib.request.urlopen(base+'/coverage') as response:coverage=json.load(response)
    corpus=coverage['corpus_sha256']
    if not cases or not any(c['expect_evidence'] for c in cases) or not any(not c['expect_evidence'] for c in cases):
        raise ValueError('Both relevant and missing-source cases are required')
    rows=[]
    for case in cases:
        request=urllib.request.Request(base+'/search',data=json.dumps({'query':case['query'],'instrument':case.get('instrument','all')}).encode(),headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(request) as response:result=json.load(response)
        validate_result(result)
        if result['corpus_sha256']!=corpus:raise ValueError('Corpus changed during acceptance')
        ids=[h['source_id'] for h in result['evidence']]
        isolated=all(h.get('instrument_id')==case['instrument'] for h in result['evidence']) if case.get('instrument') else True
        passed=bool(set(ids)&set(case['relevant_sources'])) if case['expect_evidence'] else not ids
        rows.append({'id':case['id'],'expected':case['relevant_sources'],'evidence':ids,'instrument_isolated':isolated,'passed':passed and isolated})
    return {'scope':'authored article relevance and missing-source development regression, not legal correctness',
        'health':health,'corpus_sha256':corpus,'passed':sum(r['passed'] for r in rows),'total':len(rows),'cases':rows}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--base',default='http://127.0.0.1:8892')
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    report=accept(args.base,json.loads(Path(__file__).with_name('evaluation').joinpath('official-cases.json').read_text(encoding='utf-8')))
    with args.output.open('x',encoding='utf-8') as handle:json.dump(report,handle,indent=2)
    print(json.dumps({'passed':report['passed'],'total':report['total']}))
    if report['passed']!=report['total']:raise SystemExit(2)
