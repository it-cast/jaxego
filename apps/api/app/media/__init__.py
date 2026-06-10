"""Media validation + reprocessing for KYC documents (Phase 5, T-03).

The server is the authority over every uploaded byte (owasp upload / TH-02). The
client uploads a raw image straight to B2 (presigned PUT); the backend then
downloads it, validates it by MAGIC BYTES (never the declared extension /
content-type), re-encodes it with Pillow (resize ≤1920, WebP, FULL EXIF strip),
confirms the SHA-256 of the derivative, and serves ONLY the derivative. The raw
byte is never served.
"""
