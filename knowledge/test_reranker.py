"""Failure boundaries use synthetic scores; integration evaluation uses real ONNX."""
import tempfile
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from pipeline import TokenLimitExceeded, evidence_answer
from reranker import Reranker, verify_files, contexts


class RerankerTests(unittest.TestCase):
    def make_ranker(self, scores, counts):
        ranker = Reranker.__new__(Reranker)
        ranker.model = Mock()
        ranker.model.rerank.return_value = iter(scores)
        ranker.tokenizer = Mock()
        ranker.tokenizer.encode_batch.return_value = [SimpleNamespace(ids=[0] * count) for count in counts]
        return ranker

    def test_ordering_preserves_provenance_and_does_not_edit_input(self):
        hits = [{'source_title':'Fictional record', 'text':'A condition', 'chunk_id':str(i),
                 'source_id':'record', 'source_url':'https://example.org', 'document_version':'fictional'} for i in range(2)]
        ranked = self.make_ranker([-2, 4], [9, 9]).rank('condition', hits)
        self.assertEqual([r['chunk_id'] for r in ranked], ['1','0'])
        self.assertEqual(ranked[0]['source_url'], hits[1]['source_url'])
        self.assertNotIn('rerank_score', hits[1])

    def test_pair_overflow_fails_before_inference(self):
        ranker = self.make_ranker([1], [513])
        with self.assertRaises(TokenLimitExceeded):
            ranker.rank('question', [{'source_title':'Fictional record','text':'condition','chunk_id':'1'}])
        ranker.model.rerank.assert_not_called()

    def test_model_failure_does_not_silently_use_keyword_order(self):
        ranker = self.make_ranker([], [9])
        ranker.model.rerank.side_effect = RuntimeError('unavailable')
        with self.assertRaisesRegex(RuntimeError,'unavailable'):
            ranker.rank('question', [{'source_title':'Fictional record','text':'condition','chunk_id':'1'}])

    def test_nonfinite_or_missing_scores_rejected(self):
        for scores in ([float('nan')], [float('inf')], []):
            with self.assertRaises(ValueError):
                self.make_ranker(scores,[9]).rank('question', [{'source_title':'Fictional record','text':'condition','chunk_id':'1'}])

    def test_candidate_budget_is_enforced_before_tokenization(self):
        ranker = self.make_ranker([], [])
        with self.assertRaises(ValueError):ranker.rank('question', [{}] * 41)
        ranker.tokenizer.encode_batch.assert_not_called()

    def test_changed_model_artifact_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder,'model').write_bytes(b'changed')
            with patch('reranker.FILES', {'model':'0'*64}):
                with self.assertRaisesRegex(ValueError,'checksum'):verify_files(folder)

    def test_context_is_an_exact_source_span_and_preserves_matched_chunk(self):
        source='Fictional records must retain conditions. '*80
        hit={'source_id':'record','source_title':'Fictional record','chunk_id':'record:700','char_start':700,'text':source[700:1020]}
        ranker=SimpleNamespace(tokenizer=SimpleNamespace(encode=lambda *args:SimpleNamespace(ids=[0]*300)))
        result=contexts({'sources':{'record':{'text':source}}},[hit,hit],'question',ranker)
        self.assertEqual(len(result),1)
        row=result[0]
        self.assertEqual(row['text'],source[row['char_start']:row['context_char_end']])
        self.assertEqual(row['matched_chunk_id'],'record:700')
        self.assertEqual(hit['text'],source[700:1020])

    def test_context_budget_exhaustion_does_not_truncate_query(self):
        hit={'source_id':'record','source_title':'Fictional record','chunk_id':'record:0','char_start':0,'text':'record'}
        ranker=SimpleNamespace(tokenizer=SimpleNamespace(encode=lambda *args:SimpleNamespace(ids=[0]*513)))
        with self.assertRaises(TokenLimitExceeded):contexts({'sources':{'record':{'text':'record '*300}}},[hit],'question',ranker)

    def test_high_model_score_cannot_promote_pending_source(self):
        hit={'source_id':'record','text':'Fictional text','review_status':'pending','keyword_score':0,'rerank_score':10}
        self.assertEqual(evidence_answer('question',[hit],match_gate=lambda h:True)['evidence'],[])

    def test_export_preserves_the_scored_context_and_its_content_hash(self):
        text='Fictional clause\n\n(a) A condition.\n\n(b) An exception.'
        hit={'source_id':'record','text':text,'review_status':'source_verified','keyword_score':0,
            'content_sha256':sha256(text.encode()).hexdigest()}
        evidence=evidence_answer('question',[hit],max_words=512,match_gate=lambda h:True)['evidence'][0]
        self.assertEqual(evidence['text'],text)
        self.assertEqual(sha256(evidence['text'].encode()).hexdigest(),evidence['content_sha256'])


if __name__ == '__main__':unittest.main()
