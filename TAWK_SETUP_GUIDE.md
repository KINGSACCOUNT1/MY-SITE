# 📱 TAWK.TO SETUP GUIDE

## ✅ Current Status: EMBEDDED & WORKING

Your Tawk.to live chat is already integrated into your website!

---

## 📊 YOUR TAWK.TO DETAILS

**Property Name:** elitewealth  
**Property ID:** `69c1f2a729e9681c3d64de5d`  
**API Key:** `75b4b0e9a4e6de42cd75e44db37824ae55f3fe00`  
**Property URL:** https://elitewealthcapita.uk  
**Embed Code:** ✅ Already added to `templates/base.html`

---

## 🎨 RECOMMENDED DASHBOARD SETTINGS

### 1. Complete Your Property Overview

**Steps:**
1. Go to https://dashboard.tawk.to
2. Click **Administration** → **Overview**

**Fill in these fields:**

```
Property Name: Elite Wealth Capital
Property Region: United Kingdom (or your main market)
Discovery Listing: Enabled ✅
Category: Company, organisation or institution
Subcategory: Bank/Financial Institution

Description:
Elite Wealth Capital is a premier cryptocurrency and real estate investment 
platform offering daily returns on digital asset investments. Our 24/7 support 
team assists with deposits, withdrawals, KYC verification, and investment 
portfolio management. Join 50,000+ investors worldwide building wealth with 
elite investment strategies.

Keyterms:
cryptocurrency investment, bitcoin, ethereum, real estate investment, 
daily returns, portfolio management, kyc verification, crypto deposit, 
crypto withdrawal, investment plans, elite wealth, wealth management, 
passive income, ROI, digital assets
```

---

## 🎨 WIDGET CUSTOMIZATION

### Appearance Settings

**Path:** Chat Widget → Appearance

**Primary Color:** `#d4af37` (Elite Wealth Gold)  
**Widget Position:** Bottom Right  
**Widget Size:** Standard  
**Widget Icon:** Chat bubble (default) or upload custom icon

**Branding:**
- Upload your Elite Wealth Capital logo (512x512px)
- This appears in the chat window header

**Online Badge Text:** "We're online! Chat with us"  
**Offline Badge Text:** "Leave us a message"

---

## 💬 PRE-CHAT FORM (Highly Recommended)

**Path:** Chat Widget → Pre-Chat Form

Enable pre-chat form to collect visitor info before chat starts:

**Required Fields:**
- ✅ Name
- ✅ Email
- ✅ Subject (dropdown with these options):
  - Deposit Inquiry
  - Withdrawal Support  
  - KYC Verification Help
  - Investment Plan Questions
  - Loan Application
  - Technical Issue
  - Account Upgrade
  - General Question

**Optional Fields:**
- Phone number
- Investment interest (text field)
- Current investment amount (dropdown)

---

## 📧 OFFLINE BEHAVIOR

**Path:** Chat Widget → Behavior

When your team is offline:

**Offline Message:**
```
Thank you for contacting Elite Wealth Capital! 

Our support team is currently offline. Please leave your message below 
and we'll respond within 24 hours. For urgent matters, email us at 
support@elitewealthcapita.uk

Business Hours:
Monday - Friday: 9 AM - 6 PM GMT
Saturday: 10 AM - 4 PM GMT
Sunday: Closed
```

**Email Notification:** Enable (sends offline messages to your email)  
**Auto-Reply:** Enable  
**Auto-Reply Message:**
```
Thank you for your message! We've received your inquiry and will respond 
within 24 hours. Your ticket number is #{{ticket_id}}.

For immediate assistance with common questions, visit our FAQ: 
https://elitewealthcapita.uk/faq/
```

---

## 🤖 AUTOMATED RESPONSES (Shortcuts)

**Path:** Chat Widget → Shortcuts

Create quick response templates for common questions:

### Shortcut Examples:

