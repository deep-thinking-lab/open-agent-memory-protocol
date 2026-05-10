#!/usr/bin/env python3
"""Translate OAMP spec markdown and README into ja/zh/ko/ms via OpenAI.

Two translation surfaces:

1. **Spec files**: every spec version under spec/, finding the canonical
   English source (prefers oamp-v{N}.md, falls back to oamp-v{N}-draft.md),
   translated into oamp-v{N}.{lang}.md alongside the source. Output
   filenames always drop the -draft suffix so dthink.ai's content paths
   stay stable across promotion.

2. **README**: README.md at the repo root, translated into
   docs/README.{lang}.md.

A translation is regenerated only if it is missing or older (per git
commit timestamp) than its source. This keeps re-runs cheap and produces
minimal PRs.

Designed to be invoked from the auto-translate-spec.yml workflow with
OPENAI_API_KEY in env.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from openai import OpenAI


LANGS = {
    "ja": "Japanese",
    "zh": "Chinese (Simplified)",
    "ko": "Korean",
    "ms": "Bahasa Melayu",
}

SPEC_PROMPT = (
    "You are a technical translator for an IETF-style protocol "
    "specification. Translate the following markdown document into "
    "{language}. Preserve all markdown formatting, code blocks, JSON "
    "examples, file paths, URLs, and identifiers exactly as they appear. "
    "Keep RFC 2119 keywords (MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, "
    "SHOULD, SHOULD NOT, RECOMMENDED, MAY, OPTIONAL) in English. Translate "
    "prose, headings, table cells, and prose comments only. Do not add "
    "translator notes or commentary."
)

README_PROMPT = (
    "You are a technical translator for an open-source project README. "
    "Translate the following markdown document into {language}. Preserve "
    "all markdown formatting, code blocks, shell commands, JSON examples, "
    "file paths, URLs, package names, and import statements exactly as "
    "they appear. Keep technical identifiers (function names, type names, "
    "CLI flags) in English. Translate prose, headings, table cells, and "
    "image alt text only. Do not add translator notes or commentary."
)

# Spec targets: (version_dir, source_base, output_stem).
# source_base is the filename without .md or -draft.md.
# output_stem is what translated files are named (without .{lang}.md).
SPEC_TARGETS = [
    ("spec/v1", "oamp-v1", "oamp-v1"),
    ("spec/v1.1", "oamp-v1.1", "oamp-v1.1"),
    ("spec/v1.2", "oamp-v1.2", "oamp-v1.2"),
    ("spec/v1.2", "oamp-v1.2-governed-memory", "oamp-v1.2-governed-memory"),
    ("spec/v1.3", "oamp-v1.3", "oamp-v1.3"),
]


def find_source(version_dir: Path, base: str) -> Path | None:
    stable = version_dir / f"{base}.md"
    if stable.exists():
        return stable
    draft = version_dir / f"{base}-draft.md"
    if draft.exists():
        return draft
    return None


def git_commit_time(path: Path, repo: Path) -> int | None:
    try:
        out = subprocess.check_output(
            ["git", "log", "-1", "--format=%ct", "--", str(path.relative_to(repo))],
            cwd=repo,
            text=True,
        ).strip()
        return int(out) if out else None
    except (subprocess.CalledProcessError, ValueError):
        return None


def needs_update(source: Path, translated: Path, repo: Path) -> bool:
    if not translated.exists():
        return True
    src_t = git_commit_time(source, repo)
    tx_t = git_commit_time(translated, repo)
    if src_t is None or tx_t is None:
        return True
    return src_t > tx_t


def translate(client: OpenAI, source_text: str, language: str, prompt: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt.format(language=language)},
            {"role": "user", "content": source_text},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content


class Counts:
    __slots__ = ("updated", "skipped", "missing")

    def __init__(self) -> None:
        self.updated = 0
        self.skipped = 0
        self.missing = 0


def translate_one(
    client: OpenAI,
    source: Path,
    out: Path,
    lang_name: str,
    prompt: str,
    repo: Path,
    counts: Counts,
) -> bool:
    """Translate source to out if out is missing or older. Returns True on
    success or skip; False on translation failure."""
    if not needs_update(source, out, repo):
        print(f"skip: {out.relative_to(repo)} up-to-date")
        counts.skipped += 1
        return True

    print(f"translate: {source.relative_to(repo)} -> {out.relative_to(repo)} ({lang_name})")
    try:
        translated = translate(client, source.read_text(), lang_name, prompt)
    except Exception as exc:  # noqa: BLE001 — surface any API error
        print(f"ERROR: OpenAI call failed for {out}: {exc}", file=sys.stderr)
        return False

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(translated)
    counts.updated += 1
    return True


def translate_specs(client: OpenAI, repo: Path, counts: Counts) -> bool:
    for rel_dir, source_base, output_stem in SPEC_TARGETS:
        version_dir = repo / rel_dir
        source = find_source(version_dir, source_base)
        if source is None:
            print(f"skip: no source in {rel_dir} for {source_base}")
            counts.missing += 1
            continue

        for code, name in LANGS.items():
            out = version_dir / f"{output_stem}.{code}.md"
            if not translate_one(client, source, out, name, SPEC_PROMPT, repo, counts):
                return False
    return True


def translate_readme(client: OpenAI, repo: Path, counts: Counts) -> bool:
    source = repo / "README.md"
    if not source.exists():
        print("skip: README.md not found at repo root")
        counts.missing += 1
        return True

    docs = repo / "docs"
    for code, name in LANGS.items():
        out = docs / f"README.{code}.md"
        if not translate_one(client, source, out, name, README_PROMPT, repo, counts):
            return False
    return True


def main() -> int:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set", file=sys.stderr)
        return 1

    client = OpenAI(api_key=api_key)
    repo = Path(__file__).resolve().parents[1]
    counts = Counts()

    if not translate_specs(client, repo, counts):
        return 1
    if not translate_readme(client, repo, counts):
        return 1

    print(
        f"done: {counts.updated} updated, "
        f"{counts.skipped} skipped, "
        f"{counts.missing} missing source(s)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
