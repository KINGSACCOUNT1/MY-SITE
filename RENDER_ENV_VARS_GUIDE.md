# 🔐 Environment Variables for Render Deployment

## ✅ QUICK REFERENCE: What to Fill in Render Form

Based on your `.env.example` file, here's what you need:

---

## 📋 REQUIRED NOW (Fill in Render Blueprint Form):

### **1. Branch Name**
```
Change: master → main
```

### **2. EMAIL_HOST_PASSWORD**
```
Value: Your actual Zoho/Gmail app password
Source: EMAIL_HOST_PASSWORD from your .env file
```

### **3. BYBIT_API_KEY**
```
Value: Your Bybit API key
Source: BYBIT_API_KEY from your .env file
```

### **4. BYBIT_API_SECRET**
```
Value: Your Bybit API secret
Source: BYBIT_API_SECRET from your .env file
```

### **5. CELERY_BROKER_URL**
```
Value: Your Redis URL
Options:
  - Get free Redis from: https://upstash.com (10k commands/day)
  - Or create Render Redis (free tier)
  - Format: redis://default:password@host:port
Source: CELERY_BROKER_URL from your .env (update with real Redis URL)
```

### **6. CELERY_RESULT_BACKEND**
```
Value: Same as CELERY_BROKER_URL
Just copy the Redis URL from above
```

---

## 🔐 ADD THESE AFTER DEPLOYMENT (In Dashboard):

Once your site is live, go to Dashboard → Environment tab and add:

### **Payment Gateways:**

**STRIPE_SECRET_KEY**
```
Value: sk_live_... or sk_test_...
Source: STRIPE_SECRET_KEY from your .env
```

**STRIPE_PUBLISHABLE_KEY**
```
Value: pk_live_... or pk_test_...
Source: STRIPE_PUBLIC_KEY from your .env
```

**STRIPE_WEBHOOK_SECRET** (optional)
```
Value: whsec_...
Source: STRIPE_WEBHOOK_SECRET from your .env
```

**PAYPAL_CLIENT_ID**
```
Value: Your PayPal client ID
Source: PAYPAL_CLIENT_ID from your .env
```

**PAYPAL_SECRET**
```
Value: Your PayPal secret
Source: PAYPAL_CLIENT_SECRET from your .env
```

**PAYPAL_MODE**
```
Value: sandbox or live
Source: PAYPAL_MODE from your .env
```

**COINBASE_COMMERCE_API_KEY**
```
Value: Your Coinbase Commerce key
Source: COINBASE_COMMERCE_API_KEY from your .env
```

**COINBASE_COMMERCE_WEBHOOK_SECRET** (optional)
```
Value: Your webhook secret
Source: COINBASE_COMMERCE_WEBHOOK_SECRET from your .env
```

---

## ⚠️ VARIABLES ALREADY SET BY render.yaml:

These are auto-configured by Render (don't add them):

- ✅ DATABASE_URL (auto-generated)
- ✅ SECRET_KEY (auto-generated)
- ✅ DEBUG (set to False)
- ✅ ALLOWED_HOSTS (already configured)
- ✅ PYTHON_VERSION (set to 3.12.0)
- ✅ EMAIL_HOST (smtp.zoho.com)
- ✅ EMAIL_PORT (587)
- ✅ EMAIL_HOST_USER (admin@elitewealthcapita.uk)
- ✅ DEFAULT_FROM_EMAIL (noreply@elitewealthcapita.uk)
- ✅ ADMIN_NOTIFICATION_EMAIL (admin@elitewealthcapita.uk)

---

## 🚀 DEPLOYMENT STEPS:

### **Step 1: Fill Required Variables**
In the Blueprint form on Render:
1. Change branch: `master` → `main`
2. Fill: `EMAIL_HOST_PASSWORD`
3. Fill: `BYBIT_API_KEY`
4. Fill: `BYBIT_API_SECRET`
5. Fill: `CELERY_BROKER_URL` (get from Upstash or leave blank temporarily)
6. Fill: `CELERY_RESULT_BACKEND` (same as above)

### **Step 2: Deploy**
Click **"Deploy Blueprint"** button

### **Step 3: Wait**
~10 minutes for first deployment

### **Step 4: Add Payment Variables**
After site is live:
1. Go to Dashboard → `elite-wealth-capita` service
2. Click **Environment** tab
3. Click **Add Environment Variable**
4. Add Stripe, PayPal, Coinbase keys
5. Click **Save Changes** → Auto-redeploys

---

## 💡 PRO TIPS:

### **Don't Have Redis Yet?**
- **Option 1:** Get free Redis from https://upstash.com
  - 10,000 commands/day free
  - TLS connection (secure)
  - Copy the `UPSTASH_REDIS_REST_URL`
  
- **Option 2:** Create Render Redis
  - Dashboard → New+ → Redis
  - Free plan available
  - Copy connection string

### **Don't Have Payment Keys Yet?**
- Leave them blank
- Site will work without payments
- Add them when you're ready to go live with payments

### **Test Mode vs Live Mode:**
- Use test keys for testing (`sk_test_...`, `pk_test_...`)
- Switch to live keys when ready for production
- Keep `PAYPAL_MODE=sandbox` for testing

---

## 🔒 SECURITY NOTES:

✅ **NEVER commit .env file** (already in .gitignore)  
✅ **Use app-specific passwords** for email (not your main password)  
✅ **Rotate keys regularly** (especially if exposed)  
✅ **Use test keys** for development  
✅ **Enable webhook security** for payment gateways  

---

## 📖 YOUR .ENV FILE STRUCTURE:

```bash
# Email (REQUIRED NOW)
EMAIL_HOST_PASSWORD=your-actual-password

# Bybit (REQUIRED NOW)
BYBIT_API_KEY=your-actual-key
BYBIT_API_SECRET=your-actual-secret

# Redis (REQUIRED NOW or get from Upstash)
CELERY_BROKER_URL=redis://default:password@host:port
CELERY_RESULT_BACKEND=redis://default:password@host:port

# Payment Gateways (ADD LATER)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLIC_KEY=pk_test_...
PAYPAL_CLIENT_ID=...
PAYPAL_CLIENT_SECRET=...
COINBASE_COMMERCE_API_KEY=...
```

---

## ✅ READY TO DEPLOY!

Just copy values from your `.env` file to the Render form and click Deploy!
