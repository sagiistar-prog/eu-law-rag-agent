"""Loopback-only evidence service and review UI. Does not call an LLM."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse
from pipeline import Encoder, search, evidence_answer

def serve(index,encoder,port):
    class Handler(BaseHTTPRequestHandler):
        def reply(self,status,payload):
            data=json.dumps(payload,ensure_ascii=False,allow_nan=False).encode()
            self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8')
            self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)))
            self.end_headers();self.wfile.write(data)
        def do_GET(self):
            if self.path=='/health':return self.reply(200,{'status':'ready','model':encoder.model_id,'chunks':len(index['chunks'])})
            if self.path!='/':return self.reply(404,{'error':'Not found'})
            data=(Path(__file__).parent/'workbench.html').read_bytes()
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(data)
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
                data=json.loads(self.rfile.read(size));query=data.get('query')
                if not isinstance(query,str):raise ValueError('Query required')
                result=evidence_answer(query,search(index,query,encoder))
                self.reply(200,result)
            except (ValueError,TypeError):self.reply(400,{'error':'请输入 1 到 1000 字的问题。'})
            except Exception:self.reply(503,{'error':'检索暂不可用，请保留问题后重试。'})
        def log_message(self,*args):pass  # Never log query text.
    print(f'Knowledge workbench http://127.0.0.1:{port}',flush=True)
    HTTPServer(('127.0.0.1',port),Handler).serve_forever()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--index',type=Path,required=True)
    p.add_argument('--language',choices=['zh','en'],default='zh');p.add_argument('--port',type=int,default=8782)
    p.add_argument('--cache-dir',type=Path);a=p.parse_args()
    serve(json.loads(a.index.read_text(encoding='utf-8')),Encoder(a.language,str(a.cache_dir) if a.cache_dir else None),a.port)
