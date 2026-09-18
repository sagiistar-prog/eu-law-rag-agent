"""Small, inspectable RAG pipeline. Embeddings are real ONNX model inference."""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import importlib.metadata
import json
import math
from pathlib import Path
import re
import unicodedata
from chunking import character_spans, paragraph_spans, retrieval_text

MODELS = {
    'zh': ('BAAI/bge-small-zh-v1.5', 512, '为这个句子生成表示以用于检索相关文章：'),
    'en': ('BAAI/bge-small-en-v1.5', 384, 'Represent this sentence for searching relevant passages: '),
}
REQUIRED = ('source_id', 'source_title', 'source_url', 'retrieved_at', 'text')
STOP = set('the a an is are of to for and in what does do this that with be on i we you it its they their them he she our your from at by or as into out over under can could should would must may might shall which who whose whom when where why how has have had been being was were will if then than also any all such some these those not no only about through within without before after between each other more most further according relevant required needed following include includes including provided provide requirements original text says say'.split())

def clean(text):
    """Preserve numbers, negation, paragraphs, tables, and meaningful indentation."""
    text = unicodedata.normalize('NFC', text).replace('\r\n', '\n').replace('\r', '\n')
    text = ''.join(c for c in text if c in '\n\t' or unicodedata.category(c) != 'Cc')
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(line.rstrip() for line in text.split('\n'))).strip()

def prepare(documents,chunker='characters'):
    if chunker not in ('characters','paragraphs'): raise ValueError('Unknown chunker')
    chunks, seen, ids = [], set(), set()
    for doc in documents:
        if any(not isinstance(doc.get(k), str) or not doc[k].strip() for k in REQUIRED):
            raise ValueError('Every source needs nonempty id, title, URL, retrieval date and text')
        if doc['source_id'] in ids: raise ValueError('Duplicate source_id')
        if not re.fullmatch(r'[a-zA-Z0-9_-]{1,100}', doc['source_id']): raise ValueError('Invalid source_id')
        if not re.match(r'^(https?://|urn:local:sha256:)', doc['source_url']): raise ValueError('Invalid source locator')
        datetime.fromisoformat(doc['retrieved_at'])
        if doc.get('review_status', 'pending') not in ('pending','reviewed','fictional','source_verified'): raise ValueError('Invalid review_status')
        if doc.get('review_status') == 'source_verified' and (doc.get('source_kind') != 'official_legal_text' or doc.get('document_version') != 'original_oj' or not doc.get('celex')):
            raise ValueError('Source verification requires explicit official publication provenance')
        ids.add(doc['source_id'])
        text = clean(doc['text'])
        # A short character bound is conservative for the 512-token BGE encoders.
        spans = paragraph_spans(text) if chunker=='paragraphs' else character_spans(text)
        for offset,fragment in spans:
            if not fragment: continue
            digest = sha256(fragment.encode()).hexdigest()
            # Preserve duplicate text from different sources for attribution.
            key = (doc['source_id'], digest)
            if key in seen and doc.get('source_kind') != 'private_book': continue
            seen.add(key)
            chunks.append({**{k:doc[k] for k in REQUIRED if k != 'text'},
                'schema_version': 1, 'chunk_id': f"{doc['source_id']}:{offset}:{digest[:12]}",
                'text': fragment, 'content_sha256': digest, 'char_start': offset,
                'section': doc.get('section', ''), 'page': doc.get('page'),
                'review_status': doc.get('review_status', 'pending'),
                'language': doc.get('language', 'unknown'),
                'jurisdiction':doc.get('jurisdiction',''),
                'source_kind':doc.get('source_kind','document'),
                'source_sha256':doc.get('source_sha256',''),
                **{key:doc[key] for key in ('instrument_id','celex','publication_date','document_version','version_notice') if key in doc}})
    return chunks

def tokens(text):
    words = [w for w in re.findall(r'[a-z0-9]+', text.lower()) if w not in STOP]
    for run in re.findall(r'[\u4e00-\u9fff]+', text):
        words.extend(run[i:i+2] for i in range(max(1, len(run)-1)))
    return words

def bm25(query, chunks,context='none'):
    terms = set(tokens(query)); counts = [Counter(tokens(retrieval_text(c,context))) for c in chunks]
    lengths = [sum(c.values()) for c in counts]; avg = sum(lengths)/max(1,len(lengths))
    scores = []
    for i, count in enumerate(counts):
        score = 0.0
        for term in terms:
            tf = count[term]
            if not tf: continue
            df = sum(term in c for c in counts)
            idf = math.log(1+(len(counts)-df+.5)/(df+.5))
            score += idf * tf * 2.5 / (tf + 1.5 * (.25+.75*lengths[i]/max(avg,1)))
        if score > 0: scores.append((i,score))
    return sorted(scores,key=lambda x:(-x[1],x[0]))

def fuse(*rankings, k=60):
    scores = {}
    for ranking in rankings:
        for rank,(i,_) in enumerate(ranking,1): scores[i] = scores.get(i,0) + 1/(k+rank)
    return sorted(scores.items(),key=lambda x:(-x[1],x[0]))