**!deposit** → 
```
To make a deposit:
1. Go to Dashboard → Add Funds
2. Select cryptocurrency (BTC, ETH, USDT, etc.)
3. Copy the wallet address
4. Send funds and upload proof of payment
5. Admin will confirm within 30 minutes

Minimum deposit: $10
Processing time: 15-30 minutes
```

**!withdraw** →
```
To request a withdrawal:
1. Go to Dashboard → Withdraw
2. Enter amount and wallet address
3. Submit request
4. Admin approval within 24 hours
5. Funds sent to your wallet

Minimum withdrawal: $50
Processing time: 24-48 hours
```

**!kyc** →
```
KYC Verification Steps:
1. Go to Dashboard → KYC Upload
2. Upload: ID Card/Passport + Selfie + Proof of Address
3. File requirements: JPEG/PNG, max 5MB each
4. Verification time: 24-48 hours
5. You'll receive email notification

Benefits: Higher withdrawal limits, premium features
```

**!plans** →
```
Our Investment Plans:

• Starter Plan: $100-$999 (3% daily ROI)
• Silver Plan: $1,000-$4,999 (4.5% daily ROI)  
• Gold Plan: $5,000-$9,999 (6% daily ROI)
• Platinum Plan: $10,000-$24,999 (8% daily ROI)
• Diamond Plan: $25,000+ (12% daily ROI)

All plans include:
✅ Daily ROI credited
✅ Capital return after term
✅ 24/7 support
✅ Referral bonuses

View details: https://elitewealthcapita.uk/investment-plans/
```

**!referral** →
```
Earn with our Referral Program:

💰 New User Bonus: $20 signup bonus
💰 Referrer Bonus: $30 per referral
💰 Lifetime Commissions: 5% of referral investments

Your Referral Link:
https://elitewealthcapita.uk/signup/?ref={{user.referral_code}}

Share with friends and earn passive income!
```

---

## 👥 TEAM MANAGEMENT

**Path:** User Management → Agents

**Invite Your Support Team:**

1. Click **Add Agent**
2. Enter email address
3. Select role:
   - **Administrator:** Full access to all features
   - **Agent:** Can chat with visitors
   - **Monitor:** View-only access

**Agent Guidelines Document:**

```markdown
# Support Agent Guidelines

## Response Time Standards:
- First response: Within 60 seconds
- Average resolution: 5 minutes
- Maximum wait: 3 minutes between responses

## Priority Issues:
1. Withdrawal delays (URGENT)
2. Deposit not credited (URGENT)
3. Login issues (HIGH)
4. KYC verification (HIGH)
5. General questions (NORMAL)

## Escalation:
- Technical issues → Escalate to admin
- Large deposits ($10,000+) → Notify admin
- Suspected fraud → Immediately escalate
- Negative balance → Escalate to admin

## Tone:
- Professional and friendly
- Use visitor's name
- Empathetic to concerns
- Clear and concise
- No jargon (explain technical terms)

## Never Share:
- Internal systems access
- Other user's information
- Detailed technical architecture
- Admin panel URLs
```

---

## 📊 KNOWLEDGE BASE SETUP

**Path:** Knowledge Base

Create self-service help articles to reduce chat volume:

**Recommended Articles:**

1. **How to Make a Deposit**
2. **How to Request a Withdrawal**
3. **KYC Verification Process**
4. **Investment Plans Explained**
5. **Referral Program Guide**
6. **Security & Two-Factor Authentication**
7. **Forgotten Password Reset**
8. **Understanding ROI Calculations**
9. **Withdrawal Processing Times**
10. **Supported Cryptocurrencies**

**Article Template:**
```markdown
# Title

## Quick Answer
[1-2 sentence summary]

## Step-by-Step Guide
1. First step
2. Second step
3. Third step

## Common Issues
- Issue 1: Solution
- Issue 2: Solution

## Still Need Help?
Contact our support team via live chat or email: support@elitewealthcapita.uk
```

---

## 🔔 NOTIFICATION SETTINGS

**Path:** Settings → Notifications

