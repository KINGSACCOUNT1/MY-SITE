# 🚀 Complete Migration Guide: Old Render → New Render Account

## 📋 Overview

Migrating Elite Wealth Capital from old Render account to new Render account (KINGSACCOUNT1) with complete database backup and restoration.

---

## ⚙️ Pre-Migration Setup

### ✅ What's Already Done
- ✅ GitHub repository transferred to KINGSACCOUNT1
- ✅ Local git remote updated to KINGSACCOUNT1/MY-SITE
- ✅ Email credentials updated (Zoho app password: eAXHqJSWHGvM)
- ✅ All environment variables documented
- ✅ Backup scripts created
- ✅ New Render blueprint prepared (render_new.yaml)

### 📊 Current Configuration

**Old Render Account:**
- Service: my-site (my-site-ghnp.onrender.com)
- Database: elite_wealth_capital (PostgreSQL - Oregon)
- Domain: elitewealthcapita.uk (currently pointing here)

**New Render Account:**
- Account: KINGSACCOUNT1
- GitHub Repo: https://github.com/KINGSACCOUNT1/MY-SITE
- Will create: elite-wealth-capital service
- Will create: elite-wealth-db database

---

## 🔄 STEP-BY-STEP MIGRATION PROCESS

### **PHASE 1: Backup Production Database** 

#### 1.1 Install Required Packages
```bash
cd "C:\Users\micha\OneDrive\Desktop\my w\MY-SITE"
pip install psycopg2-binary python-dotenv dj-database-url
```

#### 1.2 Run Production Backup
```bash
python backup_production_db.py
```

**Expected Output:**
```
🚀 PRODUCTION DATABASE BACKUP
Connected to production database
Exporting data...
✅ BACKUP COMPLETED SUCCESSFULLY!
File: backups/production_backup_20260502_HHMMSS.json
```

**What This Does:**
- Connects to old Render PostgreSQL database
- Exports ALL users, investments, deposits, KYC data, notifications
- Saves as JSON file in `backups/` folder
- Preserves all relationships and foreign keys

#### 1.3 Verify Backup
```bash
dir backups
# Should see: production_backup_YYYYMMDD_HHMMSS.json
```

---

### **PHASE 2: Deploy to New Render Account**

#### 2.1 Login to New Render Account
1. Go to: https://dashboard.render.com/
2. Login with KINGSACCOUNT1 credentials
3. Verify you're in the correct account

#### 2.2 Create New PostgreSQL Database

**Option A: Via Render Dashboard**
1. Click **"New +"** → **"PostgreSQL"**
2. **Name:** `elite-wealth-db`
3. **Database:** `elite_wealth_capital`
4. **User:** `elite_admin`
5. **Region:** Oregon
6. **Plan:** Starter (Free)
7. Click **"Create Database"**
8. Wait 2-3 minutes for provisioning
9. **Copy the Internal Database URL** (starts with `postgresql://`)

**Option B: Via Blueprint (Automatic)**
- Skip this step, database will be created in next step

#### 2.3 Deploy Web Service from Blueprint

**Manual Method:**
1. Click **"New +"** → **"Blueprint"**
2. Connect GitHub repository: `KINGSACCOUNT1/MY-SITE`
3. Select branch: `main`
4. Render detects `render_new.yaml`
5. Review configuration:
   - Service: elite-wealth-capital
   - Database: elite-wealth-db
   - All environment variables loaded
6. Click **"Apply"**
7. Wait 5-10 minutes for deployment

**Alternative - Import render_new.yaml:**
1. Copy content of `render_new.yaml`
2. In Render Dashboard → Settings → Blueprint
3. Paste YAML content
4. Click Save & Deploy

#### 2.4 Get New Service URL
- Note the new URL: `elite-wealth-capital-XXXX.onrender.com`
- Service will initially show errors (no data yet)

---

### **PHASE 3: Restore Database to New Deployment**

#### 3.1 Update .env for New Database

Get the new DATABASE_URL from Render dashboard (Database → Connection Info → Internal URL)

```bash
# Edit .env temporarily (for restore only)
DATABASE_URL=postgresql://new_user:new_password@new_host/elite_wealth_capital
```

#### 3.2 Test Connection
```bash
python manage.py check --database=default
```

