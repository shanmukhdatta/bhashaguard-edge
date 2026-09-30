"""Conservative claim review. Only whole, curated claim forms earn a verdict."""
from __future__ import annotations

import hashlib
import json
import math
import platform
import time
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

import regex

LANGUAGES = {"te": "Telugu", "ta": "Tamil", "kn": "Kannada"}
DEFAULT_PACK = Path(__file__).parent / "data" / "demo_pack.json"
MAX_TEXT = 12000


def normalized(text: str) -> str:
    return " ".join(unicodedata.normalize("NFC", text).casefold().split()).strip(" .!?।॥")


def script_fidelity(text: str, language: str, allow_latin: bool = False) -> dict:
    """Count Unicode Alphabetic code points; offsets refer to original text."""
    if language not in LANGUAGES:
        raise ValueError("Language must be te, ta or kn")
    script = regex.compile(r"\p{Script_Extensions=" + LANGUAGES[language] + "}")
    alphabetic = regex.compile(r"\p{Alphabetic}")
    latin = regex.compile(r"\p{Script_Extensions=Latin}")
    assessed = target = excluded = 0
    issues = []
    for offset, char in enumerate(text):
        if not alphabetic.fullmatch(char):
            continue
        if allow_latin and latin.fullmatch(char):
            excluded += 1
            continue
        assessed += 1
        if script.fullmatch(char):
            target += 1
        else:
            issues.append({"offset": offset, "character": char,
                           "unicode_name": unicodedata.name(char, "UNNAMED")})
    return {"ratio": target / assessed if assessed else None,
            "target_count": target, "assessed_count": assessed,
            "excluded_latin_count": excluded, "violations": issues,
            "policy": "Alphabetic code points with target Script_Extensions; optional Latin exclusion",
            "offset_unit": "Python Unicode code points in the original response",
            "regex_version": regex.__version__}


def load_pack(path: str | Path = DEFAULT_PACK) -> dict:
    raw = Path(path).read_bytes()
    pack = json.loads(raw)
    if pack.get("schema_version") != 1 or not isinstance(pack.get("entries"), list):
        raise ValueError("Expected schema_version 1 and an entries array")
    if pack.get("kind") not in ("synthetic_fixture", "reviewed_evidence"):
        raise ValueError("Pack kind must be synthetic_fixture or reviewed_evidence")
    if not pack.get("pack_id") or not pack.get("version"):
        raise ValueError("Pack identity and version are required")
    seen = set()
    fields = ("id", "language", "locale", "source_url", "source_title", "excerpt",
              "license", "reviewer", "reviewed_on", "translation_en")
    for entry in pack["entries"]:
        if any(not isinstance(entry.get(k), str) or not entry[k] for k in fields):
            raise ValueError("Each evidence entry needs non-empty provenance fields")
        if entry["id"] in seen:
            raise ValueError("Duplicate evidence ID")
        seen.add(entry["id"])
        if entry["language"] not in LANGUAGES:
            raise ValueError("Unsupported evidence language")
        if not entry["source_url"].startswith(("https://", "http://", "fixture://")):
            raise ValueError("Evidence URL must use http, https or fixture")
        if pack["kind"] == "reviewed_evidence" and entry["source_url"].startswith("fixture://"):
            raise ValueError("Synthetic sources cannot be labelled reviewed evidence")
        for key in ("supported_forms", "contradicted_forms", "valid_variants"):
            forms = entry.get(key, [])
            if not isinstance(forms, list) or any(not isinstance(t, str) or not normalized(t) for t in forms):
                raise ValueError("Claim forms must be non-empty strings")
        if not entry.get("supported_forms"):
            raise ValueError("At least one supported form is required")
    pack["sha256"] = hashlib.sha256(raw).hexdigest()
    return pack


def split_claims(text: str) -> list[dict]:
    """Sentence candidates only. This is not a trained factual claim extractor."""
    claims = []
    for match in regex.finditer(r"[^.!?।॥\n]+(?:[.!?।॥]+|$)", text, regex.MULTILINE):
        part = match.group()
        leading = len(part) - len(part.lstrip())
        value = part.strip()
        if value and regex.search(r"\p{Alphabetic}", value):
            start = match.start() + leading
            claims.append({"text": value, "start": start, "end": start + len(value)})
    return claims


def grams(text: str) -> Counter:
    value = normalized(text)
    return Counter(value[i:i+3] for i in range(max(0, len(value)-2)))


def similarity(left: str, right: str) -> float:
    a, b = grams(left), grams(right)
    norm = math.sqrt(sum(v*v for v in a.values()) * sum(v*v for v in b.values()))
    return sum(v * b[k] for k, v in a.items()) / norm if norm else 0.0


