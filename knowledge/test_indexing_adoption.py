import copy
import unittest
from unittest.mock import Mock
from assess_indexing import assess, DATASETS
from evaluate_indexing import evaluate
from evaluate_review import summarize


class IndexingAdoptionTests(unittest.TestCase):
    def report(self):
        datasets={}
        for name,(positive,negative) in DATASETS.items():
            rows=[{'id':str(i),'query':'Fictional question '+str(i),'expected':['s'] if i<positive else [],
                'candidates':['s'],'candidate_top1':'s','evidence':['s'] if i<positive else [],'elapsed_ms':10}
                for i in range(positive+negative)]
            datasets[name]={'cases':rows,'summary':summarize(rows)}
        baseline={'manifest':{'corpus_sha256':'baseline'},'datasets':datasets}
        candidate=copy.deepcopy(baseline);candidate['manifest']['corpus_sha256']='candidate'
        return {'results':{'index':baseline,'candidate':candidate}}

    def test_candidate_gains_cannot_offset_a_canonical_regression(self):
        report=self.report();data=report['results']['candidate']['datasets']['official-cases']
        data['cases'][0]['evidence']=[];data['summary']=summarize(data['cases'])
        decision=assess(report)
        self.assertFalse(decision['candidates']['candidate']['ready_for_default'])
        self.assertFalse(decision['default_changed'])

    def test_false_evidence_precision_and_latency_are_independent_gates(self):
        report=self.report();data=report['results']['candidate']['datasets']['official-cases']
        data['cases'][-1]['evidence']=['s']
        for row in data['cases']:
            row['elapsed_ms']=41
            if row['expected']:row['evidence'].append('unrelated')
        data['summary']=summarize(data['cases'])
        gates=assess(report)['candidates']['candidate']['gates']
        for key in ('false_evidence','precision','latency'):self.assertFalse(gates['official-cases_'+key])

    def test_missing_rows_invented_metrics_and_invalid_latency_cannot_pass(self):
        for change in ('missing','metric','nan','labels'):
            report=self.report();data=report['results']['candidate']['datasets']['official-cases']
            if change=='missing':data['cases'].pop()
            if change=='metric':data['summary']['target_evidence_hits']=23
            if change=='nan':data['cases'][0]['elapsed_ms']=float('nan')
            if change=='labels':data['cases'][0]['query']='Changed question'
            with self.assertRaises(ValueError):assess(report)

    def test_missing_source_snapshots_fail_before_inference(self):
        encoder=Mock()
        for indexes in ({},{'first':{}},{'first':{'sources':{'a':1},'manifest':{}},'other':{'sources':{'b':2}}}):
            with self.assertRaises(ValueError):evaluate(indexes,{'cases':[]},encoder)
        encoder.encode.assert_not_called()


if __name__=='__main__':unittest.main()
