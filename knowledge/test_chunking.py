from hashlib import sha256
import unittest
from unittest.mock import patch
from chunking import paragraph_spans, retrieval_text
from pipeline import prepare, build, bm25, evidence_answer


class ChunkingTests(unittest.TestCase):
    def doc(self, text):
        return {'source_id':'fictional','source_title':'Fictional retention rules',
            'source_url':'https://example.org/fictional','retrieved_at':'2026-09-18',
            'text':text,'section':'Article 1','review_status':'fictional'}

    def test_exact_spans_cover_all_nonwhitespace_without_splitting_short_paragraphs(self):
        text='First fictional condition.\n\n' + ('Do not discard the exception; retain 0.25 records. '*70) + '\n\nFinal condition.'
        spans=list(paragraph_spans(text))
        covered=set()
        for start, fragment in spans:
            self.assertEqual(fragment,text[start:start+len(fragment)])
            self.assertLessEqual(len(fragment),1200)
            covered.update(range(start,start+len(fragment)))
        self.assertTrue(all(i in covered for i,c in enumerate(text) if not c.isspace()))
        self.assertEqual(len(spans),len({start for start,_ in spans}))
        self.assertEqual(list(paragraph_spans('One.\n\nTwo.')),[(0,'One.\n\nTwo.')])

    def test_long_unbroken_text_terminates_with_bounded_exact_spans(self):
        text='x'*5001
        spans=list(paragraph_spans(text))
        self.assertLess(len(spans),10)
        self.assertEqual(spans[-1][0]+len(spans[-1][1]),len(text))
        self.assertTrue(all(len(s)<=1200 for _,s in spans))
        with self.assertRaises(ValueError): list(paragraph_spans(text,size=10,overlap=10))

    def test_paragraph_preparation_retains_exact_citation_positions_and_hashes(self):
        doc=self.doc('  A fictional paragraph.\n\n' + 'Nested condition and exception. '*100)
        chunks=prepare([doc],'paragraphs')
        source=doc['text'].strip()
        for c in chunks:
            self.assertEqual(c['text'],source[c['char_start']:c['char_start']+len(c['text'])])
            self.assertEqual(c['content_sha256'],sha256(c['text'].encode()).hexdigest())
        self.assertTrue(all(len(c['text'])<=320 for c in prepare([doc])))

    def test_context_search_does_not_rewrite_the_source_or_promote_title_only_matches(self):
        chunk={**self.doc('Unrelated fictional narrative.'),'review_status':'source_verified','keyword_score':1,'cosine_similarity':.9}
        self.assertGreater(bm25('retention',[chunk],'source-section')[0][1],0)
        self.assertEqual(evidence_answer('retention',[chunk])['evidence'],[])
        self.assertEqual(chunk['text'],'Unrelated fictional narrative.')
        with self.assertRaises(ValueError): retrieval_text(chunk,'unknown')

    def test_index_variants_have_separate_hashes_and_encode_metadata_only_when_selected(self):
        class Encoder:
            model_id='fixture';dimension=2;prefix='';max_tokens=512;tokenizer_sha256='fixture'
            def encode(self,texts):
                self.inputs=texts
                return [[1.,0.] for _ in texts]
        encoder=Encoder();docs=[self.doc('Fictional condition. '*90)]
        with patch('pipeline.importlib.metadata.version',return_value='fixture'):
            plain=build(docs,encoder)
            context=build(docs,encoder,context='source-section')
            paragraphs=build(docs,encoder,chunker='paragraphs',context='source-section')
        self.assertEqual(len({i['manifest']['corpus_sha256'] for i in (plain,context,paragraphs)}),3)
        self.assertEqual(plain['sources'],paragraphs['sources'])
        self.assertIn('Fictional retention rules',encoder.inputs[0])
        self.assertNotIn('Fictional retention rules',paragraphs['chunks'][0]['text'])


if __name__=='__main__':unittest.main()