Should show: `System check identified no issues`

#### 3.3 Run Database Restore
```bash
# List available backups
python restore_production_db.py

# Restore specific backup
python restore_production_db.py backups/production_backup_20260502_XXXXXX.json
```

**Interactive Prompts:**
```
⚠️  WARNING: This will overwrite existing data!
Continue? (yes/no): yes
```

**Expected Output:**
```
🔄 Running migrations...
✅ Migrations completed
📦 Loading data from backup...
✅ RESTORATION COMPLETED SUCCESSFULLY!
```

#### 3.4 Verify Restoration

**Test 1: Check Admin Login**
1. Go to: `https://elite-wealth-capital-XXXX.onrender.com/admin/`
2. Login with admin credentials
3. Verify users, investments, deposits appear

**Test 2: Check User Counts**
```bash
python manage.py shell
```
```python
from accounts.models import CustomUser
from investments.models import Deposit, Investment

print(f"Users: {CustomUser.objects.count()}")
print(f"Deposits: {Deposit.objects.count()}")
print(f"Investments: {Investment.objects.count()}")
```

---

### **PHASE 4: Domain Configuration**

#### 4.1 Add Custom Domain in Render
1. Go to new service → **Settings** → **Custom Domains**
2. Click **"Add Custom Domain"**
3. Add domains:
   - `elitewealthcapita.uk`
   - `www.elitewealthcapita.uk`
4. Render will show DNS instructions

#### 4.2 Update DNS Records

**Your Domain Registrar (where you bought elitewealthcapita.uk):**

**Delete Old Records:**
```
Type  | Name | Value
------|------|------
A     | @    | [old Render IP] ← DELETE
A     | www  | [old Render IP] ← DELETE
```

**Add New Records:**
Render will provide these values. Typically:
```
Type  | Name | Value                     | TTL
------|------|---------------------------|-----
A     | @    | [New Render IP]           | 3600
CNAME | www  | elitewealthcapita.uk      | 3600
```

Or if Render provides CNAME for apex:
```
Type  | Name | Value                                      | TTL
------|------|--------------------------------------------|-----
ALIAS | @    | elite-wealth-capital-XXXX.onrender.com    | 3600
CNAME | www  | elite-wealth-capital-XXXX.onrender.com    | 3600
```

#### 4.3 Wait for DNS Propagation
- Takes 5 minutes to 48 hours (usually < 1 hour)
- Check status: https://dnschecker.org/#A/elitewealthcapita.uk
- Render will auto-provision SSL certificate when DNS propagates

#### 4.4 Verify SSL Certificate
1. In Render Dashboard → Custom Domains
2. Wait for "Certificate Status: Active"
3. Test: https://elitewealthcapita.uk (should show green lock)

---

### **PHASE 5: Post-Migration Testing**

#### 5.1 Test Critical Features

**✅ User Authentication:**
- [ ] Login with existing user
- [ ] Password recovery works
- [ ] New user signup works
- [ ] Admin panel accessible

**✅ Email Notifications:**
- [ ] Create test user → admin receives email with credentials
- [ ] Make test deposit → admin receives deposit notification
- [ ] Confirm deposit → user receives confirmation email

**✅ Deposits & Withdrawals:**
- [ ] Create deposit request
- [ ] Upload screenshot
- [ ] Admin can verify/reject
- [ ] Balance updates correctly

**✅ Investments:**
- [ ] View investment plans
- [ ] Create investment
- [ ] Track ROI calculations

**✅ Media Uploads:**
- [ ] Profile picture upload (uses Cloudinary)
- [ ] KYC document upload
- [ ] Images display correctly

#### 5.2 Performance Check
- [ ] Homepage loads < 2 seconds
- [ ] Dashboard responsive
- [ ] Database queries optimized
- [ ] Static files served correctly

---

### **PHASE 6: Old Deployment Cleanup** ⚠️

**DO THIS LAST - AFTER VERIFYING NEW DEPLOYMENT WORKS!**

#### 6.1 Deactivate Old Service
1. Go to old Render account
2. Settings → Suspend Service
3. Keep database active for 7 days (backup period)

#### 6.2 Final Backup Check
```bash
# Keep backups folder
# Create additional backup just in case
python backup_production_db.py
```

