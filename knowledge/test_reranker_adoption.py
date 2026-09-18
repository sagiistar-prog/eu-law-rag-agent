from copy import deepcopy
import unittest
from assess_reranker import assess


def report(positive,negative,hits,false=0):
    row={'positive_cases':positive,'negative_cases':negative,'target_evidence_hits':hits,'false_evidence_cases':false}
    return {'corpus_sha256':'example','cases_sha256':'example','ranking':{'method':'example'},
        'modes':{'hybrid':{'summary':deepcopy(row)},'rerank':{'summary':deepcopy(row)}}}


class AdoptionTests(unittest.TestCase):
    def test_improvement_below_the_predeclared_gate_does_not_enable_default(self):
        result=assess(report(24,6,24),report(3,2,2),report(16,8,10))
        self.assertFalse(result['ready_for_default'])
        self.assertFalse(result['gates']['holdout_target_hits'])

    def test_missing_negative_cases_and_changed_corpus_cannot_pass(self):
        canonical,known,holdout=report(24,6,24),report(3,2,2),report(16,8,16)
        holdout['modes']['rerank']['summary']['negative_cases']=0
        with self.assertRaises(ValueError):assess(canonical,known,holdout)
        holdout=report(16,8,16);holdout['corpus_sha256']='other'
        with self.assertRaises(ValueError):assess(canonical,known,holdout)

    def test_new_false_evidence_blocks_adoption_even_with_all_targets(self):
        holdout=report(16,8,16)
        holdout['modes']['rerank']['summary']['false_evidence_cases']=1
        self.assertFalse(assess(report(24,6,24),report(3,2,2),holdout)['ready_for_default'])
