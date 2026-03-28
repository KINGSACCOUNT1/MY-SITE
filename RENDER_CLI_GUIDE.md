# 🚀 Render CLI - Complete Setup & Deployment Guide

## ✅ CLI IS INSTALLED!

Your Render CLI is working perfectly! Just need to configure it.

---

## 📋 STEP-BY-STEP SETUP:

### **Step 1: Initialize CLI Configuration**

Run this command (remove the extra backtick):
```powershell
render config init
```

**NOT:** `render login` (doesn't exist)  
**NOT:** `render config init`` (typo)

---

### **Step 2: Get Your API Key**

1. Visit: https://dashboard.render.com/u/settings/api
2. Click **"Create API Key"**
3. Name it: `CLI Access` (or whatever you prefer)
4. **Copy the generated key** (you'll only see it once!)

---

### **Step 3: Configure CLI**

When you run `render config init`, it will ask:

**Question 1: API Key**
```
? Render API Key: [paste your key here]
```

**Question 2: Profile Name**
```
? Profile name: (default) [just press Enter]
```

**Question 3: Default Region**
```
? Default region: oregon [or choose your preferred region]
```

---

## 🚀 DEPLOY YOUR SITE:

Once configured, you have TWO options:

### **OPTION 1: Use the Dashboard (Easier - Recommended)**

You're already on the Blueprint page! Just:
1. Change branch to `main`
2. Fill `EMAIL_HOST_PASSWORD`
3. Click **"Deploy Blueprint"**
4. Done in 10 minutes!

**Dashboard Advantage:** Visual interface, real-time logs, no commands needed

---

### **OPTION 2: Use CLI (Advanced)**

After `render config init`, run:

```powershell
cd E:\DailyFundzProfile\Desktop\my-elite

# Preview what will be created
render blueprint launch --preview

# Actually deploy
render blueprint launch
```

**CLI will:**
- Read your `render.yaml`
- Create database
- Create web service
- Deploy everything

---

## 📊 USEFUL CLI COMMANDS:

### **View Your Services:**
```powershell
render services list
```

### **View Service Logs:**
```powershell
render services logs elite-wealth-capita
```

### **Trigger Manual Deploy:**
```powershell
render services deploy elite-wealth-capita
```

### **View Service Details:**
```powershell
render services get elite-wealth-capita
```

### **Open Dashboard:**
```powershell
render dashboard
```

### **View Deployments:**
```powershell
render deploys list elite-wealth-capita
```

---

## 🔧 ENVIRONMENT VARIABLES:

### **Set via CLI:**
```powershell
render services env set elite-wealth-capita EMAIL_HOST_PASSWORD=your-password
render services env set elite-wealth-capita REDIS_URL=redis://your-redis-url
```

### **View Environment:**
```powershell
render services env list elite-wealth-capita
```

---

## 🎯 RECOMMENDED APPROACH:

Since you're already on the Blueprint deployment page in your browser:

### **BEST:** Use Dashboard NOW
1. You're at the right page
2. Just click a few buttons
3. Site live in 10 minutes
4. Use CLI later for updates

### **OR:** Use CLI
1. Run `render config init`
2. Get API key from Dashboard
3. Run `render blueprint launch`
4. Site deploys same way

**Both methods use the same `render.yaml` file!**

---

## 💡 CLI vs Dashboard:

| Feature | CLI | Dashboard |
|---------|-----|-----------|
| Initial Setup | Commands | Click buttons |
| API Key Required | Yes | No |
| View Logs | Terminal | Browser (better formatting) |
| Environment Vars | Commands | Visual editor |
| Metrics | Limited | Full graphs |
| Shell Access | No | Yes (interactive) |
| Best For | Automation, CI/CD | First deploy, monitoring |

---

## ⚠️ COMMON CLI ISSUES:

**Error: "API key invalid"**
- Generate new key in Dashboard
- Make sure you copied entire key

**Error: "Blueprint file not found"**
- Make sure you're in project directory
- Check `render.yaml` exists

**Error: "Branch not found"**
- Make sure branch is `main` not `master`
- Verify repo is pushed to GitHub

---

## 🎉 QUICK START (RIGHT NOW):

### **FASTEST:** Dashboard (you're already there!)
```
1. Change branch to "main"
2. Fill EMAIL_HOST_PASSWORD
3. Click "Deploy Blueprint"
4. ✅ DONE!
```

### **ALTERNATIVE:** CLI
```powershell
# Step 1: Configure
render config init
# (paste API key from https://dashboard.render.com/u/settings/api)

# Step 2: Navigate to project
cd E:\DailyFundzProfile\Desktop\my-elite

# Step 3: Deploy
render blueprint launch

# Step 4: Watch it deploy!
```

---

## 📖 MORE CLI INFO:

**CLI Help:**
```powershell
render --help
render blueprint --help
render services --help
```

**CLI Docs:**
```powershell
render docs
```

**Open Dashboard:**
```powershell
render dashboard
```

---

## ✅ YOUR CHOICE:

**Dashboard (5 minutes):**
- You're already there
- Just fill the form
- Click deploy
- Done!

**CLI (10 minutes):**
- Get API key
- Run `render config init`
- Run `render blueprint launch`
- Done!

**Both deploy the exact same site with same features!**

---

🚀 **Recommendation:** Since you're already on the Dashboard Blueprint page, just complete that form and deploy! You can use CLI for future updates.
