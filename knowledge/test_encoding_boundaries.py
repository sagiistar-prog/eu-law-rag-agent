from types import SimpleNamespace
import unittest
from pipeline import Encoder, TokenLimitExceeded, search


class EncodingBoundaryTests(unittest.TestCase):
    def encoder(self):
        encoder=Encoder.__new__(Encoder)
        encoder.prefix='prefix:';encoder.max_tokens=8
        encoder.tokenizer=SimpleNamespace(encode_batch=lambda texts:[SimpleNamespace(ids=list(text)) for text in texts])
        encoder.model=SimpleNamespace(embed=lambda texts:(_ for _ in ()).throw(AssertionError('inference must not run')))
        return encoder

    def test_prefix_is_part_of_token_budget_and_long_inputs_fail(self):
        encoder=self.encoder()
        self.assertEqual(encoder.token_counts(['a'],query=True),[8])
        with self.assertRaises(TokenLimitExceeded):encoder.encode(['ab'],query=True)
        with self.assertRaises(TokenLimitExceeded):encoder.encode(['123456789'])

    def test_keyword_search_does_not_require_inference(self):
        class NoModel:
            model_id='test';dimension=2;prefix=''
            def encode(self,*args,**kwargs):raise AssertionError('keyword search invoked model')
        index={'manifest':{'model_id':'test','dimension':2,'query_prefix':''},'chunks':[{'source_id':'a','text':'押金退还'}],'vectors':[[1,0]]}
        hits=search(index,'押金',NoModel(),mode='keyword')
        self.assertEqual(hits[0]['source_id'],'a')
        self.assertIsNone(hits[0]['cosine_similarity'])


if __name__=='__main__':unittest.main()
