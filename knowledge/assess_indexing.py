"""Fail closed against the indexing protocol; an experiment never changes defaults."""
import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
from evaluate_review import summarize

DATASETS={'official-cases':(24,6),'known-paraphrase-cases':(3,2),'paraphrase-holdout-v1':(16,8)}


def assess(report, baseline='index'):
    results=report['results']
    if baseline not in results or len(results)<2:
        raise ValueError('A baseline and candidate are required')
    reference=results[baseline]
    for result in results.values():
        if set(result['datasets'])!=set(DATASETS):
            raise ValueError('All three regression datasets are required')
        for name,(positive,negative) in DATASETS.items():
            data=result['datasets'][name]; rows=data['cases']; summary=data['summary']
            if not rows or len({r['id'] for r in rows})!=len(rows):
                raise ValueError('Missing or duplicate case rows')
            if any(not math.isfinite(r['elapsed_ms']) or r['elapsed_ms']<=0 for r in rows):
                raise ValueError('Invalid measured latency')
            if summarize(rows)!=summary:
                raise ValueError('Reported metrics do not match the case rows')
            if (summary['positive_cases'],summary['negative_cases'])!=(positive,negative):
                raise ValueError('Incomplete evaluation denominator')
            labels=lambda items:{r['id']:(r['query'],r['expected']) for r in items}
            if labels(rows)!=labels(reference['datasets'][name]['cases']):
                raise ValueError('Variants must use the same cases and labels')
    candidates={}
    for name,result in results.items():
        if name==baseline:continue
        summaries={key:data['summary'] for key,data in result['datasets'].items()}
        gates={'canonical_target_hits':summaries['official-cases']['target_evidence_hits']==24,
               'paraphrase_target_hits':summaries['paraphrase-holdout-v1']['target_evidence_hits']>=12}
        for dataset,summary in summaries.items():
            base=reference['datasets'][dataset]['summary']
            gates[dataset+'_false_evidence']=summary['false_evidence_cases']<=base['false_evidence_cases']
            gates[dataset+'_precision']=summary['mean_positive_source_precision']>=base['mean_positive_source_precision']
            gates[dataset+'_latency']=summary['latency_p50_ms']<=4*base['latency_p50_ms']
        candidates[name]={'gates':gates,'ready_for_default':all(gates.values()),
            'corpus_sha256':result['manifest']['corpus_sha256']}
    return {'scope':'Observed author-labeled regression, not independent validation or legal accuracy',
        'baseline':baseline,'default_changed':False,'candidates':candidates}


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--comparison',type=Path,required=True)
    p.add_argument('--baseline',default='index')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--require-ready',action='store_true')
    args=p.parse_args()
    raw=args.comparison.read_bytes();result=assess(json.loads(raw),args.baseline)
    result['comparison_sha256']=sha256(raw).hexdigest()
    with args.output.open('x',encoding='utf-8') as file:json.dump(result,file,indent=2)
    print(json.dumps(result))
    if args.require_ready and not any(c['ready_for_default'] for c in result['candidates'].values()):
        raise SystemExit(2)
