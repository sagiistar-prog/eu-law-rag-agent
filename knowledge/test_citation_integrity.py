from hashlib import sha256
from types import SimpleNamespace
import unittest
from pipeline import prepare, clean, evidence_answer
from research import verify_spans
from reranker import contexts


class CitationTests(unittest.TestCase):
    def test_character_chunk_boundary_whitespace_has_exact_source_position(self):
        text='x'*280+'\n\n  exception remains. '+ 'y'*400
        doc={'source_id':'fictional','source_title':'Fixture','source_url':'https://example.org',
             'retrieved_at':'2026-09-18','text':text}
        chunks=prepare([doc]);source=clean(text)
        self.assertEqual(chunks[1]['char_start'],284)
        for chunk in chunks:
            start=chunk['char_start']
            self.assertEqual(source[start:start+len(chunk['text'])],chunk['text'])

    def test_legacy_trim_offset_is_repaired_only_for_exact_original_window(self):
        source='x'*280+'\n\n  exception remains. '+'y'*400
        text=source[280:600].strip()
        hit={'source_id':'s','char_start':280,'text':text,'chunk_id':'s:280',
             'content_sha256':sha256(text.encode()).hexdigest()}
        index={'manifest':{'chunker':'characters-320-overlap-40-v1'},'sources':{'s':{'text':source}}}
        result=verify_spans(index,[hit])[0]
        self.assertEqual(result['char_start'],284)
        self.assertEqual(hit['char_start'],280)
        index['manifest']['chunker']='characters-320-overlap-40-v2'
        with self.assertRaises(ValueError):verify_spans(index,[hit])
        index['manifest']['chunker']='characters-320-overlap-40-v1'
        with self.assertRaises(ValueError):verify_spans(index,[{**hit,'text':'invented'}])
        with self.assertRaises(ValueError):verify_spans(index,[{**hit,'content_sha256':'0'*64}])

    def test_truncated_excerpt_is_exact_prefix_with_its_own_hash_and_provenance(self):
        text='Condition\n\n(a) Applies only if\n\n(b) Exception remains.'
        hit={'source_id':'s','chunk_id':'s:context:10','char_start':10,'context_char_end':10+len(text),
             'text':text,'content_sha256':sha256(text.encode()).hexdigest(),
             'review_status':'fictional','keyword_score':1}
        row=evidence_answer('Condition',[hit],max_words=3)['evidence'][0]
        self.assertEqual(row['text'],'Condition\n\n(a) Applies')
        self.assertEqual(row['content_sha256'],sha256(row['text'].encode()).hexdigest())
        self.assertEqual(row['char_end'],10+len(row['text']))
        self.assertEqual(row['excerpt_of']['content_sha256'],hit['content_sha256'])
        self.assertEqual(row['excerpt_of']['chunk_id'],hit['chunk_id'])
        self.assertNotIn('context_char_end',row)
        self.assertTrue(row['truncated'])
        self.assertNotEqual(row['chunk_id'],hit['chunk_id'])

    def test_long_matched_chunk_remains_inside_context_and_invalid_spans_fail(self):
        source='prefix '*150+'condition '*120+'suffix '*200
        start=1050;text=source[start:start+1200]
        hit={'source_id':'s','source_title':'Fixture','chunk_id':'s:1050','char_start':start,'text':text}
        ranker=SimpleNamespace(tokenizer=SimpleNamespace(encode=lambda *args:SimpleNamespace(ids=[0]*300)))
        index={'sources':{'s':{'text':source}}}
        row=contexts(index,[hit],'query',ranker)[0]
        self.assertLessEqual(row['char_start'],start)
        self.assertGreaterEqual(row['char_end'],start+len(text))
        self.assertEqual(source[row['char_start']:row['char_end']],row['text'])
        for bad in ({**hit,'char_start':-1},{**hit,'text':source[start:start+1601]}):
            with self.assertRaises(ValueError):contexts(index,[bad],'query',ranker)


if __name__=='__main__':unittest.main()
