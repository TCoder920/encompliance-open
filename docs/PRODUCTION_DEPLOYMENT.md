# Production Deployment Guide

## Overview

This guide covers deploying EnCompliance to production with proper Stripe payment integration.

## 🚨 Critical Production Requirements

1. **HTTPS Certificate** - Required for Stripe webhooks
2. **Live Stripe Keys** - Switch from test to live keys
3. **Webhook Endpoint** - Configure in Stripe Dashboard
4. **Environment Variables** - Secure configuration
5. **Database Migration** - Production database setup

---

## Pre-Deployment Checklist

### 1. Stripe Configuration

#### Switch to Live Mode
1. Go to [Stripe Dashboard](https://dashboard.stripe.com)
2. Toggle from "Test mode" to "Live mode" (top right)
3. Generate live API keys:
   - **Publishable key**: `pk_live_...`
   - **Secret key**: `sk_live_...`

#### Create Live Products/Prices
1. Navigate to Products in Stripe Dashboard
2. Create live versions of your test products:
   - **Pro Base Subscription**: Note the `price_live_...` ID
   - **User Seat Add-on**: Note the `price_live_...` ID

#### Configure Webhook Endpoint
1. Go to **Developers > Webhooks**
2. Click **"Add endpoint"**
3. Set endpoint URL: `https://yourdomain.com/api/v1/payments/webhook`
4. Select events to send:
   ```
   ✅ checkout.session.completed
   ✅ customer.created
   ✅ customer.updated
   ✅ invoice.created
   ✅ invoice.finalized
   ✅ invoice.paid
   ✅ invoice.payment_succeeded
   ✅ customer.subscription.created
   ```
5. **Save the webhook signing secret** (starts with `whsec_`)

### 2. SSL Certificate

Stripe requires HTTPS for production webhooks. Options:

#### Option A: Let's Encrypt (Free)
```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### Option B: Cloud Provider SSL
- **AWS**: Use Application Load Balancer with ACM certificate
- **Cloudflare**: Enable SSL/TLS encryption
- **DigitalOcean**: Use Load Balancer with managed certificate

### 3. Environment Variables

Create production `.env` file:

```bash
# Production Database
DATABASE_URL=postgresql://user:password@localhost/encompliance_prod

# JWT Security (Generate new secrets!)
JWT_SECRET_KEY=your_production_jwt_secret_256_bits_minimum
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Admin Security
ADMIN_SECRET_KEY=your_production_admin_secret_256_bits_minimum
ADMIN_ALGORITHM=HS256
ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES=60

# Email Configuration
SMTP_HOST=your-smtp-server.com
SMTP_PORT=587
SMTP_TLS=True
SMTP_USER=noreply@yourdomain.com
SMTP_PASSWORD=your_smtp_password
EMAILS_FROM_EMAIL=noreply@yourdomain.com
EMAILS_FROM_NAME=YourApp Support
SUPPORT_EMAIL=support@yourdomain.com

# WebAuthn (Update for production domain)
WEBAUTHN_RP_ID=yourdomain.com
WEBAUTHN_RP_NAME=YourApp
WEBAUTHN_RP_ORIGIN=https://yourdomain.com
WEBAUTHN_TIMEOUT=60000

# OpenAI
OPENAI_API_KEY=sk-proj-your_production_openai_key

# Stripe LIVE Keys (⚠️ LIVE KEYS - NOT TEST!)
STRIPE_SECRET_KEY=sk_live_your_live_secret_key
STRIPE_PUBLISHABLE_KEY=pk_live_your_live_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_signing_secret

# Stripe LIVE Product/Price IDs
STRIPE_PRO_BASE_PRICE_ID=price_live_your_pro_price_id
STRIPE_USER_SEAT_PRICE_ID=price_live_your_seat_price_id

# Push Notifications
VAPID_PRIVATE_KEY=your_vapid_private_key
VAPID_PUBLIC_KEY=your_vapid_public_key
VAPID_EMAIL=mailto:support@yourdomain.com
```

---

## Deployment Steps

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3 python3-pip python3-venv nginx postgresql postgresql-contrib

# Create application user
sudo useradd -m -s /bin/bash encompliance
sudo su - encompliance

# Clone repository
git clone https://github.com/yourusername/encompliance-project.git
cd encompliance-project/encompliance-backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Create PostgreSQL database
sudo -u postgres createdb encompliance_prod
sudo -u postgres createuser encompliance_user
sudo -u postgres psql -c "ALTER USER encompliance_user PASSWORD 'secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE encompliance_prod TO encompliance_user;"

# Run migrations
alembic upgrade head
```

### 3. Application Configuration

```bash
# Copy environment file
cp .env.example .env
# Edit .env with production values (see above)

# Test application
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Process Manager (Systemd)

Create `/etc/systemd/system/encompliance.service`:

```ini
[Unit]
Description=EnCompliance Backend
After=network.target

[Service]
Type=simple
User=encompliance
WorkingDirectory=/home/encompliance/encompliance-project/encompliance-backend
Environment=PATH=/home/encompliance/encompliance-project/encompliance-backend/venv/bin
ExecStart=/home/encompliance/encompliance-project/encompliance-backend/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable encompliance
sudo systemctl start encompliance
sudo systemctl status encompliance
```

### 5. Nginx Configuration

Create `/etc/nginx/sites-available/encompliance`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL Configuration (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Admin interface
    location /admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend (if serving from same domain)
    location / {
        root /var/www/encompliance-frontend/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/encompliance /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Post-Deployment Verification

### 1. Test Webhook Endpoint

```bash
# Test webhook endpoint is accessible
curl -X POST https://yourdomain.com/api/v1/payments/webhook \
  -H "Content-Type: application/json" \
  -d '{"test": true}'

# Should return 400 (signature verification failed) - this is expected
```

### 2. Stripe Webhook Testing

1. Go to **Stripe Dashboard > Webhooks**
2. Click on your webhook endpoint
3. Click **"Send test webhook"**
4. Select `checkout.session.completed`
5. Verify it shows successful delivery (200 response)

### 3. End-to-End Payment Test

1. Create test account on production site
2. Verify email works
3. Complete payment flow with real card (small amount)
4. Verify account upgrades to Pro
5. Check Stripe Dashboard for successful payment

### 4. Monitor Webhook Delivery

In Stripe Dashboard:
1. Go to **Webhooks > Your endpoint**
2. Monitor **"Recent deliveries"**
3. Check for any failed deliveries
4. Set up alerts for webhook failures

---

## Monitoring & Maintenance

### 1. Log Monitoring

```bash
# Application logs
sudo journalctl -u encompliance -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Database logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

### 2. Health Checks

Create monitoring script `/home/encompliance/health_check.sh`:

```bash
#!/bin/bash

# Check application health
curl -f http://localhost:8000/health || echo "Backend down"

# Check database connection
python3 -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://user:pass@localhost/encompliance_prod')
    print('Database OK')
except:
    print('Database ERROR')
"

# Check Stripe webhook endpoint
curl -f https://yourdomain.com/api/v1/payments/webhook || echo "Webhook endpoint down"
```

### 3. Backup Strategy

```bash
# Database backup
pg_dump encompliance_prod > backup_$(date +%Y%m%d_%H%M%S).sql

# Automated daily backups
echo "0 2 * * * pg_dump encompliance_prod > /backups/db_$(date +\%Y\%m\%d).sql" | crontab -
```

### 4. SSL Certificate Renewal

```bash
# Test renewal
sudo certbot renew --dry-run

# Automatic renewal (already set up with Let's Encrypt)
sudo crontab -l | grep certbot
```

---

## Troubleshooting Production Issues

### Webhook Failures

1. **Check Stripe Dashboard**: Look for failed webhook deliveries
2. **Verify SSL**: Ensure certificate is valid and not expired
3. **Check logs**: `sudo journalctl -u encompliance -f`
4. **Test endpoint**: Use curl to verify webhook URL is accessible

### Payment Issues

1. **Check Stripe logs**: Dashboard > Logs
2. **Verify live keys**: Ensure using `sk_live_` and `pk_live_`
3. **Check product IDs**: Ensure using live price IDs
4. **Monitor webhook events**: Verify `checkout.session.completed` is being received

### Performance Issues

1. **Database optimization**: Add indexes, analyze queries
2. **Connection pooling**: Configure PostgreSQL connection limits
3. **Caching**: Implement Redis for session storage
4. **Load balancing**: Use multiple application instances

---

## Security Considerations

### 1. Environment Variables
- Never commit `.env` to version control
- Use secure secrets (256-bit minimum)
- Rotate secrets regularly

### 2. Database Security
- Use strong passwords
- Enable SSL connections
- Regular security updates

### 3. API Security
- Rate limiting
- Input validation
- CORS configuration
- Regular dependency updates

### 4. Stripe Security
- Webhook signature verification (already implemented)
- Use live keys only in production
- Monitor for suspicious activity
- Enable Stripe Radar for fraud detection

---

## Rollback Plan

If deployment fails:

1. **Revert to previous version**:
   ```bash
   git checkout previous-stable-tag
   sudo systemctl restart encompliance
   ```

2. **Database rollback**:
   ```bash
   # Restore from backup
   psql encompliance_prod < backup_YYYYMMDD_HHMMSS.sql
   ```

3. **Nginx rollback**:
   ```bash
   # Revert to previous configuration
   sudo systemctl reload nginx
   ```

4. **Stripe webhook**:
   - Update webhook URL in Stripe Dashboard if needed
   - Verify webhook deliveries are working 