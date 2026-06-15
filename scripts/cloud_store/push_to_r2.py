#!/usr/bin/env python3
"""Push data patches to Cloudflare R2.

Uploads the top-level ``patches/NNNN-slug.yaml`` files verbatim (no JSON
conversion) under the ``flippatch/patches/`` prefix and writes a manifest at
``flippatch/manifest.json`` so downstream consumers (flipcommons'
``ingest_patches`` via ``make pull-patches``) can fetch the patch set without
listing the bucket.

The bucket is shared with the catalog (pindata, under ``pindata/``) and
pinexplore ingest sources (root); the ``flippatch/`` prefix keeps patches
isolated. Patches are NOT walked recursively: ``patches/authoring/`` holds
scratch tooling (generators, worksheets, caches) that must never ship.

The manifest sha256 is for download integrity only. It is unrelated to the
apply-time immutability hash, which flipcommons computes from normalized
patch content at ingest time.

Usage:
    python scripts/cloud_store/push_to_r2.py

Requires R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET
in environment or .env.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import TypedDict

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(REPO_ROOT / ".env")
PATCHES_DIR = REPO_ROOT / "patches"

# R2 prefix for the patch set. The manifest lives at ``<PREFIX>manifest.json``;
# patch files live at ``<PREFIX>patches/NNNN-slug.yaml``.
R2_PREFIX = "flippatch/"

EXCLUDE = {
    "manifest.json",
    ".DS_Store",
}


class ManifestEntry(TypedDict):
    """One row of ``flippatch/manifest.json`` (download-integrity metadata)."""

    path: str
    size: int
    sha256: str


class CollectedEntry(ManifestEntry):
    """A ``ManifestEntry`` plus the transient local path, stripped before write."""

    _local: Path


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _collect_patch_files(
    src: Path, path_prefix: str = "patches/"
) -> list[CollectedEntry]:
    """Collect top-level data patch files (``NNNN-slug.yaml``) only.

    The ``patches/`` tree is NOT walked recursively: subdirectories such as
    ``authoring/`` hold scratch tooling (generators, worksheets, caches) that
    must never be shipped to downstream consumers. Each entry carries a
    transient ``_local`` absolute path (stripped before the manifest is
    written).
    """
    entries: list[CollectedEntry] = []
    for full in src.glob("*.yaml"):
        if not full.is_file() or full.name in EXCLUDE:
            continue
        entries.append(
            {
                "path": path_prefix + full.name,
                "size": full.stat().st_size,
                "sha256": _sha256(full),
                "_local": full,
            }
        )
    entries.sort(key=lambda e: e["path"])
    return entries


def main() -> int:
    try:
        import boto3
    except ImportError:
        print("ERROR: boto3 is required. pip install boto3", file=sys.stderr)
        return 1

    account_id = os.environ.get("R2_ACCOUNT_ID")
    access_key = os.environ.get("R2_ACCESS_KEY_ID")
    secret_key = os.environ.get("R2_SECRET_ACCESS_KEY")
    bucket = os.environ.get("R2_BUCKET")

    missing = [
        name
        for name, val in [
            ("R2_ACCOUNT_ID", account_id),
            ("R2_ACCESS_KEY_ID", access_key),
            ("R2_SECRET_ACCESS_KEY", secret_key),
            ("R2_BUCKET", bucket),
        ]
        if not val
    ]
    if missing:
        print(f"ERROR: Missing env vars: {', '.join(missing)}", file=sys.stderr)
        return 1
    # The missing-check above guarantees bucket is set; narrow for the checker.
    assert bucket is not None

    if not PATCHES_DIR.is_dir():
        print(f"ERROR: no patches/ directory at {PATCHES_DIR}", file=sys.stderr)
        return 1

    # Build manifest from the top-level patch YAMLs.
    print("Building manifest...")
    entries = _collect_patch_files(PATCHES_DIR, path_prefix="patches/")
    print(f"  {len(entries)} patch files")

    manifest_entries: list[ManifestEntry] = [
        {"path": e["path"], "size": e["size"], "sha256": e["sha256"]} for e in entries
    ]
    manifest_bytes = (json.dumps(manifest_entries, indent=2) + "\n").encode("utf-8")

    # Upload to R2 under the flippatch/ prefix.
    print("Uploading to R2...")
    endpoint = f"https://{account_id}.r2.cloudflarestorage.com"
    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )

    uploaded = 0
    skipped = 0
    for entry in entries:
        local_path = entry["_local"]
        key = f"{R2_PREFIX}{entry['path']}"

        # Skip if remote file matches size AND content hash.
        try:
            head = s3.head_object(Bucket=bucket, Key=key)
            remote_size = head["ContentLength"]
            remote_etag = head["ETag"].strip('"')
            # Not security — must match R2/S3's MD5 ETag to detect unchanged
            # objects and skip re-upload.
            local_md5 = hashlib.md5(
                local_path.read_bytes(), usedforsecurity=False
            ).hexdigest()
            if remote_size == entry["size"] and remote_etag == local_md5:
                skipped += 1
                continue
        except s3.exceptions.ClientError:
            pass  # File doesn't exist remotely yet

        print(f"  {key}")
        s3.upload_file(str(local_path), bucket, key)
        uploaded += 1

    # Upload manifest last so consumers never see stale references.
    s3.put_object(
        Bucket=bucket,
        Key=f"{R2_PREFIX}manifest.json",
        Body=manifest_bytes,
        ContentType="application/json",
    )

    print(f"Done. {uploaded} uploaded, {skipped} unchanged.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
