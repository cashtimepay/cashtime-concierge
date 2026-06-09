# Cloud IAP setup — judge access

Both Cloud Run services are deployed with `--no-allow-unauthenticated`. Access
for the judging window (2026-06-11 → 2026-06-22) is granted through Cloud IAP +
a global external HTTPS load balancer, so judges sign in with a single Google
account and never see our internal network.

## Topology

```
judge → IAP (Google sign-in) → HTTPS LB → Serverless NEG → Cloud Run
                                              ├── cashtime-concierge-ui   (concierge.cashtimepay.com)
                                              └── cashtime-concierge      (concierge-api.cashtimepay.com)
```

## One-time setup

1. **OAuth consent + IAP brand** (once per project):
   ```bash
   gcloud iap oauth-brands create \
     --application_title="CashTime Brand Concierge" \
     --support_email="dmitry@cashtimepay.com" --project tools-cashtimepay-com
   ```

2. **Serverless NEGs** for each service (region europe-west6):
   ```bash
   gcloud compute network-endpoint-groups create concierge-ui-neg \
     --region=europe-west6 --network-endpoint-type=serverless \
     --cloud-run-service=cashtime-concierge-ui --project tools-cashtimepay-com
   gcloud compute network-endpoint-groups create concierge-api-neg \
     --region=europe-west6 --network-endpoint-type=serverless \
     --cloud-run-service=cashtime-concierge --project tools-cashtimepay-com
   ```

3. **Backend services with IAP enabled**, URL map, target HTTPS proxy, managed
   cert for `concierge.cashtimepay.com` + `concierge-api.cashtimepay.com`, and a
   global forwarding rule. (Standard LB wiring — see Google's "Serverless +
   external HTTPS LB + IAP" guide.)

4. **Grant the judge tester account** IAP access (read-only entry):
   ```bash
   gcloud iap web add-iam-policy-binding \
     --resource-type=backend-services --service=concierge-ui-backend \
     --member="user:JUDGE_TESTER@gmail.com" \
     --role="roles/iap.httpsResourceAccessor" --project tools-cashtimepay-com
   ```
   The tester account is provisioned just before submission and **revoked on
   2026-06-22**. Credentials are entered in the Devpost "Testing access" field,
   never committed.

## Health check (no auth)

`/healthz` on the concierge service is reachable without IAP via the LB's
unauthenticated path matcher, so judges can confirm the service is live before
signing in:

```
GET https://concierge-api.cashtimepay.com/healthz  →  {"status":"ok"}
```

## Teardown after judging

```bash
gcloud iap web remove-iam-policy-binding ... --member="user:JUDGE_TESTER@gmail.com" ...
```
