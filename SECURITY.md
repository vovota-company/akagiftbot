# Security checklist

- Do not commit `.env` or the BIP-39 mnemonic.
- Prefer KMS/HSM/secret-manager injection for `WALLET_MNEMONIC` in production.
- The mnemonic is the root of every user deposit wallet and the central wallet.
- Never expose private keys through REST endpoints.
- The API intentionally exposes only deposit addresses and transaction status.
- Use a dedicated BSC RPC endpoint with rate limits and monitoring.
- Start with BSC testnet or very small funds and verify sweep behavior.
- Keep the central wallet funded only with the BNB needed for operations plus a controlled reserve.
- Use an OS-level service account for the monitor worker.
- Restrict admin access and enable HTTPS.
- Back up the database and secret material separately.
- Review legal, tax, consumer-protection and financial requirements before handling customer funds.