#### 6.3 Delete Old Resources (After 7 Days)
1. Old Render Service → Settings → Delete Service
2. Old Database → Settings → Delete Database
3. Confirm all data is working on new deployment

---

## 🔧 Troubleshooting

### Issue: Backup Script Fails
**Error:** `Connection refused`
- Check if DATABASE_URL is correct
- Verify Render database is still active
- Check firewall/network settings

**Fix:**
```bash
# Test connection manually
psql "postgresql://elite_admin_acc:ENIIWPFknHA5m4XQREVRymlVq8QhVSRI@dpg-d73r90qdbo4c738iabug-a.oregon-postgres.render.com/elite_wealth_capital"
```

### Issue: Restore Fails
**Error:** `Foreign key constraint violated`
- Run migrations first: `python manage.py migrate`
- Use `--natural-foreign` flag (already in script)

**Error:** `Model doesn't exist`
- Ensure all apps are in INSTALLED_APPS
- Run migrations before restore

### Issue: Domain Not Working
**DNS not propagating:**
- Wait longer (up to 48 hours)
- Clear browser cache: Ctrl+Shift+Delete
- Try incognito mode
- Check DNS: `nslookup elitewealthcapita.uk`

**SSL certificate pending:**
- Wait for DNS to propagate first
- Render auto-provisions SSL after DNS works
- Can take 10-30 minutes after DNS is live

### Issue: Email Notifications Not Sending
**Check environment variables:**
```bash
# In Render Dashboard → Environment
EMAIL_HOST_PASSWORD=eAXHqJSWHGvM  # Correct password?
EMAIL_HOST_USER=admin@elitewealthcapita.uk
```

**Test email:**
```python
python manage.py shell
from django.core.mail import send_mail
send_mail('Test', 'Test message', 'admin@elitewealthcapita.uk', ['admin@elitewealthcapita.uk'])
```

### Issue: Static Files Not Loading
**Check build logs:**
- Look for `collectstatic` command
- Verify WhiteNoise is installed

**Manual fix:**
```bash
python manage.py collectstatic --noinput
```

---

## 📊 Migration Checklist

### Before Migration
- [x] GitHub repo transferred to KINGSACCOUNT1
- [x] Local git updated
- [x] Backup scripts created
- [x] New render_new.yaml prepared
- [x] Environment variables updated

### During Migration
- [ ] Production database backed up
- [ ] Backup file verified (JSON exists in backups/)
- [ ] New Render account accessed
- [ ] PostgreSQL database created
- [ ] Web service deployed from blueprint
- [ ] Database restored successfully
- [ ] Admin login verified

### Post-Migration
- [ ] Domain DNS updated
- [ ] SSL certificate active
- [ ] All features tested
- [ ] Email notifications working
- [ ] Old deployment documented
- [ ] Team notified of new URLs

---

## 🆘 Emergency Rollback Plan

If new deployment has critical issues:

### 1. Revert DNS
- Change DNS back to old Render IP
- Wait for propagation

### 2. Keep Old Service Active
- Don't delete old Render service until 100% confident
- Keep for at least 7 days after migration

### 3. Data Sync
- If users created accounts on new deployment during testing
- Backup new deployment database
- Merge with old database (manual process)

---

## 📞 Support Resources

**Render Documentation:**
- https://render.com/docs
- https://render.com/docs/databases
- https://render.com/docs/custom-domains

**Django Documentation:**
- https://docs.djangoproject.com/en/4.2/ref/django-admin/#loaddata
- https://docs.djangoproject.com/en/4.2/ref/django-admin/#dumpdata

**DNS Tools:**
- https://dnschecker.org
- https://www.whatsmydns.net

---

## ✅ Success Criteria

Migration is successful when:
- ✅ https://elitewealthcapita.uk loads (with SSL)
- ✅ All users can login with existing passwords
- ✅ All deposits/investments data visible
- ✅ Admin receives email notifications
- ✅ New signups work correctly
- ✅ Deposit verification process works
- ✅ No data loss confirmed

---

## 🎉 Post-Migration

Once migration is complete:
1. Announce new deployment to team
2. Monitor for 24 hours for issues
3. Keep old deployment suspended for 7 days
4. Delete old resources after verification period
5. Update any documentation with new URLs
6. Celebrate successful migration! 🎊
