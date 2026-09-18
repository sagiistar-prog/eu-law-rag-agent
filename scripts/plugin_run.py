#!/usr/bin/env python3
"""Versioned JSON interface with local BGE hybrid retrieval or explicit keyword baseline."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
MAX_BYTES = 1_000_000

def execute(data: dict) -> dict:
    if data.get('retrieval_mode', 'hybrid') == 'hybrid':
        sys.path.insert(0, str(ROOT / 'knowledge'))
        from pipeline import Encoder, build, search, evidence_answer
        encoder = Encoder('en', str(ROOT / '.cache/models'))
        documents = [{**d, 'review_status': d.get('review_status', 'pending')} for d in data['documents']]
        result = evidence_answer(data['query'], search(build(documents, encoder), data['query'], encoder), data.get('max_words_per_source',80))
        evidence = result['evidence']
        markdown = '# Evidence review\n\n' + ('\n\n'.join(f"### {h['source_title']}\n\n{h['text']}\n\nSource: {h['source_id']} / {h['chunk_id']}\n\n{h['source_url']}" for h in evidence) if evidence else 'Insufficient reviewed evidence. Add relevant sources or clarify the question.')
        markdown += '\n\nManual legal review required. Similarity is not a legal conclusion.'
        return {'markdown':markdown,'answer_status':'answered' if evidence else 'refused',
            'sources':[{k:h[k] for k in ('source_id','source_title','source_url','retrieved_at','chunk_id')} for h in evidence],
            'confidence':'unrated' if evidence else 'none','manual_review_required':True,'not_legal_advice':True}
    from build_index import build_index
    from query_rag import retrieve, format_answer, format_refusal, confidence_label
    chunks = [{**source, "chunk_id": f"{source['source_id']}::demo"} for source in data["documents"]]
    ids = [chunk["source_id"] for chunk in chunks]
    if len(set(ids)) != len(ids): raise ValueError("Each document needs a unique source_id")
    results = retrieve(data["query"], build_index(chunks)["chunks"])
    sources = [{key: chunk[key] for key in ("source_id", "source_title", "source_url", "retrieved_at", "chunk_id")} for _, chunk in results]
    return {"markdown": format_answer(data["query"], results, data.get("max_words_per_source", 80)) if results else format_refusal(data["query"]), "answer_status": "answered" if results else "refused", "sources": sources, "confidence": confidence_label(results), "manual_review_required": True, "not_legal_advice": True}


def run(data: dict) -> dict:
    from jsonschema import Draft202012Validator
    schema = json.loads((ROOT / "schemas/input.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(data)
    hybrid = data.get('retrieval_mode', 'hybrid') == 'hybrid'
    result = {"schema_version": "1.0", "status": "ok", "mode": 'local_bge_hybrid' if hybrid else 'offline_keyword_retrieval', "result": execute(data), "warnings": [('本地BGE向量与BM25混合检索，回答为原文摘录，非LLM生成。' if hybrid else '显式关键词基线，没有调用向量模型。'), '来源由调用者提供，未核验网址、法律时效或现实适用性。']}
    Draft202012Validator(json.loads((ROOT / "schemas/output.schema.json").read_text(encoding="utf-8"))).validate(result)
    return result

def main() -> int:
    parser = argparse.ArgumentParser(description='用短来源文本演示可追溯检索与无依据拒答')
    parser.add_argument("--input", type=Path, help="UTF-8 JSON file. Omit to read stdin.")
    parser.add_argument("--output-dir", type=Path, help="New directory inside output/. Existing directories are never overwritten.")
    args = parser.parse_args()
    try:
        if args.input and args.input.stat().st_size > MAX_BYTES: raise ValueError("Input exceeds 1 MB")
        raw = args.input.read_text(encoding="utf-8-sig") if args.input else sys.stdin.buffer.read(MAX_BYTES + 1).decode("utf-8-sig")
        if len(raw.encode("utf-8")) > MAX_BYTES: raise ValueError("Input exceeds 1 MB")
        data = json.loads(raw, parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Non-finite JSON number")))
        payload = run(data)
        if args.output_dir:
            destination = args.output_dir.resolve()
            allowed = (ROOT / "output").resolve()
            if not destination.is_relative_to(allowed) or destination == allowed:
                raise ValueError("Choose a new subdirectory inside output/")
            destination.mkdir(parents=True, exist_ok=False)
            (destination / "result.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            (destination / "result.md").write_text(payload["result"]["markdown"], encoding="utf-8")
            if "csv" in payload["result"]: (destination / "timeline.csv").write_text(payload["result"]["csv"], encoding="utf-8")
        code = 0
    except ImportError:
        payload = {"schema_version":"1.0", "status":"error", "error":{"code":"DEPENDENCY_MISSING", "message":"Install requirements-plugin.txt and, for hybrid mode, knowledge/requirements.txt in the same Python environment."}}
        code = 2
    except Exception as exc:
        # Do not echo user text, stack traces or local file paths into the response.
        if type(exc).__name__ == "ValidationError":
            location = ".".join(str(part) for part in exc.absolute_path) or "input"
            message = f"Invalid field: {location}; failed {exc.validator} constraint. See schemas/input.schema.json."
        elif isinstance(exc, (FileExistsError, FileNotFoundError, PermissionError, OSError)):
            message = "Cannot read input or create a fresh output directory. Existing output is preserved."
        elif isinstance(exc, json.JSONDecodeError): message = "Input must be valid UTF-8 JSON."
        else: message = str(exc) if isinstance(exc, ValueError) else "Generation failed; check the documented input contract."
        payload = {"schema_version":"1.0", "status":"error", "error":{"code":"INVALID_INPUT_OR_OUTPUT", "message":message}}
        code = 2
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, allow_nan=False))
    return code

if __name__ == "__main__":
    raise SystemExit(main())
