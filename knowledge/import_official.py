"""Import selected original OJ articles through the official Cellar REST interface.

No corpus is vendored. HTML and vectors stay in ignored output/. Article-level
character coverage is checked before an original-version snapshot is accepted.
"""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import urllib.request
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 8_000_000
NOTICE = 'Original Official Journal text; amendments, corrigenda and current applicability have not been checked.'


def safe_url(url):
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or parsed.hostname not in ('publications.europa.eu', 'eur-lex.europa.eu') or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError('Only the official HTTPS publication hosts are allowed')
    return url


class OfficialRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Cellar publishes an HTTP canonical Location; request its HTTPS form only.
        if newurl.startswith('http://publications.europa.eu/'):
            newurl = 'https://' + newurl[len('http://'):]
        return super().redirect_request(req, fp, code, msg, headers, safe_url(newurl))


def download(celex):
    if not re.fullmatch(r'3\d{4}R\d{4}', celex):
        raise ValueError('Only original regulation CELEX identifiers are supported')
    url = f'https://publications.europa.eu/resource/celex/{celex}'
    request = urllib.request.Request(url, headers={'Accept': 'application/xhtml+xml', 'Accept-Language': 'en', 'User-Agent': 'EU-Law-Evidence-Lab/0.3 (public-source-research)'})
    with urllib.request.build_opener(OfficialRedirect()).open(request, timeout=45) as response:
        if response.status != 200:
            raise ValueError('Publication download was not a successful document response')
        safe_url(response.url)
        body = response.read(LIMIT + 1)
        if not body or len(body) > LIMIT:
            raise ValueError('Publication empty or above download limit')
        return body, response.url


def normalized(text):
    return ' '.join(text.split())


def extract_articles(body, spec, retrieved_at):
    if b'<!ENTITY' in body.upper():
        raise ValueError('XML entities are not accepted')
    root = ET.fromstring(body)
    if root.tag.rsplit('}', 1)[-1] != 'html':
        raise ValueError('Expected official XHTML, not an error page')
    titles = [node for node in root.iter() if 'eli-main-title' in node.get('class', '').split()]
    if not titles or spec['number'] not in normalized(' '.join(titles[0].itertext())):
        raise ValueError('Publication identity does not match the catalog')
    elements = {}
    for node in root.iter():
        identifier = node.get('id')
        if identifier and identifier.startswith('art_'):
            if identifier in elements:
                raise ValueError('Duplicate article identifier')
            elements[identifier] = node
    documents = []
    for number in spec['articles']:
        article = elements.get(f'art_{number}')
        if article is None:
            raise ValueError(f'Missing requested article {number}')
        paragraphs = [normalized(''.join(node.itertext())) for node in article.iter() if node.tag.rsplit('}', 1)[-1] == 'p']
        if not paragraphs or paragraphs[0] != f'Article {number}':
            raise ValueError('Article heading mismatch')
        text = '\n\n'.join(line for line in paragraphs if line)
        compact = lambda value: ''.join(value.split())
        if compact(text) != compact(''.join(article.itertext())):
            raise ValueError('Article extraction lost text outside paragraph blocks')
        if len(text) < 80:
            raise ValueError('Article unexpectedly short')
        documents.append({
            'source_id': f"{spec['id']}-oj-art-{number}",
            'source_title': f"{spec['name']} — Article {number}: {paragraphs[1]}",
            'source_url': f"https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:{spec['celex']}#art_{number}",
            'retrieved_at': retrieved_at, 'text': text, 'review_status': 'source_verified',
            'section': f'Article {number}', 'language': 'en', 'jurisdiction': 'EU',
            'source_kind': 'official_legal_text', 'source_sha256': sha256(body).hexdigest(),
            'instrument_id': spec['id'], 'celex': spec['celex'],
            'publication_date': spec['publication_date'], 'document_version': 'original_oj',
            'version_notice': NOTICE,
        })
    return documents


def run(destination, catalog):
    destination = destination.resolve()
    allowed = (ROOT / 'output').resolve()
    if destination == allowed or not destination.is_relative_to(allowed):
        raise ValueError('Choose a new snapshot directory inside output/')
    specs = catalog['instruments']
    if len({s['id'] for s in specs}) != len(specs) or any(len(set(s['articles'])) != len(s['articles']) for s in specs):
        raise ValueError('Duplicate instrument or article')
    destination.mkdir(parents=True, exist_ok=False)
    retrieved_at = datetime.now(timezone.utc).isoformat()
    rows, coverage = [], []
    for spec in specs:
        body, resolved = download(spec['celex'])
        articles = extract_articles(body, spec, retrieved_at)
        # Do not retain full regulation downloads; only the selected articles.
        rows.extend(articles)
        coverage.append({'instrument_id': spec['id'], 'celex': spec['celex'],
            'download_url': f"https://publications.europa.eu/resource/celex/{spec['celex']}",
            'resolved_url': resolved, 'download_sha256': sha256(body).hexdigest(),
            'download_bytes': len(body), 'selected_articles': spec['articles'],
            'selected_characters': sum(len(d['text']) for d in articles),
            'extracted_nonwhitespace_coverage': 1.0, 'document_version': 'original_oj'})
    with (destination / 'documents.jsonl').open('x', encoding='utf-8') as handle:
        for document in rows:
            handle.write(json.dumps(document, ensure_ascii=False) + '\n')
    report = {'schema_version': 1, 'retrieved_at': retrieved_at, 'status': 'complete',
        'scope': NOTICE, 'articles': len(rows), 'characters': sum(len(d['text']) for d in rows),
        'documents_sha256': sha256((destination / 'documents.jsonl').read_bytes()).hexdigest(),
        'sources': coverage}
    (destination / 'coverage.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'complete', 'articles': len(rows), 'characters': report['characters']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.output, json.loads(Path(__file__).with_name('official-sources.json').read_text(encoding='utf-8')))
