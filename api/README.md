# Feed API

This package exposes the generated feeds over two public HTTP endpoints:

- `GET /api/content-feed.xml`
- `GET /api/propositions-feed.xml`

Run it from the project root:

```bash
python3 -m api
```

Default behavior:

- binds to `0.0.0.0:8000`
- allows all origins with permissive CORS headers
- regenerates the XML before each response
- uses `feed_module/xml_example/fk-inhome.com.ua.xml` as the base source
- uses `feed_module/xml_example/fk-inhome.com.ua=2.xml` as the supplemental image source
- writes logs to `logs/convert-api-YYYY-MM-DD.log`

Useful options:

```bash
python3 -m api --host 0.0.0.0 --port 8000
python3 -m api --source /path/to/source.xml --supplemental-source /path/to/extra.xml
python3 -m api --log-level DEBUG
```
