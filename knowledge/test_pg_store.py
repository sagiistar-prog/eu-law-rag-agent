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

if __name__=='__main__':unittest.main()
