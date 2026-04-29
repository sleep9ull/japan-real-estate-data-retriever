# Source ID Strategy

Different sites may reuse the same numeric listing ID. Never store a raw listing ID as the global primary key.

## Global ID

Use:

```text
<source>:<source_listing_id>
```

Examples:

```text
suumo:73345621
athome:1029384756
homes:B-1234567890
yahoo_japan:000012345678
```

## URL Fallback

If no stable source listing ID is visible, keep `source_listing_id = null`, keep `source_url`, and generate:

```text
<source>:url:<first-16-chars-of-sha256-canonical-url>
```

Canonical URL rules:

- trim whitespace
- lowercase scheme and host
- remove URL fragment
- remove trailing slash except root
- keep query string if it appears necessary to identify the listing

## Future Storage Keys

If a future storage layer is added, use these keys:

- primary key: `id`
- unique source tuple: `(source, source_listing_id)` when `source_listing_id` is not null
- additional index: `(source, source_url)`
