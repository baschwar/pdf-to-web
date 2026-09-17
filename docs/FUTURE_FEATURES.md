# Future Features

## Connected WordPress Publishing

Add an optional authenticated WordPress connection after the manual media
mapping workflow is proven in production.

Potential scope:

- Connect over HTTPS using a revocable WordPress Application Password or an
  institution-approved authentication mechanism.
- Test site capabilities and permissions before attempting writes.
- Upload extracted images through the WordPress Media REST API.
- Capture authoritative attachment IDs, source URLs, generated sizes, and CDN
  rewrites instead of predicting upload paths.
- Apply alt text and captions from the reviewed document.
- Regenerate Gutenberg and WXR with resolved `core/image` blocks.
- Optionally create or update a draft page or post only after explicit user
  confirmation.
- Never store a normal WordPress login password in a PDF to Web project.

This is intentionally deferred. The current supported workflow is local asset
export followed by manual Media Library upload and CSV mapping import.
