"""Pinned local cross-encoder for passage ordering, never legal confidence."""
from hashlib import sha256
import math
from pathlib import Path

from pipeline import TokenLimitExceeded

MODEL = 'Xenova/ms-marco-MiniLM-L-6-v2'
REVISION = 'a09144355adeed5f58c8ed011d209bf8ee5a1fec'
FILES = {
    'onnx/model.onnx': 'c623d0bcb99f4622beb413eaef00cfbe5db20df9f1dd982da4b4f26022881870',
    'config.json': 'd827779a72d27ae68cf878a6fc2e954542663fe21ca515d9f4783fc96be2d37e',
    'tokenizer.json': 'd241a60d5e8f04cc1b2b3e9ef7a4921b27bf526d9f6050ab90f9267a1f9e5c66',
    'tokenizer_config.json': '0b29c7bfc889e53b36d9dd3e686dd4300f6525110eaa98c76a5dafceb2029f53',
    'special_tokens_map.json': 'b6d346be366a7d1d48332dbc9fdf3bf8960b5d879522b7799ddba59e76237ee3',
}
MAX_CANDIDATES = 40
MIN_LOGIT = 0.0
MAX_LOGIT_GAP = 2.0
INSTRUMENT_NAMES = {'gdpr':'the General Data Protection Regulation', 'dsa':'the Digital Services Act',
    'dma':'the Digital Markets Act', 'ai-act':'the AI Act', 'all':'EU law'}


def scoped_query(query, instrument):
    return f'Under {INSTRUMENT_NAMES.get(instrument, instrument)}, {query}'


def contexts(index, hits, query, ranker):
    result, seen = [], set()
    for hit in hits:
        source = index.get('sources', {}).get(hit['source_id'])
        if not source or 'char_start' not in hit:
            result.append(hit)
            continue
        text, pivot = source['text'], hit['char_start']
        width = 1600
        while True:
            start = max(0, pivot - min(640, (width-320)//2))
            end = min(len(text), start+width)
            start = max(0, end-width)
            passage = text[start:end]
            count = len(ranker.tokenizer.encode(query, hit['source_title']+'\n'+passage).ids)
            if count <= 512:
                break
            if width == 320:
                raise TokenLimitExceeded('Query and matched passage exceed the reranker token limit')
            width = max(320, width-200)
        key = (hit['source_id'], start, end)
        if key in seen:
            continue
        seen.add(key)
        digest = sha256(passage.encode()).hexdigest()
        result.append({**hit, 'text':passage, 'matched_chunk_id':hit['chunk_id'],
            'chunk_id':f"{hit['source_id']}:context:{start}:{end}:{digest[:12]}",
            'content_sha256':digest, 'char_start':start, 'context_char_end':end})
    return result


def verify_files(directory):
    for name, expected in FILES.items():
        digest = sha256()
        with (Path(directory) / name).open('rb') as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b''):
                digest.update(block)
        if digest.hexdigest() != expected:
            raise ValueError(f'Reranker artifact checksum mismatch: {name}')


class Reranker:
    def __init__(self, cache_dir=None):
        from huggingface_hub import snapshot_download
        from huggingface_hub.errors import LocalEntryNotFoundError
        from fastembed.rerank.cross_encoder import TextCrossEncoder
        from tokenizers import Tokenizer
        options = dict(repo_id=MODEL, revision=REVISION, allow_patterns=list(FILES), cache_dir=cache_dir)
        try:
            directory = snapshot_download(**options, local_files_only=True)
            if not all((Path(directory) / name).is_file() for name in FILES):
                raise LocalEntryNotFoundError('Incomplete reranker cache')
        except LocalEntryNotFoundError:
            directory = snapshot_download(**options, max_workers=1)
        verify_files(directory)
        self.model = TextCrossEncoder(model_name=MODEL, specific_model_path=directory, threads=2)
        tokenizer = self.model.model.tokenizer
        if not tokenizer.truncation or tokenizer.truncation['max_length'] != 512:
            raise ValueError('Unexpected reranker tokenizer limit')
        self.tokenizer = Tokenizer.from_str(tokenizer.to_str())
        self.tokenizer.no_truncation()
        self.tokenizer.no_padding()
        self.manifest = {'method': 'hybrid-cross-encoder', 'model': MODEL, 'revision': REVISION,
            'model_sha256': FILES['onnx/model.onnx'], 'tokenizer_sha256': sha256(self.tokenizer.to_str().encode()).hexdigest(),
            'max_pair_tokens': 512, 'max_candidates': MAX_CANDIDATES, 'score_kind': 'uncalibrated_logit',
            'query_context':'selected-instrument-v1', 'passage_context':'neighbor-window-1600-v1',
            'minimum_logit':MIN_LOGIT, 'max_logit_gap':MAX_LOGIT_GAP}

    def rank(self, query, hits):
        if len(hits) > MAX_CANDIDATES:
            raise ValueError('Reranker candidate budget exceeded')
        if not hits:
            return []
        documents = [hit['source_title'] + '\n' + hit['text'] for hit in hits]
        pairs = [(query, document) for document in documents]
        counts = [len(row.ids) for row in self.tokenizer.encode_batch(pairs)]
        if any(count > 512 for count in counts):
            raise TokenLimitExceeded('Query and passage exceed the 512-token reranker limit')
        scores = list(self.model.rerank(query, documents, batch_size=16))
        if len(scores) != len(hits) or not all(math.isfinite(score) for score in scores):
            raise ValueError('Invalid reranker scores')
        return sorted([{**hit, 'rerank_score': float(score)} for hit, score in zip(hits, scores)],
            key=lambda hit: (-hit['rerank_score'], hit['chunk_id']))
