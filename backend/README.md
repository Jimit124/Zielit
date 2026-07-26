# Zielit Data Onboarding Backend

Lets a customer send you their contact data — by **SFTP** or by **API** — and turns
it into a clean, queryable audience you can hand back to them for a campaign.
This is infrastructure, not the marketing site: it doesn't need to be live
until your first customer signs up. Everything here is ready to deploy on a day's notice.

## How it works (matches the "How we do it" section on zielit.com)

```
Customer sends data                We load it                  You find the audience
─────────────────────      ─────────────────────      ──────────────────────────────
  SFTP folder     ─┐                                    Saved segments (rule-based):
                    ├──▶  Validate → Dedupe → Load  ──▶   "Opted-in, engaged 90 days"
  API upload      ─┘        into `contacts` table         "High engagement, no purchase"
                                                            ...or a custom rule-set
```

- **SFTP path:** each customer gets a folder (`/incoming/`). A watcher process checks
  it every 15 seconds, and anything dropped there is validated and loaded automatically.
- **API path:** `POST /uploads` with a file and the customer's API key — same
  validation and loading, synchronous response with a load report.
- Either way, the result lands in the same `contacts` table, so audience-building
  works identically no matter how the data arrived.

## File format

One row per contact. Only `email` is required — everything else improves targeting
but is optional. See `sample_data/contacts_template.csv`.

| Column | Required | Notes |
|---|---|---|
| `email` | **yes** | Must be a valid address; used to de-duplicate on re-upload |
| `first_name`, `last_name` | no | |
| `company`, `industry`, `job_title` | no | Used for B2B segmentation |
| `country` | no | |
| `engagement_score` | no | 0–100, higher = more engaged (customer-supplied or defaulted to 0) |
| `last_purchase_date` | no | `YYYY-MM-DD`, `MM/DD/YYYY`, or `DD/MM/YYYY` |
| `consent_status` | no | `opted_in`, `opted_out`, or `unknown` (defaults to `unknown` — **never emailed** until explicitly opted in on your side) |
| `consent_date` | no | Same date formats as above |
| `tags` | no | Semicolon- or comma-separated, e.g. `newsletter;webinar-attendee` |

Bad rows (invalid email, unparseable data) are skipped and reported back in the
upload's `error_report` — they don't fail the whole file.

## Finding the right audience

Segments are saved as small rule-sets (see `app/segmentation.py`), e.g.:

```json
{
  "match": "all",
  "conditions": [
    {"field": "consent_status", "op": "eq", "value": "opted_in"},
    {"field": "engagement_score", "op": "gte", "value": 40},
    {"field": "industry", "op": "in", "value": ["SaaS", "Fintech"]}
  ]
}
```

Because the rule-set is data, not hard-coded SQL, a saved segment stays live —
re-running it after the customer's next upload automatically reflects new or
updated contacts. `GET /segments/starter-templates` returns three ready-made
segments (recently engaged, high-value prospects, win-back) so there's something
useful the moment the first file lands, before anyone has written a custom rule.

## Running it locally

Requires Docker.

```bash
cp .env.example .env
docker compose up --build
```

This starts:
- **db** — Postgres, schema auto-created from `schema.sql`
- **api** — FastAPI on `http://localhost:8000` (interactive docs at `/docs`)
- **sftp** — SFTP server on port `2222`, with one demo account (`demo` / `demo-pass123`)
- **watcher** — polls the SFTP folders and loads anything dropped there

### Try it end-to-end

1. Create a customer (this is what you'd do when someone signs up):
   ```bash
   curl -X POST http://localhost:8000/admin/customers \
     -H "Content-Type: application/json" \
     -d '{"name": "Acme Corp", "contact_email": "ops@acme.com"}'
   ```
   Save the returned `api_key` — you'll need it for every request below.

2. Upload via API:
   ```bash
   curl -X POST http://localhost:8000/uploads \
     -H "x-api-key: <api_key>" \
     -F "file=@sample_data/contacts_template.csv"
   ```

   Or upload via SFTP instead (same result, picked up within 15s):
   ```bash
   sftp -P 2222 demo@localhost
   put sample_data/contacts_template.csv incoming/
   ```

3. Create a segment and pull the audience:
   ```bash
   curl -X POST http://localhost:8000/segments \
     -H "x-api-key: <api_key>" -H "Content-Type: application/json" \
     -d '{"name": "Engaged US SaaS", "rules": {"match":"all","conditions":[
           {"field":"consent_status","op":"eq","value":"opted_in"},
           {"field":"engagement_score","op":"gte","value":40}]}}'

   curl http://localhost:8000/segments/<segment_id>/contacts -H "x-api-key: <api_key>"
   ```

## Adding a real customer's SFTP account

The demo Docker Compose file has one hardcoded SFTP account, which is fine for
testing but not for onboarding real customers without a redeploy each time.
Two ways to fix that when you're ready to go live:

- **Fastest to launch:** self-hosted, add accounts by mounting a `users.conf`
  file for the `atmoz/sftp` image and reloading — fine for a handful of early customers.
- **Recommended for production:** [AWS Transfer Family](https://aws.amazon.com/aws-transfer-family/)
  (managed SFTP backed by S3) — accounts can be provisioned by API call the moment
  someone signs up, no server to babysit, and it drops files somewhere a Lambda
  or this same watcher logic can pick them up.

## Deployment recommendation

- **API + Postgres:** Render or Railway — both deploy straight from this repo,
  managed Postgres included, and are inexpensive to run idle until you have a
  real customer.
- **SFTP:** AWS Transfer Family for production; the Docker Compose `sftp`
  service for early testing/demos.
- **Secrets:** move `api_key` generation and the Postgres password out of
  compose defaults before handling real customer data — use your host's
  secret manager.

## Compliance notes (email marketing specifically)

- `consent_status` defaults to `unknown` on load — contacts are never treated
  as opted in just because they appeared in a file. Marketing sends should
  filter on `consent_status = opted_in` everywhere, not just in one segment.
- Keep `consent_date` and the original `source_upload_id` on every contact —
  it's your evidence trail if a customer is ever asked to prove consent
  (GDPR, CAN-SPAM, CASL).
- This backend doesn't send email itself — it prepares the audience. Wire the
  segment output into whatever sending tool you use for the actual campaign.
