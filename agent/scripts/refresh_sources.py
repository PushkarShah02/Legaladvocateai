"""Recheck reviewed bytes without sending case details to a source host."""

import argparse
import asyncio
import hashlib
import json
from datetime import datetime, timezone
from urllib.parse import urlparse

import aiohttp

from advocate.legal import PACK


async def refresh(selected=None):
    pack = json.loads(PACK.read_text(encoding="utf-8"))
    reports = []
    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=20)
    ) as session:
        for source_id, source in pack["sources"].items():
            if selected and source_id not in selected:
                continue
            url = source["url"]
            parsed = urlparse(url)
            if parsed.scheme != "https" or parsed.hostname not in {
                "egazette.gov.in",
                "consumerhelpline.gov.in",
            }:
                raise ValueError("Source host is not allowlisted.")
            try:
                async with session.get(url, allow_redirects=False) as response:
                    response.raise_for_status()
                    if response.status != 200:
                        raise ValueError(
                            "Unexpected response; redirects are not followed."
                        )
                    body = await response.content.read(8 * 1024 * 1024 + 1)
                    if len(body) > 8 * 1024 * 1024:
                        raise ValueError("Source exceeds size limit.")
                if hashlib.sha256(body).hexdigest() != source["sha256"]:
                    candidate = PACK.parent / (source["file"] + ".candidate")
                    candidate.write_bytes(body)
                    reports.append(
                        {
                            "source": source_id,
                            "status": "changed_manual_review_required",
                            "candidate": candidate.name,
                        }
                    )
                else:
                    source["checked_at"] = datetime.now(timezone.utc).isoformat()
                    reports.append(
                        {
                            "source": source_id,
                            "status": "same_reviewed_bytes_retrieved",
                            "checked_at": source["checked_at"],
                        }
                    )
            except (aiohttp.ClientError, TimeoutError, ValueError) as error:
                reports.append(
                    {
                        "source": source_id,
                        "status": "not_refreshed",
                        "reason": str(error),
                    }
                )
    PACK.write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(reports, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", action="append")
    asyncio.run(refresh(parser.parse_args().source))