class Guard:
    def __init__(self, pack_path: str | Path = DEFAULT_PACK, embedder=None):
        self.pack = load_pack(pack_path)
        self.embedder = embedder

    def _check_claim(self, claim: dict, language: str, locale: str) -> dict:
        value = normalized(claim["text"])
        entries = [e for e in self.pack["entries"] if e["language"] == language]
        exact = []
        for entry in entries:
            for forms, status in (("supported_forms", "supported"),
                                  ("contradicted_forms", "contradicted"),
                                  ("valid_variants", "valid_variant")):
                if value in [normalized(t) for t in entry.get(forms, [])]:
                    exact.append((entry, status))
        scoped = [(e, s) for e, s in exact if e["locale"] == locale]
        status, reason = "unresolved", "No exact reviewed claim form matched. Retrieved passages are suggestions only."
        evidence_ids = []
        if scoped:
            states = {s for _, s in scoped}
            evidence_ids = sorted({e["id"] for e, _ in scoped})
            if "contradicted" in states and len(states) > 1:
                reason = "Evidence pack contains conflicting labels. Human review is required."
            else:
                status = "contradicted" if "contradicted" in states else ("valid_variant" if "valid_variant" in states else "supported")
                reason = "Exact whole-claim match to a curated form in the selected language and locale."
        elif exact:
            reason = "The claim matches evidence for a different locale. No factual verdict was assigned."
        candidates = [e for e in entries if e["locale"] == locale]
        ranked = sorted(((similarity(claim["text"], e["excerpt"]), e["id"]) for e in candidates), reverse=True)[:3]
        result = {**claim, "status": status, "reason": reason, "evidence_ids": evidence_ids,
                  "context_mismatch": bool(exact and not scoped),
                  "retrieval": [{"id": eid, "score": round(score, 5)} for score, eid in ranked if score > 0],
                  "retrieval_method": "character-trigram cosine, lexical CPU baseline",
                  "semantic_distance": None}
        if self.embedder and candidates:
            hits = self.embedder.retrieve(claim["text"], candidates)
            result["retrieval"] = hits
            result["retrieval_method"] = "multilingual-e5-small, local CPU embeddings"
            result["semantic_distance"] = (1 - hits[0]["score"]) / 2 if hits else None
            result["semantic_distance_note"] = "Distance to best retrieved passage, not entailment or cultural correctness."
        return result

    def analyze(self, text: str, language: str = "te", locale: str = "fictional:vennela",
                prompt: str = "", allow_latin: bool = False) -> dict[str, Any]:
        if not isinstance(text, str) or not text.strip() or len(text) > MAX_TEXT:
            raise ValueError(f"Provide 1 to {MAX_TEXT} response characters")
        if language not in LANGUAGES:
            raise ValueError("Language must be te, ta or kn")
        if not isinstance(prompt, str) or len(prompt) > MAX_TEXT:
            raise ValueError("Prompt is too long or invalid")
        if not isinstance(locale, str) or not locale or len(locale) > 200:
            raise ValueError("Provide a locale of 1 to 200 characters")
        if not isinstance(allow_latin, bool):
            raise ValueError("allow_latin must be a boolean")
        start = time.perf_counter()
        script = script_fidelity(text, language, allow_latin)
        findings = [self._check_claim(c, language, locale) for c in split_claims(text)]
        counts = Counter(f["status"] for f in findings)
        supported = counts["supported"] + counts["valid_variant"]
        contradicted = counts["contradicted"]
        checked = supported + contradicted
        flags = []
        if script["violations"]:
            flags.append("script_mismatch")
        if contradicted:
            flags.append("evidence_contradiction")
        if any(c["context_mismatch"] for c in findings):
            flags.append("context_mismatch")
        if counts["unresolved"] or not findings:
            flags.append("insufficient_evidence")
        risk = "review_required" if any(f != "insufficient_evidence" for f in flags) else ("unresolved" if flags else "no_flag_in_pack")
        return {"schema_version": 1, "response": text, "prompt": prompt, "language": language,
                "locale": locale, "script": script, "claims": findings,
                "metrics": {"claim_count": len(findings), "supported": supported,
                            "contradicted": contradicted, "unresolved": counts["unresolved"],
                            "valid_variants": counts["valid_variant"],
                            "consistency": supported / checked if checked else None,
                            "coverage": checked / len(findings) if findings else None},
                "risk": {"level": risk, "flags": flags, "probability": None},
                "evidence": self.pack["entries"],
                "pack": {k: self.pack[k] for k in ("pack_id", "version", "kind", "sha256")},
                "runtime": {"backend": "CPU", "npu_used": False,
                            "embedding_model": self.embedder.model_id if self.embedder else None,
                            "platform": platform.platform(), "machine": platform.machine(),
                            "python": platform.python_version(),
                            "guard_latency_ms": round((time.perf_counter()-start)*1000, 3)},
                "limitations": ["Sentence segmentation and exact curated forms are a limited baseline.",
                                "The prompt is retained for review; arbitrary prompt entailment is not implemented.",
                                "Script fidelity is not language identification.",
                                "Missing evidence never establishes that a claim is false.",
                                "No calibrated risk probability or Snapdragon NPU acceleration is implemented."]}
