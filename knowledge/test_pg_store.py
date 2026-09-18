"""Real PostgreSQL tests: KB_TEST_DATABASE_URL must point to a disposable database."""
import copy
import os
import unittest
import uuid
from pg_store import install,ingest,retrieve

@unittest.skipUnless(os.getenv('KB_TEST_DATABASE_URL'),'isolated PostgreSQL URL not provided')
class PgStoreTests(unittest.TestCase):
    def setUp(self):
        import psycopg
        self.conn=psycopg.connect(os.environ['KB_TEST_DATABASE_URL'],autocommit=True)
        install(self.conn)
        self.corpus='test-'+uuid.uuid4().hex
        self.index={'manifest':{'corpus_sha256':self.corpus,'model_id':'integration-fixture','dimension':2},
            'chunks':[{'chunk_id':'a','text':'deposit refund rental contract','review_status':'fictional'},
                      {'chunk_id':'b','text':'transport commute station','review_status':'fictional'}],
            'vectors':[[1.,0.],[0.,1.]]}
    def tearDown(self):
        self.conn.execute('DELETE FROM evidence_kb.chunks WHERE corpus_id=%s',(self.corpus,))
        self.conn.close()
    def test_idempotent_ingestion_and_hybrid_scores(self):
        ingest(self.conn,self.index);ingest(self.conn,self.index)
        count=self.conn.execute('SELECT count(*) FROM evidence_kb.chunks WHERE corpus_id=%s',(self.corpus,)).fetchone()[0]
        self.assertEqual(count,2)
        class Encoder:
            model_id='integration-fixture'
            def encode(self,texts,query=False):return [[1.,0.]]
        hits=retrieve(self.conn,self.corpus,'deposit unexpectedword',Encoder())
        self.assertEqual(hits[0]['chunk_id'],'a')
        self.assertGreater(hits[0]['keyword_score'],0)
        self.assertIn('cosine_similarity',hits[0])
        self.assertEqual(retrieve(self.conn,'different-corpus','deposit',Encoder()),[])
    def test_invalid_vector_rolls_back_the_entire_ingestion(self):
        bad=copy.deepcopy(self.index);bad['vectors'][1]=[float('nan'),0.]
        with self.assertRaises(ValueError):ingest(self.conn,bad)
        count=self.conn.execute('SELECT count(*) FROM evidence_kb.chunks WHERE corpus_id=%s',(self.corpus,)).fetchone()[0]
        self.assertEqual(count,0)

    def test_source_context_is_searchable_without_rewriting_citation_body(self):
        self.index['manifest']['document_context']='source-section'
        for chunk in self.index['chunks']:chunk['source_title']='Fictional quasar policy'
        ingest(self.conn,self.index)
        class Encoder:
            model_id='integration-fixture'
            def encode(self,texts,query=False):return [[1.,0.]]
        hits=retrieve(self.conn,self.corpus,'quasar',Encoder())
        self.assertTrue(all(hit['keyword_score']>0 for hit in hits))
        self.assertTrue(all('quasar' not in hit['text'] for hit in hits))
        self.assertEqual(hits[0]['text'],self.index['chunks'][0]['text'])

    def test_instrument_filter_precedes_nearest_neighbor_limit(self):
        self.index['chunks'][0]['instrument_id']='gdpr'
        self.index['chunks'][1]['instrument_id']='dsa'
        ingest(self.conn,self.index)
        class Encoder:
            model_id='integration-fixture'
            def encode(self,texts,query=False):return [[1.,0.]]
        hits=retrieve(self.conn,self.corpus,'deposit',Encoder(),instrument='dsa')
        self.assertEqual([h['chunk_id'] for h in hits],['b'])

    def test_lexical_candidate_outside_dense_limit_still_has_semantic_score(self):
        self.index['chunks']=[{'chunk_id':str(n),'text':'common' if n<24 else 'specialwhale','review_status':'fictional'} for n in range(25)]
        self.index['vectors']=[[1.,0.] for _ in range(24)]+[[0.,1.]]
        ingest(self.conn,self.index)
        class Encoder:
            model_id='integration-fixture'
            def encode(self,texts,query=False):return [[1.,0.]]
        hits=retrieve(self.conn,self.corpus,'specialwhale',Encoder(),top_k=25)
        candidate=next(h for h in hits if h['chunk_id']=='24')
        self.assertEqual(candidate['cosine_similarity'],0.0)

if __name__=='__main__':unittest.main()
