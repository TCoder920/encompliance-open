# Usage-Based Billing RFC

## Objective
Introduce metered AI billing for enterprise tenants with Stripe usage records. The goal is to provide transparent token tracking, an admin-visible dashboard, and automated invoicing hooks.

## Architecture
1. **Measurement**: `ai_usage_logs` captures user/token metadata per request. Each LLM interaction writes `tokens_used` and `cost_usd`.
2. **Aggregation Service**: `UsageBillingService` summarizes usage per month and exposes `/usage-billing/summary`.
3. **Stripe Integration (Phase 2)**:
   - Nightly job reads aggregated totals and pushes to Stripe usage records.
   - Webhook ensures reconciliation.
4. **Frontend Dashboard**: New `/usage-billing` route (next iteration) will visualize token trends and alert administrators when thresholds are exceeded.

## Milestones
1. **M1 (Current)**: Logging + summary endpoint.
2. **M2**: Add alerting + frontend dashboard.
3. **M3**: Stripe usage-based pricing integration with automated invoicing.

