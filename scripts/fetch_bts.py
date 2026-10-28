"""Download verified official BTS ZIP links; retain provenance, never overwrite files."""
import argparse
import hashlib
import json
import os
import tempfile
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def validate_archive(path):
    with zipfile.ZipFile(path) as archive:
        if not any(n.lower().endswith('.csv') for n in archive.namelist()):
            raise ValueError('Archive contains no CSV files')
        bad = archive.testzip()
        if bad:
            raise ValueError(f'ZIP integrity failure: {bad}')
        return archive.namelist()


def fetch(url, directory, year, quarter):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != 'https' or not (parsed.hostname == 'bts.gov' or (parsed.hostname or '').endswith('.bts.gov')):
        raise ValueError('Use a verified official HTTPS BTS download URL')
    name = Path(urllib.parse.unquote(parsed.path)).name
    if not name.lower().endswith('.zip'):
        raise ValueError('Expected a direct .zip download URL')
    target = directory / name
    metadata = directory / (name + '.json')
    if target.exists() or metadata.exists():
        raise FileExistsError(f'Refusing to overwrite {target} or its manifest')
    directory.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.download-', dir=directory)
    temporary = Path(temporary)
    try:
        digest = hashlib.sha256()
        with os.fdopen(fd, 'wb') as out, urllib.request.urlopen(url, timeout=120) as response:
            final_url = response.url
            while chunk := response.read(1024 * 1024):
                digest.update(chunk)
                out.write(chunk)
        members = validate_archive(temporary)
        info = dict(source_url=url, final_url=final_url,
                    retrieved_utc=datetime.now(timezone.utc).isoformat(),
                    requested_year=year, requested_quarter=quarter,
                    period_verified=False, bytes=temporary.stat().st_size,
                    sha256=digest.hexdigest(), members=members)
        temporary.rename(target)
        metadata.write_text(json.dumps(info, indent=2) + '\n')
        print(f'Downloaded {target.name}: {info["bytes"]:,} bytes; ZIP validated')
    finally:
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--year', type=int, required=True)
    parser.add_argument('--quarter', type=int, choices=range(1, 5), required=True)
    parser.add_argument('--url', action='append', required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    directory = root / 'data' / 'raw' / f'{args.year}Q{args.quarter}'
    for url in args.url:
        fetch(url, directory, args.year, args.quarter)


if __name__ == '__main__':
    main()
