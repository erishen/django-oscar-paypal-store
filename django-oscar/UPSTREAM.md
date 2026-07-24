# Upstream provenance

This directory is a vendored copy of the official django-oscar source
(originally an embedded git clone; history stripped when this project was
extracted into a standalone repository on 2026-07-24).

- Upstream: https://github.com/django-oscar/django-oscar
- Base commit: `002e67aa070b6469910b3ddea25d26356d0e34b1` (2025-11-19, post-4.1.0 master)
- Local customizations on top of that base (previously commit `431e2ffca`):
  - `sandbox/apps/paypal_express/` — PayPal Orders v2 integration
    (create/capture/refund, SSL retries, idempotency guards)
  - `sandbox/apps/dashboard/` — forked dashboard orders app: "refunded"
    payment events trigger real PayPal refunds
  - `sandbox/locale/zh_CN/` — project-level zh_CN translations (~83 strings)
  - `sandbox/templates/` + `sandbox/static/` — DEMO badge, EN|中文 language
    toggle, product card tweaks, PayPal button on payment details
  - `sandbox/settings.py` / `sandbox/urls.py` — app registration, LOCALE_PATHS,
    PayPal env config, paypal routes

To diff against upstream, compare with the base commit above.
