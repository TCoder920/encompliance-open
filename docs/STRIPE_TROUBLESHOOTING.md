# Stripe Payment Troubleshooting - Quick Reference

## 🚨 Most Common Issues

### Issue: User paid but account not upgraded

**Quick Check:**
```bash
# 1. Is webhook listener running?
ps aux | grep "stripe listen"

# 2. Check webhook secret in .env
grep STRIPE_WEBHOOK_SECRET .env

# 3. Check recent webhook events
stripe events list --limit 5
```

**Quick Fix:**
```bash
# Start webhook listener
stripe listen --forward-to localhost:8000/api/v1/payments/webhook

# Copy the webhook secret and add to .env
echo "STRIPE_WEBHOOK_SECRET=whsec_xxxxx" >> .env

# Restart backend server
# (Ctrl+C and restart uvicorn)
```

---

### Issue: All webhooks return 400 errors

**Symptoms:**
```
2025-06-07 19:23:29  <--  [400] POST http://localhost:8000/api/v1/payments/webhook
```

**Quick Fix:**
```bash
# Check .env file formatting
cat .env | grep STRIPE_WEBHOOK_SECRET

# Should be on its own line, not concatenated
# If wrong, fix and restart backend server
```

---

### Issue: Payment fails with 400 error at checkout

**Quick Fix:**
- Check that automatic tax is disabled in `payments.py`
- Verify using test price IDs in development
- Check Stripe Dashboard for error details

---

### Issue: "Manage Subscription" button causes 400 error

**Cause:** User was manually upgraded without Stripe customer setup

**Quick Fix:** Use actual payment flow instead of manual database updates

---

## 🔧 Quick Commands

### Check Status
```bash
# Webhook listener status
ps aux | grep "stripe listen"

# Backend server status
curl http://localhost:8000/health

# Recent Stripe events
stripe events list --limit 10

# User subscription status
sqlite3 app.db "SELECT id, email, subscription_status FROM users WHERE id = X;"
```

### Start Services
```bash
# Development (all-in-one)
./start_dev.sh

# Manual webhook listener
stripe listen --forward-to localhost:8000/api/v1/payments/webhook

# Backend server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Test Webhooks
```bash
# Trigger test webhook
stripe trigger checkout.session.completed

# Test webhook endpoint
curl -X POST http://localhost:8000/api/v1/payments/webhook \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```

---

## 📋 Environment Checklist

### Development
- [ ] `STRIPE_SECRET_KEY=sk_test_...`
- [ ] `STRIPE_PUBLISHABLE_KEY=pk_test_...`
- [ ] `STRIPE_WEBHOOK_SECRET=whsec_...` (from CLI)
- [ ] `STRIPE_PRO_BASE_PRICE_ID=price_...` (test price)
- [ ] Webhook listener running
- [ ] Backend server restarted after .env changes

### Production
- [ ] `STRIPE_SECRET_KEY=sk_live_...`
- [ ] `STRIPE_PUBLISHABLE_KEY=pk_live_...`
- [ ] `STRIPE_WEBHOOK_SECRET=whsec_...` (from Dashboard)
- [ ] `STRIPE_PRO_BASE_PRICE_ID=price_...` (live price)
- [ ] Webhook endpoint configured in Stripe Dashboard
- [ ] HTTPS certificate valid

---

## 🎯 Success Indicators

### Webhook Working Correctly
```
# Webhook listener shows 200 responses
2025-06-07 19:26:40  <--  [200] POST http://localhost:8000/api/v1/payments/webhook

# Backend logs show processing
INFO: Processing checkout.session.completed webhook
INFO: User upgraded to pro subscription

# User status updated in database
subscription_status: "pro"
user_role: "FACILITY_ADMIN"
```

### Payment Flow Working
1. ✅ User completes payment on Stripe checkout
2. ✅ Redirected to success page with "Welcome to Pro!" message
3. ✅ Account shows "Pro" status in settings
4. ✅ OpenAI logs show "Using model gpt-4o for user X based on subscription status pro"

---

## 📞 When to Contact Support

Contact Stripe support if:
- Webhook events are not being sent from Stripe
- Live payment processing issues
- Account verification problems
- Suspicious payment activity

Contact development team if:
- Backend application errors
- Database issues
- Custom webhook processing logic problems 