"""Fictional XHTML contract fixtures; no legal corpus is copied into tests."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from import_official import extract_articles, safe_url, run
from pipeline import prepare
from research import research, select_index, markdown

SPEC = {'id':'test','number':'2099/1234','celex':'32099R1234','name':'Fictional act',
    'publication_date':'2099-01-01','articles':[1]}
BODY = b'''<html xmlns="http://www.w3.org/1999/xhtml"><div class="eli-main-title">Regulation 2099/1234</div>
<div id="art_1"><p>Article 1</p><div><p>Fictional safeguards</p></div><p>Do not remove the original records. Keep the reference and review all conditions before making a decision.</p>
<table><tr><td><p>(a)</p></td><td><p>Keep the date.</p></td></tr></table></div></html>'''


class OfficialTests(unittest.TestCase):
    def test_article_identity_negation_and_table_coverage(self):
        row = extract_articles(BODY,SPEC,'2099-01-02')[0]
        self.assertIn('Do not remove',row['text']);self.assertIn('(a)\n\nKeep the date.',row['text'])
        chunks=prepare([row]);self.assertEqual(chunks[0]['document_version'],'original_oj')
        self.assertEqual(chunks[0]['review_status'],'source_verified')

    def test_wrong_instrument_missing_article_and_lost_text_rejected(self):
        for bad in [BODY.replace(b'2099/1234',b'2099/9999'),BODY.replace(b'art_1',b'art_2'),BODY.replace(b'</table>',b'</table>unparsed restriction'),b'<html>Challenge</html>']:
            with self.assertRaises(ValueError):extract_articles(bad,SPEC,'2099-01-02')

    def test_untrusted_download_hosts_rejected(self):
        for url in ['http://publications.europa.eu/x','https://publications.europa.eu.evil.test/x','https://localhost/x','https://a@publications.europa.eu/x']:
            with self.assertRaises(ValueError):safe_url(url)

    def test_no_arbitrary_source_is_promoted(self):
        row=extract_articles(BODY,SPEC,'2099-01-02')[0];row['document_version']='latest'
        with self.assertRaises(ValueError):prepare([row])

    def test_filter_before_retrieval_and_scope_validation(self):
        index={'chunks':[{'instrument_id':'gdpr'},{'instrument_id':'dsa'}],'vectors':[[1],[2]]}
        self.assertEqual(select_index(index,'gdpr')['vectors'],[[1]])
        with self.assertRaises(ValueError):select_index(index,'unknown')

    def test_current_law_and_language_get_specific_next_step_without_inference(self):
        row=extract_articles(BODY,SPEC,'2099-01-02')[0]
        index={'manifest':{'corpus_sha256':'example'},'chunks':[row],'vectors':[[1]]}
        for query,reason in [('Are we currently compliant?','version_review_required'),('数据如何删除','english_required')]:
            with patch('research.search',side_effect=AssertionError('must not retrieve')):
                result=research(index,query,None)
            self.assertEqual(result['reason'],reason);self.assertEqual(result['evidence'],[])
            self.assertIn('Snapshot: example',markdown(result))

    def test_article_diversity_and_version_survive_export(self):
        a=extract_articles(BODY,SPEC,'2099-01-02')[0]
        hit={**a,'chunk_id':'test:0','keyword_score':2}
        index={'manifest':{'corpus_sha256':'example'},'chunks':[a],'vectors':[[1]]}
        result=research(index,'original records',None,retriever=lambda *args:[hit,hit])
        self.assertEqual(len(result['evidence']),1)
        self.assertIn(SPEC['celex'],markdown(result));self.assertEqual(result['confidence'],'unrated')


if __name__=='__main__':unittest.main()
