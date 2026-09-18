"""Loopback-only evidence service and review UI. Does not call an LLM."""
import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse
from pipeline import Encoder, TokenLimitExceeded
from research import research, coverage, markdown
from jsonschema import Draft202012Validator, ValidationError

def serve(index,encoder,port,database_url=None,reranker=None):
    manifest=index['manifest']
    request_validator=Draft202012Validator(json.loads((Path(__file__).resolve().parents[1]/'schemas/research-input.schema.json').read_text(encoding='utf-8')))
    if (manifest['model_id'],manifest['dimension'],manifest['query_prefix']) != (encoder.model_id,encoder.dimension,encoder.prefix):
        raise ValueError('Index and query model differ; choose the matching language or rebuild')
    connection=None
    if database_url:
        import psycopg
        from pg_store import install,ingest
        connection=psycopg.connect(database_url,autocommit=True)
        install(connection);ingest(connection,index)
        connection.close()
    class Handler(BaseHTTPRequestHandler):
        def reply(self,status,payload):
            data=json.dumps(payload,ensure_ascii=False,allow_nan=False).encode()
            self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8')
            self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)))
            self.end_headers();self.wfile.write(data)
        def do_GET(self):
            if self.headers.get('Host') not in (f'127.0.0.1:{port}',f'localhost:{port}'):
                return self.reply(403,{'error':'Host rejected'})
            if self.path == '/coverage':return self.reply(200,coverage(index))
            if self.path.startswith('/sources/'):
                source_id=self.path.removeprefix('/sources/')
                source=index.get('sources',{}).get(source_id)
                if source is None:return self.reply(404,{'error':'完整原文未保存在这个索引中，请打开官方链接或重建索引。'})
                return self.reply(200,source)
            if self.path=='/health':
                if database_url:
                    try:
                        with psycopg.connect(database_url) as active:active.execute('SELECT 1')
                    except Exception:return self.reply(503,{'status':'unavailable'})
                return self.reply(200,{'status':'ready','model':encoder.model_id,'chunks':len(index['chunks']),
                    'storage':'postgres-pgvector' if database_url else 'local-json',
                    'sources':len({c['source_id'] for c in index['chunks']}),
                    'ranking':reranker.manifest if reranker else {'method':'hybrid'}})
            assets={'/':('workbench.html','text/html'),'/workbench.js':('workbench.js','text/javascript')}
            if self.path not in assets:return self.reply(404,{'error':'Not found'})
            filename,mime=assets[self.path];data=(Path(__file__).parent/filename).read_bytes()
            self.send_response(200);self.send_header('Content-Type',mime+'; charset=utf-8')
            self.send_header('Content-Security-Policy',"default-src 'none'; script-src 'self'; style-src 'unsafe-inline'; font-src data:; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
            self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(data)
        def do_POST(self):
            origin=self.headers.get('Origin')
            if origin and origin not in (f'http://127.0.0.1:{port}',f'http://localhost:{port}'):
                return self.reply(403,{'error':'Origin rejected'})
            if self.headers.get('Host') not in (f'127.0.0.1:{port}',f'localhost:{port}'):
                return self.reply(403,{'error':'Host rejected'})
            if self.path!='/search':return self.reply(404,{'error':'Not found'})
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=8192:raise ValueError('Request too large or empty')
                data=json.loads(self.rfile.read(size))
                request_validator.validate(data)
                query=data.get('query')
                if not isinstance(query,str):raise ValueError('Query required')
                retriever=None
                if database_url:
                    from pg_store import retrieve
                    def retriever(q,instrument):
                        with psycopg.connect(database_url) as active:
                            return retrieve(active,index['manifest']['corpus_sha256'],q,encoder,40 if reranker else 12,instrument)
                result=research(index,query,encoder,data.get('instrument','all'),retriever,reranker)
                result['storage']='postgres-pgvector' if database_url else 'local-json'
                result['markdown']=markdown(result)
                self.reply(200,result)
            except TokenLimitExceeded:self.reply(400,{'error':'问题超过模型长度限制，请缩短后重试。','code':'QUERY_TOO_LONG'})
            except (ValueError,TypeError,ValidationError):self.reply(400,{'error':'请检查问题和资料范围，问题需为 1 到 1000 字。'})
            except Exception:self.reply(503,{'error':'检索暂不可用，请保留问题后重试。'})
        def log_message(self,*args):pass  # Never log query text.
    print(f'Knowledge workbench http://127.0.0.1:{port}',flush=True)
    HTTPServer(('127.0.0.1',port),Handler).serve_forever()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--index',type=Path,required=True)
    p.add_argument('--language',choices=['zh','en'],default='en');p.add_argument('--port',type=int,default=8782)
    p.add_argument('--cache-dir',type=Path)
    p.add_argument('--ranking',choices=['hybrid','rerank'],default='hybrid');a=p.parse_args()
    from reranker import Reranker
    cache=str(a.cache_dir) if a.cache_dir else None
    ranker=Reranker(cache) if a.ranking=='rerank' else None
    serve(json.loads(a.index.read_text(encoding='utf-8')),Encoder(a.language,cache),a.port,os.getenv('KB_DATABASE_URL'),ranker)