**Desktop Notifications:** Enable (Chrome/Firefox/Safari)  
**Email Notifications:** Enable  
**Sound Alerts:** Enable  
**Mobile Push:** Enable (install Tawk.to mobile app)

**Email Digest:** Daily summary at 9 AM

---

## 📱 MOBILE APP (Highly Recommended)

**Download Tawk.to Mobile App:**
- iOS: App Store → Search "tawk.to"
- Android: Google Play → Search "tawk.to"

**Benefits:**
- Respond to chats from anywhere
- Push notifications for new chats
- View visitor details
- Access shortcuts
- View chat history

---

## 🎯 WIDGET CARDS (NEW FEATURE)

**Path:** Chat Widget → Widget Cards

Add interactive cards that appear before chat opens:

**Recommended Cards:**

1. **Quick Links Card:**
   - View Investment Plans
   - Check Deposit Status
   - FAQ Page
   - Contact Support

2. **Lead Qualification Card:**
   - Investment amount interest
   - Investment timeline
   - Contact information

3. **Video Introduction Card:**
   - CEO welcome video
   - Platform overview
   - Investment success stories

---

## 📈 ANALYTICS & REPORTING

**Path:** Dashboard → Reports

**Key Metrics to Track:**

- **Chat Volume:** Total chats per day/week/month
- **Response Time:** Average first response time
- **Resolution Time:** Average time to resolve issue
- **Satisfaction:** Chat satisfaction ratings
- **Busiest Hours:** When to staff more agents
- **Top Issues:** Most common support topics
- **Conversion Rate:** Chats that lead to investments

**Weekly Review Meeting Agenda:**
1. Review satisfaction scores
2. Identify common issues
3. Update shortcuts/knowledge base
4. Agent performance review
5. Process improvements

---

## 🔐 SECURITY SETTINGS

**Path:** Settings → Security

**Enable These Features:**

✅ **Secure Mode:** Verify user identity  
✅ **IP Tracking:** Track visitor IPs for security  
✅ **Block Abusive Visitors:** Auto-block spam/abuse  
✅ **Profanity Filter:** Filter offensive language  
✅ **CAPTCHA:** Prevent bot spam (if needed)

**Data Retention:**
- Chat history: 12 months
- Visitor data: 6 months
- Export data monthly for backup

---

## 🎨 CUSTOM CSS (Advanced)

**Path:** Chat Widget → Appearance → Custom CSS

Match your website theme:

```css
/* Elite Wealth Capital Custom Styles */
.tawk-button {
    background-color: #d4af37 !important;
    box-shadow: 0 4px 12px rgba(212, 175, 55, 0.4) !important;
}

.tawk-header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%) !important;
    border-bottom: 2px solid #d4af37 !important;
}

.tawk-min-chat-bubble {
    border: 2px solid #d4af37 !important;
}
```

---

## ✅ SETUP CHECKLIST

Copy this checklist to complete setup:

- [x] Property created and configured
- [x] Widget embed code added to website
- [ ] Property description added
- [ ] Keyterms added for discovery
- [ ] Widget color customized (#d4af37)
- [ ] Logo uploaded (512x512px)
- [ ] Pre-chat form configured
- [ ] Offline message customized
- [ ] 5+ shortcuts created (deposit, withdraw, kyc, etc.)
- [ ] Support team invited
- [ ] Agent guidelines documented
- [ ] Knowledge base articles created (at least 10)
- [ ] Mobile app installed
- [ ] Notifications configured
- [ ] Security settings enabled
- [ ] Analytics review scheduled (weekly)

---

## 📞 SUPPORT CONTACTS

**Tawk.to Support:**
- Email: support@tawk.to
- Live Chat: https://www.tawk.to
- Help Center: https://help.tawk.to

**Your Admin Dashboard:**
- https://dashboard.tawk.to
- Login with your registered email

---

**Status:** ✅ Widget embedded and working  
**Setup Progress:** 31% → Target: 100%  
**Next Step:** Complete property description and shortcuts  
**Est. Time to Complete:** 2-3 hours