class TokenLimitExceeded(ValueError):
    """The full input cannot be encoded without losing content."""


class Encoder:
    def __init__(self, language, cache_dir=None):
        from fastembed import TextEmbedding
        self.model_id,self.dimension,self.prefix = MODELS[language]
        self.model = TextEmbedding(model_name=self.model_id,cache_dir=cache_dir,threads=2)
        from tokenizers import Tokenizer
        tokenizer = getattr(self.model.model, 'tokenizer', None)
        if tokenizer is None or not tokenizer.truncation:
            raise ValueError('Pinned FastEmbed tokenizer contract unavailable')
        self.max_tokens = min(512, tokenizer.truncation['max_length'])
        self.tokenizer = Tokenizer.from_str(tokenizer.to_str())
        self.tokenizer.no_truncation()
        self.tokenizer.no_padding()
        self.tokenizer_sha256 = sha256(self.tokenizer.to_str().encode()).hexdigest()

    def token_counts(self, texts, query=False):
        prepared = [self.prefix+t if query else t for t in texts]
        counts = [len(row.ids) for row in self.tokenizer.encode_batch(prepared)]
        if any(count > self.max_tokens for count in counts):
            raise TokenLimitExceeded(f'Input exceeds the {self.max_tokens}-token model limit; shorten the query or split the source')
        return counts


    def encode(self,texts,query=False):
        self.token_counts(texts,query=query)
        prepared = [self.prefix+t if query else t for t in texts]
        result=[]
        for raw in self.model.embed(prepared):
            v=[float(x) for x in raw]
            if len(v)!=self.dimension or not all(math.isfinite(x) for x in v):
                raise ValueError('Invalid embedding returned by model')
            norm=math.sqrt(sum(x*x for x in v))
            if norm == 0: raise ValueError('Zero embedding')
            result.append([x/norm for x in v])
        return result

def build(documents,encoder,chunker='characters',context='none'):
    chunks=prepare(documents,chunker)
    if not chunks: raise ValueError('No chunks to index')
    from jsonschema import Draft202012Validator
    validator=Draft202012Validator(json.loads(Path(__file__).with_name('chunk.schema.json').read_text(encoding='utf-8')))
    for chunk in chunks:validator.validate(chunk)
    texts=[retrieval_text(c,context) for c in chunks]
    descriptor='paragraphs-1200-overlap-160-v1' if chunker=='paragraphs' else 'characters-320-overlap-40-v2'
    payload=chunks if chunker=='characters' and context=='none' else {'chunker':descriptor,'document_context':context,'chunks':chunks}
    return {'manifest': {'schema_version':1,'model_id':encoder.model_id,
        'document_context':context,
        'dimension':encoder.dimension,'query_prefix':encoder.prefix,'normalized':True,
        'chunker':descriptor,'fastembed_version':importlib.metadata.version('fastembed'),
        'created_at':datetime.now(timezone.utc).isoformat(),
        'tokenizer_sha256':encoder.tokenizer_sha256,'max_tokens':encoder.max_tokens,
        'corpus_sha256':sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False).encode()).hexdigest()},
        'chunks':chunks,'vectors':encoder.encode(texts),
        'sources':{d['source_id']:{**d,'text':clean(d['text'])} for d in documents}}

def search(index,query,encoder,top_k=5,mode='hybrid'):
    if not query.strip() or len(query)>1000: raise ValueError('Query must contain 1 to 1000 characters')
    m=index['manifest']
    if (m['model_id'],m['dimension'],m['query_prefix']) != (encoder.model_id,encoder.dimension,encoder.prefix):
        raise ValueError('Index and query model differ. Rebuild the index.')
    chunks=index['chunks']; vectors=index['vectors']
    if len(chunks)!=len(vectors): raise ValueError('Incomplete vector index')
    if any(len(v)!=encoder.dimension or not all(math.isfinite(x) for x in v) for v in vectors):
        raise ValueError('Corrupt vector index')
    keyword=bm25(query,chunks,m.get('document_context','none'))
    if mode=='keyword':
        return [{**chunks[i], 'rrf_score':None,'keyword_score':score,
            'cosine_similarity':None,'retrieval_method':mode,'requires_review':True} for i,score in keyword[:top_k]]
    q=encoder.encode([query],query=True)[0]
    dense=sorted([(i,sum(a*b for a,b in zip(q,v))) for i,v in enumerate(vectors)],key=lambda x:-x[1])
    candidates=fuse(keyword[:20],dense[:20]) if mode=='hybrid' else keyword if mode=='keyword' else dense
    lexical=dict(keyword); semantic=dict(dense)
    # Scores are ranking signals, never a probability that a claim is true.
    return [{**chunks[i], 'rrf_score':score if mode=='hybrid' else None,
        'keyword_score':lexical.get(i,0),'cosine_similarity':semantic[i],
        'retrieval_method':mode,'requires_review':True} for i,score in candidates[:top_k]]

