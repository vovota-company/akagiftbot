# AkaGiftBot Wallet API

Django REST Framework API for email-only Google authentication, deterministic BIP-39/BIP-44 Ethereum/BNB Smart Chain wallets, USDT BEP-20 deposit monitoring, idempotent deposit ledgering, and automatic collection (sweep) to a central wallet.

This project intentionally contains **no Docker configuration** and uses **SQLite** by default.

## Important security note

The root BIP-39 mnemonic controls the central wallet and every derived user wallet. Never commit it to Git. For production, place it in a KMS/HSM/secret manager and inject it as an environment secret. The included `.env` support is for deployment convenience, not a substitute for key management.

The sweep worker signs blockchain transactions. Test it on BSC testnet or with a tiny operational balance before using real funds.

## What is included

- Google ID-token authentication; no password field is used.
- JWT access/refresh tokens.
- Automatic wallet assignment at user creation.
- 12-word BIP-39 root mnemonic.
- BIP-44 Ethereum derivation paths: `m/44'/60'/0'/0/index`.
- Central wallet at the configured central index.
- One unique deposit address per user.
- USDT BEP-20 `Transfer` log scanning with configurable confirmations.
- Idempotent blockchain deposit processing.
- Automatic collection of detected USDT from the user wallet to the central wallet.
- Optional BNB gas top-up from the central wallet before collection.
- Ledger records for detected deposits and sweeps.
- DRF + drf-spectacular Swagger UI and OpenAPI schema.
- Django admin.
- Health endpoint.
- No private keys are stored in the database; they are derived from the root mnemonic at runtime.

## API

Swagger UI: `/api/docs/`
OpenAPI JSON: `/api/schema/`

Endpoints:

- `POST /api/v1/auth/google/` — exchange a Google ID token for JWTs and create/return the user.
- `POST /api/v1/auth/token/refresh/` — refresh a JWT.
- `GET /api/v1/me/` — current user and wallet.
- `GET /api/v1/wallet/` — current deposit wallet.
- `GET /api/v1/deposits/` — current user's deposit ledger.
- `GET /api/v1/transactions/` — current user's blockchain transactions.
- `GET /health/` — health check.

The Swagger docs include request/response parameters and authentication requirements.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py generate_wallet_mnemonic
# Put the generated mnemonic into WALLET_MNEMONIC in .env.
python manage.py check
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
python manage.py runserver
```

Open `/api/docs/`.

## Google setup

Create a Google OAuth web client in Google Cloud Console and configure the client ID in `GOOGLE_CLIENT_ID`.
The frontend should obtain a Google Identity Services ID token and POST it to `/api/v1/auth/google/`:

```json
{
  "id_token": "<google-id-token>"
}
```

The backend verifies the token signature, audience, issuer, and expiry, then uses the verified email as the account identity.

## Blockchain worker

Run the deposit monitor separately from Gunicorn:

```bash
python manage.py monitor_deposits
```

The worker:

1. Reads the last scanned BSC block.
2. Scans USDT `Transfer` logs in batches.
3. Matches transfers whose `to` address belongs to a platform user wallet.
4. Waits for the configured confirmation count.
5. Creates an idempotent deposit transaction.
6. Sweeps the user wallet's USDT to the central wallet.
7. Optionally tops up BNB gas first.

For production, run the worker under systemd/supervisor and give the process a restricted OS account.

## Systemd example

Copy and adapt `deploy/akagiftbot-web.service` and `deploy/akagiftbot-worker.service`.

## SQLite production note

SQLite is fine for a small single-process MVP and the requested deployment shape. For higher write concurrency (especially blockchain monitoring + admin/API writes), migrate to PostgreSQL before scaling horizontally.

## Source requirements alignment

The supplied system design calls for email authentication, a dedicated USDT BEP-20 deposit address, Alchemy/blockchain monitoring, confirmation/reconciliation before crediting, idempotent payment processing, a wallet/transaction ledger, and central-wallet accounting. Those requirements are reflected in this MVP implementation. fileciteturn0file0L70-L87 fileciteturn0file0L201-L224
