# WordPress round-trip validation

This isolated local stack proves that generated WXR can be imported, opened in
the block editor, edited, saved, and reopened. Imported content remains Draft.

The `pdf-to-web-block-contract` plugin is a validation shim. It registers the
attributes and save behavior used by the `wsuwp/hero` and `wsuwp/section`
fixtures so WordPress can check their serialization. It is not WSUWP production
code and does not prove compatibility with an untested version of the real WSU
block plugin.

## Run

From the repository root:

```sh
PYTHONPATH=src python3 -m pdf_to_web.cli wordpress-fixtures \
  --output build/wordpress-fixtures
docker compose -f tools/wordpress-roundtrip/compose.yml pull
docker compose -f tools/wordpress-roundtrip/compose.yml up -d db wordpress
docker compose -f tools/wordpress-roundtrip/compose.yml run --rm cli \
  wp core install --url=http://localhost:8099 --title='PDF to Web Round Trip' \
  --admin_user=admin --admin_password=pdf-to-web-test \
  --admin_email=test@example.invalid --skip-email
docker compose -f tools/wordpress-roundtrip/compose.yml run --rm cli \
  wp plugin activate pdf-to-web-block-contract
docker compose -f tools/wordpress-roundtrip/compose.yml run --rm cli \
  wp plugin install wordpress-importer --activate
```

Import the XML files from `/fixtures` with `wp import`, then run:

```sh
cd tools/wordpress-roundtrip
npm install
npm run validate-editor
```

The browser report and screenshots are written to
`build/wordpress-editor/`. Tear down the disposable stack with:

```sh
docker compose -f tools/wordpress-roundtrip/compose.yml down -v
```
