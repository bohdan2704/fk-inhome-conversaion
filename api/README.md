# Feed API

This package exposes the generated feeds over two public HTTP endpoints:

- `GET /api/content-feed.xml`
- `GET /api/propositions-feed.xml`

Run it from the project root:

```bash
python3 main.py
```

Default behavior:

- binds to `0.0.0.0:8000`
- allows all origins with permissive CORS headers
- regenerates the XML before each response
- downloads the Rozetka and Prom XML feeds before generation when `FEED_SOURCE_URL` and `FEED_SUPPLEMENTAL_SOURCE_URL` are configured
- stores the downloaded source files in `feed_module/downloaded/`
- gives each downloaded XML a UTC timestamp in its filename so older snapshots are kept
- writes logs to `logs/convert-api-YYYY-MM-DD.log`

Useful options:

```bash
python3 main.py --host 0.0.0.0 --port 8000
python3 main.py --source-url https://example.com/rozetka.xml --supplemental-source-url https://example.com/prom.xml
python3 main.py --log-level DEBUG
```

Local source download entrypoint:

```bash
python3 download_sources.py
python3 download_sources.py --source-url https://example.com/rozetka.xml --supplemental-source-url https://example.com/prom.xml
```
