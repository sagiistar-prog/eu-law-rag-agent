"""Apply predeclared adoption gates; successful execution is not adoption approval."""
import argparse
import json
from pathlib import Path


def assess(canonical, known, holdout):
    reports=[canonical,known,holdout]
    if len({r['corpus_sha256'] for r in reports})!=1 or any(r['ranking']!=canonical['ranking'] for r in reports):
        raise ValueError('Comparisons must use the same corpus and ranking policy')
    expected=[(24,6),(3,2),(16,8)]
    for report,(positive,negative) in zip(reports,expected):
        for mode in ('hybrid','rerank'):
            row=report['modes'][mode]['summary']
            if (row['positive_cases'],row['negative_cases'])!=(positive,negative):
                raise ValueError('Incomplete evaluation denominator')
    c,k,h=[r['modes']['rerank']['summary'] for r in reports]
    base=holdout['modes']['hybrid']['summary']
    gates={'canonical_target_hits':c['target_evidence_hits']==24,
        'canonical_no_false_evidence':c['false_evidence_cases']==0,
        'known_paraphrases':k['target_evidence_hits']>=2,
        'known_no_false_evidence':k['false_evidence_cases']==0,
        'holdout_target_hits':h['target_evidence_hits']>=12,
        'holdout_false_evidence':h['false_evidence_cases']<=min(2,base['false_evidence_cases'])}
    return {'scope':'predeclared engineering adoption decision; not legal certification',
        'gates':gates,'ready_for_default':all(gates.values()),
        'default_mode':'hybrid','candidate_mode':'explicit opt-in rerank',
        'holdout_cases_sha256':holdout['cases_sha256'],
        'corpus_sha256':holdout['corpus_sha256'], 'ranking':holdout['ranking']}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('canonical','known','holdout','output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--require-ready',action='store_true')
    args=parser.parse_args()
    result=assess(*[json.loads(getattr(args,key).read_text(encoding='utf-8')) for key in ('canonical','known','holdout')])
    with args.output.open('x',encoding='utf-8') as handle:json.dump(result,handle,indent=2)
    print(json.dumps(result))
    if args.require_ready and not result['ready_for_default']:raise SystemExit(2)
