# Primary-source pack

Source text was retrieved and inspected for this implementation on 9 November
2026 (IST). This was not a review by a licensed advocate. `sources.json` maps a
small set of supported propositions to actual excerpts, source files, URLs,
SHA-256 hashes and source-check dates.

- [Gazette of India, Consumer Protection Act 2019](https://egazette.gov.in/WriteReadData/2019/210422.pdf): original enacted text. Curated excerpts cover section 2(7), section 35, section 39(1)(a)-(d) and section 69. This is not a consolidated assurance of all current amendments.
- [National Consumer Helpline, Department of Consumer Affairs](https://consumerhelpline.gov.in/public/convergenceprogram): pre-litigation grievance-channel information. This is administrative guidance, not an adjudicated entitlement or an extension of a limitation period.

India Code timed out during retrieval; the Chandigarh court mirror had a TLS
trust failure. Certificate validation was not disabled. The statute was instead
retrieved directly from the Gazette of India.

`jurisdiction-2021.pdf` was retrieved from an official government-hosted NCDRC
practice direction, but its text extraction was not reliable. It is retained as
research material and is **not** a supported runtime proposition. The old monetary
threshold from section 34(1) of the original Act is intentionally not exposed.
The assistant must not supply a remembered forum threshold, fee, portal procedure,
judgment, penalty or precise deadline as verified law.

Runtime status meanings:

| Status | Meaning |
|---|---|
| `verified_source_snapshot` | The bounded proposition has an inspected official source, a matching stored hash, and a source-check date within 30 days. Applicability and amendment completeness remain uncertain. |
| `reference_only` | The source check is too old or the clock is inconsistent. Specific legal assertions are blocked pending refresh/review. |
| `unverified` | No supported entry, source unavailable/malformed, or integrity check failed. Do not fabricate a replacement proposition. |

`scripts/build_source_pack.py` reproduces the original curated excerpts with their
original review date. It must not be used to falsely claim a new retrieval or
expert legal review. `scripts/refresh_sources.py` fetches only allowlisted official
URLs, with timeouts, certificate verification, size limits and no redirects. It
sends no case data. Changed content is saved as a candidate and requires manual
review; it does not silently replace the trusted source. Even identical source
bytes do not prove that no separate amending instrument exists.

There is no arbitrary web RAG, case-law database, OCR, document authentication,
automated amendment monitoring or definitive limitation calculator in this MVP.
