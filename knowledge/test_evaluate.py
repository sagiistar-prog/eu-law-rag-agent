import unittest
from evaluate import score, summarize, validate_cases, release_gate


class EvaluationTests(unittest.TestCase):
    def case(self, **changes):
        return {'id':'case-a','query':'押金','category':'test','relevant_sources':['a','b'], 'expect_evidence':True, **changes}

    def hit(self, source, **changes):
        return {'source_id':source,'text':'deposit refund','keyword_score':1,'review_status':'fictional', **changes}

    def test_repeated_chunks_do_not_inflate_source_recall(self):
        row=score(self.case(),[self.hit('x'),self.hit('a'),self.hit('a')],10)
        self.assertEqual(row['recall_at_k'],.5)
        self.assertEqual(row['reciprocal_rank'],.5)
        self.assertEqual(row['source_precision'],.5)

    def test_negative_denominator_and_unrated_empty_slice(self):
        row=score(self.case(relevant_sources=[],expect_evidence=False),[self.hit('x')],12)
        result=summarize([row])
        self.assertEqual(result['false_evidence_rate'],1)
        self.assertIsNone(result['recall_at_k'])
        self.assertEqual(result['retrieval_labeled_cases'],0)
        self.assertIsNone(summarize([])['latency_p95_ms'])

    def test_pending_source_can_be_retrieved_without_becoming_evidence(self):
        row=score(self.case(relevant_sources=['a'],expect_evidence=False),[self.hit('a',review_status='pending')],5)
        self.assertEqual(row['recall_at_k'],1)
        self.assertTrue(row['evidence_policy_passed'])

    def test_missing_labels_and_unknown_sources_fail_before_scoring(self):
        for rows in [[],[self.case(relevant_sources=[])],[self.case(relevant_sources=['unknown'])],[self.case(),self.case()]]:
            with self.assertRaises(ValueError):validate_cases(rows,{'a','b'})

    def test_region_leak_is_reported_separately_from_recall(self):
        row=score(self.case(jurisdiction='北京'),[self.hit('a',jurisdiction='上海')],5)
        self.assertEqual(row['jurisdiction_leaks'],['a'])

    def test_gate_cannot_pass_without_the_relevant_denominators(self):
        report={'results':{'hybrid':{'summary':{'hit_rate_at_k':1,'false_evidence_rate':None,'jurisdiction_leak_cases':0}}}}
        self.assertFalse(release_gate(report,1,0)['passed'])
        report['results']['hybrid']['summary']['false_evidence_rate']=0
        self.assertTrue(release_gate(report,1,0)['passed'])
        report['results']['hybrid']['summary']['jurisdiction_leak_cases']=1
        self.assertFalse(release_gate(report,1,0)['passed'])


if __name__=='__main__':unittest.main()
