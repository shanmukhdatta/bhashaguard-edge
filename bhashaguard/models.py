"""Optional local model adapters. No automatic weight downloads."""
import json
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler


class E5Retriever:
    def __init__(self, model_dir: str):
        location = Path(model_dir).resolve()
        if not location.is_dir():
            raise ValueError("E5 model directory does not exist. Download weights separately first.")
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise ValueError('Install the embeddings extra: pip install ".[embeddings]"') from exc
        self.model = SentenceTransformer(str(location), device="cpu", local_files_only=True,
                                         trust_remote_code=False)
        self.model_id = str(location)
        self.cache = {}

    def retrieve(self, query, entries):
        key = tuple((e["id"], e["excerpt"]) for e in entries)
        if key not in self.cache:
            self.cache[key] = self.model.encode(["passage: " + e["excerpt"] for e in entries],
                                               normalize_embeddings=True)
        vec = self.model.encode(["query: " + query], normalize_embeddings=True)[0]
        scores = self.cache[key] @ vec
        ranked = sorted(zip(scores, entries), key=lambda x: float(x[0]), reverse=True)[:3]
        return [{"id": e["id"], "score": max(-1., min(1., float(score)))} for score, e in ranked]


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Local model endpoint redirects are disabled")


def generate_local(prompt: str, language: str, endpoint: str, model: str) -> str:
    url = urlparse(endpoint)
    if url.scheme != "http" or url.hostname not in ("127.0.0.1", "::1") or url.username or url.password:
        raise ValueError("The model endpoint must be an HTTP loopback IP address")
    if url.query or url.fragment:
        raise ValueError("Do not include query strings or fragments in the endpoint")
    body = {"model": model, "messages": [
        {"role": "system", "content": f"Answer in {language}. State uncertainty when evidence is missing."},
        {"role": "user", "content": prompt}], "max_tokens": 400, "temperature": .2}
    req = Request(endpoint, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    opener = build_opener(ProxyHandler({}), NoRedirect())
    with opener.open(req, timeout=90) as response:
        raw = response.read(1_000_001)
    if len(raw) > 1_000_000:
        raise ValueError("Model response exceeded the size limit")
    result = json.loads(raw)["choices"][0]["message"]["content"]
    if not isinstance(result, str) or not result.strip() or len(result) > 12000:
        raise ValueError("Model returned empty, invalid or oversized text")
    return result
