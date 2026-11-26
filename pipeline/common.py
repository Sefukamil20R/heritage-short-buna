"""Shared helpers: storyboard loading + validation, hash caching, retries, runs.jsonl logging."""
import hashlib, json, os, pathlib, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
RUNS = ROOT / "runs.jsonl"
CACHE_FILE = OUT / ".cache.json"


def load_env():
    """Tiny .env reader so secrets live in .env (git-ignored), never in code."""
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def need(name):
    load_env()
    v = os.environ.get(name)
    if not v:
        raise SystemExit(f"Missing {name}. Copy .env.example to .env and fill it in.")
    return v


def load_storyboard():
    from jsonschema import validate  # pip install jsonschema
    sb = json.loads((ROOT / "storyboard.json").read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "schema" / "storyboard.schema.json").read_text())
    validate(sb, schema)
    ids = [s["id"] for s in sb["shots"]]
    assert len(ids) == len(set(ids)), "duplicate shot ids"
    return sb


def h(*parts):
    """Short stable hash of the inputs of a step. Same inputs -> same hash -> cache hit."""
    blob = json.dumps(parts, sort_keys=True, ensure_ascii=False, default=str).encode()
    return hashlib.sha256(blob).hexdigest()[:16]


def file_hash(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()[:16]


def _cache():
    return json.loads(CACHE_FILE.read_text()) if CACHE_FILE.exists() else {}


def is_cached(path, key):
    p = pathlib.Path(path)
    return p.exists() and _cache().get(str(p.relative_to(ROOT))) == key


def mark_cached(path, key):
    OUT.mkdir(exist_ok=True)
    c = _cache()
    c[str(pathlib.Path(path).relative_to(ROOT))] = key
    CACHE_FILE.write_text(json.dumps(c, indent=1))


def log_call(stage, model, params, seed=None, latency_s=0.0, cost_usd=0.0,
             status="ok", cached=False, shot=None, note=""):
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "stage": stage, "model": model,
           "shot": shot, "params": params, "seed": seed, "latency_s": round(latency_s, 3),
           "cost_usd": cost_usd, "status": status, "cached": cached, "note": note}
    with open(RUNS, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def retry(fn, tries=4, base=3.0, stage="?", shot=None, model="?"):
    """Exponential backoff. Every failed attempt is logged so FAILURES.md has evidence."""
    for i in range(tries):
        try:
            return fn()
        except Exception as e:  # noqa
            log_call(stage, model, {}, shot=shot, status="error", note=f"attempt {i+1}: {str(e)[:300]}")
            if i == tries - 1:
                raise
            time.sleep(base * (2 ** i))