def evidence_answer(query,hits,max_words=80,match_gate=None):
    if not isinstance(max_words, int) or isinstance(max_words, bool) or max_words < 1:
        raise ValueError('Quote budget must be a positive integer')
    # A nearest vector always exists. Do not convert that fact into an answer.
    def supported_hit(hit):
        if hit['review_status'] not in ('reviewed','fictional','source_verified'):
            return False
        if match_gate is not None:return match_gate(hit)
        if hit['keyword_score'] <= 0:return False
        if hit['review_status'] != 'source_verified':return True
        terms=set(tokens(query));overlap=terms & set(tokens(hit['text']))
        # Public-source excerpts need two distinct content terms for a longer query.
        # This is an inspectable heuristic, not legal entailment or calibrated confidence.
        required=2 if len(terms)>=3 else 1
        cosine=hit.get('cosine_similarity')
        return len(overlap)>=required and (cosine is None or cosine>=.6)
    supported=[h for h in hits if supported_hit(h)]
    used={}; evidence=[]
    for h in supported:
        remaining=max_words-used.get(h['source_id'],0)
        if remaining<=0: continue
        words=list(re.finditer(r'\S+',h['text']))
        excerpt=h['text'] if len(words)<=remaining else h['text'][:words[remaining-1].end()]
        used[h['source_id']]=used.get(h['source_id'],0)+min(len(words),remaining)
        quoted={**h,'text':excerpt,'truncated':len(words)>remaining,
            'content_sha256':sha256(excerpt.encode()).hexdigest()}
        if 'char_start' in h:
            quoted['char_end']=h['char_start']+len(excerpt)
        if quoted['truncated']:
            quoted['excerpt_of']={k:h[k] for k in ('chunk_id','char_start','context_char_end','matched_chunk_id') if k in h}
            quoted['excerpt_of']['content_sha256']=sha256(h['text'].encode()).hexdigest()
            if 'char_start' in h:
                quoted['excerpt_of']['char_end']=h['char_start']+len(h['text'])
                quoted['chunk_id']=f"{h['source_id']}:excerpt:{h['char_start']}:{quoted['char_end']}:{quoted['content_sha256'][:12]}"
            quoted.pop('context_char_end',None)
        evidence.append(quoted)
    return {'query':query,'answer_status':'evidence_found' if evidence else 'insufficient_evidence',
        'answer_mode':'extractive','evidence':evidence,'candidates':hits,
        'manual_review_required':True,'confidence':'unrated',
        'next_step':'核对原文及适用条件。' if evidence else '请补充相关资料或更具体的问题。'}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('command',choices=['build','search','evaluate'])
    p.add_argument('--documents',type=Path);p.add_argument('--index',type=Path,required=True)
    p.add_argument('--language',choices=MODELS,default='en');p.add_argument('--query')
    p.add_argument('--chunker',choices=['characters','paragraphs'],default='characters')
    p.add_argument('--document-context',choices=['none','source-section'],default='none')
    p.add_argument('--cases',type=Path);p.add_argument('--cache-dir',type=Path)
    a=p.parse_args();encoder=Encoder(a.language,str(a.cache_dir) if a.cache_dir else None)
    if a.command=='build':
        docs=[json.loads(line) for line in a.documents.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
        index=build(docs,encoder,a.chunker,a.document_context);a.index.parent.mkdir(parents=True,exist_ok=True)
        with a.index.open('x',encoding='utf-8') as f:json.dump(index,f,ensure_ascii=False,allow_nan=False)
        with a.index.with_suffix('.chunks.jsonl').open('w',encoding='utf-8') as f:
            for c in index['chunks']:f.write(json.dumps(c,ensure_ascii=False)+'\n')
        print(json.dumps(index['manifest'],ensure_ascii=False));return
    index=json.loads(a.index.read_text(encoding='utf-8'))
    if a.command=='search':
        print(json.dumps(evidence_answer(a.query,search(index,a.query,encoder)),ensure_ascii=False));return
    cases=json.loads(a.cases.read_text(encoding='utf-8'));results={}
    for mode in ('keyword','dense','hybrid'):
        rows=[]
        for case in cases:
            hits=search(index,case['query'],encoder,3,mode)
            ranks=[i+1 for i,h in enumerate(hits) if h['source_id'] in case['relevant_sources']]
            found={h['source_id'] for h in hits}&set(case['relevant_sources'])
            rows.append({'query':case['query'],'recall_at_3':len(found)/len(case['relevant_sources']),
                'reciprocal_rank':1/min(ranks) if ranks else 0})
        results[mode]={'recall_at_3':sum(r['recall_at_3'] for r in rows)/len(rows),
            'mrr_at_3':sum(r['reciprocal_rank'] for r in rows)/len(rows),'cases':rows}
    print(json.dumps({'scope':'small fictional retrieval smoke set, not a quality benchmark','model':encoder.model_id,'results':results},ensure_ascii=False,indent=2))

if __name__=='__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    main()
