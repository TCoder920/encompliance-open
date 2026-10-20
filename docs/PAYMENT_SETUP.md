# Stripe Payment Setup Guide

## Overview

This guide covers Stripe payment integration for both **development** and **production** environments. The key difference is how webhooks are handled.

## 🚨 Critical Requirements

### For Development (Local)
**The Stripe CLI webhook listener MUST be running** - this is the most common cause of payment failures.

### For Production
**Stripe webhooks must be configured** to point to your live server endpoint.

---

## Development Setup

### Quick Start (Recommended)

Use the provided development script that starts both the backend and webhook listener:

```bash
cd encompliance-backend
./start_dev.sh
```

### Manual Setup

If you prefer to run components separately:

#### Terminal 1 - Stripe Webhook Listener:
```bash
stripe listen --forward-to localhost:8000/api/v1/payments/webhook
```

**Important:** Copy the webhook signing secret from the output:
```
> Ready! Your webhook signing secret is whsec_xxxxx...
```

#### Terminal 2 - Update Environment Variables:
Add the webhook secret to your `.env` file:
```bash
echo "STRIPE_WEBHOOK_SECRET=whsec_xxxxx..." >> .env
```

#### Terminal 3 - Backend Server:
```bash
cd encompliance-backend
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**⚠️ IMPORTANT:** Restart the backend server after adding the webhook secret to `.env`

---

## Production Setup

### 1. Stripe Dashboard Configuration

1. Go to [Stripe Dashboard > Webhooks](https://dashboard.stripe.com/webhooks)
2. Click "Add endpoint"
3. Set endpoint URL: `https://yourdomain.com/api/v1/payments/webhook`
4. Select events to send:
   - `checkout.session.completed` (required)
   - `customer.created`
   - `customer.updated`
   - `invoice.created`
   - `invoice.finalized`
   - `invoice.paid`
   - `invoice.payment_succeeded`
   - `customer.subscription.created`

### 2. Environment Variables

Set these in your production environment:

```bash
# Production Stripe Keys (live keys, not test keys)
STRIPE_SECRET_KEY=sk_live_xxxxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxxxx

# Webhook secret from Stripe Dashboard
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# Product/Price IDs (use live IDs, not test IDs)
STRIPE_PRO_BASE_PRICE_ID=price_xxxxx
STRIPE_USER_SEAT_PRICE_ID=price_xxxxx
```

### 3. SSL Certificate Required

Stripe requires HTTPS for production webhooks. Ensure your server has a valid SSL certificate.

---

## Common Issues & Solutions

### Issue 1: User paid but account not upgraded

**Symptoms:**
- Payment succeeds on Stripe checkout
- User sees success message
- Account remains "free" status
- OpenAI logs show "Using model gpt-4.1-nano for user X based on subscription status free"

**Causes & Solutions:**

#### Development:
1. **Webhook listener not running**
   ```bash
   # Check if running
   ps aux | grep "stripe listen"
   
   # Start if not running
   stripe listen --forward-to localhost:8000/api/v1/payments/webhook
   ```

2. **Missing or incorrect webhook secret**
   ```bash
   # Check .env file
   grep STRIPE_WEBHOOK_SECRET .env
   
   # Should match webhook listener output
   # If missing or wrong, update and restart backend
   ```

3. **Backend not restarted after adding webhook secret**
   - Always restart backend server after updating `.env`

#### Production:
1. **Webhook endpoint not configured in Stripe Dashboard**
2. **Incorrect webhook URL** (must be HTTPS)
3. **Wrong webhook secret** in environment variables

### Issue 2: All webhooks return 400 errors

**Symptoms:**
- Webhook listener shows: `<-- [400] POST http://localhost:8000/api/v1/payments/webhook`
- Backend logs show signature verification failures

**Solution:**
- Check `.env` file formatting - ensure `STRIPE_WEBHOOK_SECRET` is on its own line
- Restart backend server after fixing `.env`

### Issue 3: 400 Error during payment confirmation

**Symptoms:**
- Payment fails at Stripe checkout with 400 error
- Error about automatic tax

**Solution:**
- Disable automatic tax in `payments.py` (already implemented)
- Ensure test price IDs are used in development

### Issue 4: "Manage Subscription" button causes 400 error

**Symptoms:**
- User clicks "Manage Subscription" in settings
- 400 error: "No Stripe customer found for this facility"

**Cause:**
- User was manually upgraded without proper Stripe customer/subscription setup

**Solution:**
- Only show "Manage Subscription" for users with valid Stripe setup
- For testing, use actual payment flow instead of manual upgrades

---

## Verification & Testing

### Successful Webhook Processing

When webhooks work correctly, you'll see:

**Webhook Listener:**
```
2025-06-07 19:26:39   --> checkout.session.completed [evt_xxxxx]
2025-06-07 19:26:40  <--  [200] POST http://localhost:8000/api/v1/payments/webhook
```

**Backend Logs:**
```
INFO: Processing checkout.session.completed webhook
INFO: User upgraded to pro subscription
INFO: Facility created for user
```

### Test Payment Flow

1. **Sign up** for new account
2. **Verify email** 
3. **Complete payment** on Stripe checkout
4. **Verify upgrade:**
   - User status shows "Pro"
   - Facility is created
   - OpenAI logs show "Using model gpt-4o for user X based on subscription status pro"

### Manual Webhook Testing

Trigger test webhooks:
```bash
stripe trigger checkout.session.completed
```

---

## Environment Variables Reference

### Required for All Environments:
```bash
# Stripe API Keys
STRIPE_SECRET_KEY=sk_test_xxxxx  # Use sk_live_ for production
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxx  # Use pk_live_ for production

# Webhook Secret (from CLI listener or Stripe Dashboard)
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# Product/Price IDs
STRIPE_PRO_BASE_PRICE_ID=price_xxxxx
STRIPE_USER_SEAT_PRICE_ID=price_xxxxx
```

### Development vs Production:

| Environment | Keys | Webhook Source | HTTPS Required |
|-------------|------|----------------|----------------|
| Development | `sk_test_`, `pk_test_` | Stripe CLI | No |
| Production | `sk_live_`, `pk_live_` | Stripe Dashboard | Yes |

---

## Debugging Commands

```bash
# Check webhook listener status
ps aux | grep "stripe listen"

# Check environment variables
grep STRIPE_ .env

# Test webhook endpoint manually
curl -X POST http://localhost:8000/api/v1/payments/webhook \
  -H "Content-Type: application/json" \
  -d '{"test": true}'

# View recent Stripe events
stripe events list --limit 10

# Check database user status
sqlite3 app.db "SELECT id, email, subscription_status, user_role FROM users WHERE id = X;"
```

---

## Production Deployment Checklist

- [ ] Live Stripe keys configured
- [ ] Webhook endpoint added in Stripe Dashboard
- [ ] HTTPS certificate installed
- [ ] Environment variables set correctly
- [ ] Test payment flow end-to-end
- [ ] Monitor webhook delivery in Stripe Dashboard
- [ ] Set up webhook failure alerts 