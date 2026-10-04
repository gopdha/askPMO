"""Upload `corpus/` with relative paths in one request and wait for the ingest job (`make seed`)."""

from __future__ import annotations

import mimetypes
import os
import sys
import time
from pathlib import Path

import httpx

BASE_URL = os.environ.get("ASKPMO_BASE_URL", "http://localhost:8080")
POLL_INTERVAL_S = 3.0
TIMEOUT_S = 900.0


def corpus_files(root: Path) -> list[Path]:
    """Every file under the corpus root, sorted."""
    return sorted(path for path in root.rglob("*") if path.is_file())


def upload(root: Path, client: httpx.Client) -> dict[str, object]:
    """POST all files as `files[]` with parallel `rel_paths[]`."""
    paths = corpus_files(root)
    files = [
        (
            "files[]",
            (path.name, path.read_bytes(), mimetypes.guess_type(path.name)[0] or "application/octet-stream"),
        )
        for path in paths
    ]
    data = {"rel_paths[]": [path.relative_to(root).as_posix() for path in paths]}
    response = client.post(f"{BASE_URL}/api/documents", files=files, data=data, timeout=120)
    response.raise_for_status()
    body: dict[str, object] = response.json()
    print(f"uploaded {len(paths)} files; job {body['job_id']}; {len(body['document_ids'])} to index")  # type: ignore[arg-type]
    return body


def wait_for_job(job_id: str, client: httpx.Client) -> dict[str, object]:
    """Poll the job until it finishes."""
    deadline = time.monotonic() + TIMEOUT_S
    while time.monotonic() < deadline:
        job: dict[str, object] = client.get(f"{BASE_URL}/api/ingest-jobs/{job_id}", timeout=30).json()
        print(f"  {job['status']}: {job['documents_done']} docs, {job['chunks_written']} chunks")
        if job["status"] in {"succeeded", "failed"}:
            return job
        time.sleep(POLL_INTERVAL_S)
    raise TimeoutError(f"job {job_id} did not finish in {TIMEOUT_S:.0f}s")


def main(corpus_dir: str = "corpus") -> int:
    """Seed the corpus; exit 1 if the job fails."""
    with httpx.Client() as client:
        body = upload(Path(corpus_dir), client)
        job = wait_for_job(str(body["job_id"]), client)
        documents = client.get(f"{BASE_URL}/api/documents", timeout=30).json()
    indexed = [doc for doc in documents if doc["status"] == "indexed"]
    total_chunks = sum(int(doc["chunk_count"]) for doc in indexed)
    print(
        f"job {job['status']}; documents indexed {len(indexed)}/{len(documents)}; total chunks {total_chunks}"
    )
    if job.get("error"):
        print(f"error: {job['error']}")
    return 0 if job["status"] == "succeeded" else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
