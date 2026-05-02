# Admin Email Notification System

## Overview
Automated email notifications are sent to `admin@elitewealthcapita.uk` for:
1. **New User Registrations** - Includes user credentials for password recovery
2. **Deposit Requests** - Includes payment details, screenshot, and verification buttons

## Email Configuration

### Zoho SMTP Settings (already configured in .env)
```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.zoho.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=admin@elitewealthcapita.uk
EMAIL_HOST_PASSWORD=eAXHqJSWHGvM
DEFAULT_FROM_EMAIL=admin@elitewealthcapita.uk
ADMIN_EMAIL=admin@elitewealthcapita.uk
```

## Features Implemented

### 1. New User Registration Notifications
**Trigger**: When a user creates a new account

**Email includes**:
- User's full name
- Email address
- User ID
- Referral code
- Registration date
- **Plain text password** (for customer support/password recovery)
- Link to user's admin panel page

**Security Note**: The plain text password is only sent once via email. It's stored hashed in the database for security.

**File**: `accounts/email_notifications.py` → `send_new_user_notification()`

### 2. Deposit Request Notifications
**Trigger**: When a user submits a deposit

**Email includes**:
- User information (name, email, ID)
- Deposit amount (highlighted in large text)
- Payment method (Bank/Crypto type)
- Transaction hash (if provided)
- Payment screenshot (embedded in email + attached)
- **VERIFY & APPROVE button** - Links directly to admin panel
- **REJECT button** - Links directly to admin panel

**File**: `accounts/email_notifications.py` → `send_deposit_notification()`

### 3. Deposit Status Change Notifications (to User)
**Trigger**: When admin changes deposit status in admin panel

**Confirmed**:
- User receives confirmation email
- Balance is automatically credited
- In-app notification created

**Rejected**:
- User receives rejection email with reason
- In-app notification created
- Contact support button included

**File**: `investments/signals.py` → `notify_deposit_status_change()`

## How Admin Verifies Deposits

### Method 1: Via Email
1. Admin receives email with deposit details and screenshot
2. Click **"VERIFY & APPROVE"** button in email
3. Opens admin panel → Deposit page
4. Change **Status** to **"Confirmed"** or **"Rejected"**
5. Add optional admin note (for rejections)
6. Click **Save**
7. User automatically receives email confirmation
8. User's balance is automatically updated (if confirmed)

### Method 2: Via Admin Panel Directly
1. Log in to admin panel: `https://elitewealthcapita.uk/admin/`
2. Navigate to **Investments → Deposits**
3. Find pending deposits (yellow "Pending" badge)
4. Click on deposit to view details
5. Review payment screenshot
6. Change **Status** to **"Confirmed"** or **"Rejected"**
7. Add optional admin note
8. Click **Save**

## Testing the Email System

### Test 1: New User Registration
```bash
# Run Django development server
python manage.py runserver

# Or on production (Render):
# Email will be sent automatically when users signup
```

1. Go to signup page: `http://localhost:8000/signup/`
2. Create a new account
3. Check `admin@elitewealthcapita.uk` inbox
4. Should receive email with user credentials

### Test 2: Deposit Request
1. Log in to website
2. Go to **Deposit** page: `/investments/deposit/`
3. Enter amount (e.g., $100)
4. Select payment method (Bitcoin, Ethereum, etc.)
5. Upload screenshot (optional)
6. Enter transaction hash (optional)
7. Submit deposit
8. Check `admin@elitewealthcapita.uk` inbox
9. Should receive email with deposit details

### Test 3: Deposit Verification
1. Log in to admin panel: `/admin/`
2. Go to **Investments → Deposits**
3. Click on a pending deposit
4. Change Status to **"Confirmed"**
5. Click **Save**
6. User should receive confirmation email
7. User's balance should be updated

### Test 4: Deposit Rejection
1. Log in to admin panel
2. Go to **Investments → Deposits**
3. Click on a pending deposit
4. Change Status to **"Rejected"**
5. Add reason in **Admin note** field
6. Click **Save**
7. User should receive rejection email with reason

## Production Deployment

### On Render.com
The system is already configured for production. Just ensure:

1. **.env file on Render** has Zoho credentials:
   ```
   EMAIL_HOST_USER=admin@elitewealthcapita.uk
   EMAIL_HOST_PASSWORD=eAXHqJSWHGvM
   ```

2. **Push code to GitHub**:
   ```bash
   git add .
   git commit -m "Add admin email notification system"
   git push origin main
   ```

3. **Render auto-deploys** - Wait for deployment to finish

4. **Test on production**: Create test user or deposit

## Troubleshooting

### Emails not sending?
1. Check .env file has correct credentials
2. Check Django logs: `python manage.py runserver` (look for errors)
3. Verify Zoho account is active and app password is valid
4. Check spam folder in admin@elitewealthcapita.uk

### Email sent but not received?
1. Check spam/junk folder
2. Verify Zoho sending limits (usually 500/day for free accounts)
3. Check Django logs for sending errors

### Balance not updating on deposit confirmation?
1. Check `investments/signals.py` is properly connected
2. Verify `investments/apps.py` has `ready()` method importing signals
3. Restart Django server

## File Structure
```
MY-SITE/
├── accounts/
│   ├── email_notifications.py   # Admin notification emails
│   └── views.py                  # Signup view (calls email notification)
├── investments/
│   ├── signals.py                # Deposit status change notifications
│   ├── apps.py                   # Registers signals
│   ├── views.py                  # Deposit view (calls email notification)
│   └── admin.py                  # Admin panel deposit management
└── .env                          # Email credentials (Zoho SMTP)
```

## Security Considerations

### Password Storage
- ⚠️ **Passwords sent via email** is a security risk
- Passwords are stored hashed in database
- Only sent once in plain text to admin email
- Admin should store credentials securely (password manager)
- Consider implementing password reset links instead

### Recommendations
1. Use secure password manager for storing user credentials
2. Implement 2FA for admin email account
3. Regularly rotate Zoho app password
4. Monitor failed login attempts
5. Consider implementing password reset flow instead of storing passwords

## Support

If you encounter any issues:
1. Check Django logs: `python manage.py runserver`
2. Verify email configuration in .env
3. Test Zoho SMTP manually with a simple script
4. Contact Zoho support if SMTP issues persist

## Next Steps (Optional Enhancements)

1. **SMS Notifications**: Add Twilio integration for SMS alerts
2. **Slack Integration**: Post notifications to Slack channel
3. **Admin Dashboard**: Create custom admin dashboard for deposits
4. **Auto-verification**: Blockchain verification via API
5. **Batch Actions**: Approve multiple deposits at once
6. **Email Templates**: Use Django templates for better maintainability
