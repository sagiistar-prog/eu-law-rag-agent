import unittest
from pipeline import clean,prepare,bm25,fuse,search,evidence_answer

class PipelineTests(unittest.TestCase):
    def doc(self,**kwargs):
        return {'source_id':'a','source_title':'Fixture','source_url':'https://example.org/a','retrieved_at':'2026-09-17','text':'Do not use 20 mg.\n\n| field | value |','review_status':'fictional',**kwargs}
    def test_clean_preserves_negation_tables_and_units(self):
        self.assertEqual(clean('\ufeffDo not use 20 mg.\r\n\r\n| field | value |').lstrip('\ufeff'),self.doc()['text'])
    def test_missing_provenance_rejected(self):
        with self.assertRaises(ValueError):prepare([{'text':'anonymous source'}])
    def test_chunk_bounds_and_provenance(self):
        chunks=prepare([self.doc(text='abc '*300)])
        self.assertTrue(all(len(c['text'])<=320 for c in chunks))
        self.assertTrue(all(c['source_id']=='a' for c in chunks))
        self.assertEqual(len({c['content_sha256'] for c in chunks}),len(chunks))
    def test_duplicate_source_rejected(self):
        with self.assertRaises(ValueError):prepare([self.doc(),self.doc()])
    def test_bm25_and_rrf(self):
        chunks=[self.doc(text='document retention deletion'),self.doc(text='tariff classification')]
        self.assertEqual(bm25('retention',chunks)[0][0],0)
        self.assertEqual(fuse([(0,20),(1,2)],[(1,.9),(2,.8)])[0][0],1)
    def test_nearest_neighbor_not_automatically_evidence(self):
        hit={**self.doc(),'keyword_score':0,'cosine_similarity':.9}
        self.assertEqual(evidence_answer('unrelated',[hit])['answer_status'],'insufficient_evidence')
        hit['keyword_score']=1;hit['review_status']='pending'
        self.assertEqual(evidence_answer('retention',[hit])['answer_status'],'insufficient_evidence')
    def test_quote_budget_across_chunks(self):
        hits=[{**self.doc(text='one two three four'),'keyword_score':1}]*3
        answer=evidence_answer('one',hits,max_words=5)
        self.assertEqual(sum(len(h['text'].split()) for h in answer['evidence']),5)
    def test_model_mismatch_rejected_before_inference(self):
        class Fake: model_id='other';dimension=2;prefix=''
        with self.assertRaises(ValueError):search({'manifest':{'model_id':'old','dimension':2,'query_prefix':''}},'query',Fake())

if __name__=='__main__':unittest.main()
