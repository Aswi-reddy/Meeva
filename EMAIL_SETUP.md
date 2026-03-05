# 📧 Email Configuration for Meeva Platform

## ⚠️ IMPORTANT: Gmail App Password Required

Gmail has disabled "Less Secure Apps" access. You **MUST** use an App Password instead of your regular Gmail password.

### 🔧 How to Generate Gmail App Password:

1. **Enable 2-Factor Authentication** (if not already enabled):
   - Go to: https://myaccount.google.com/security
   - Enable 2-Step Verification

2. **Generate App Password**:
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" as the app
   - Select "Other" as the device and name it "Meeva"
   - Click "Generate"
   - Copy the 16-character password (remove spaces)

3. **Update .env file**:
   ```
   EMAIL_HOST_PASSWORD=your-16-character-app-password
   ```

### 📝 Current Email Settings:

```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-character-app-password  # ⚠️ Use Gmail App Password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

⚠️ Never commit real credentials (emails/passwords/app-passwords) into the repository. Store them only as environment variables (Render dashboard, `.env` locally).

---

## 📨 Email Notifications Implemented:

### 1. **Vendor Registration** 
- Sent when vendor completes registration
- Contains: Business details, next steps, timeline

### 2. **Vendor Approval**
- Sent when admin approves vendor
- Contains: Login link, platform fee, approval details

### 3. **Vendor Rejection**
- Sent when admin rejects vendor
- Contains: Rejection reason, next steps

### 4. **Vendor Suspension**
- Sent when admin suspends vendor account
- Contains: Suspension notice, contact information

### 5. **Vendor Reactivation**
- Sent when admin reactivates suspended account
- Contains: Reactivation confirmation, login link

---

## 🧪 Testing Email Configuration:

### Method 1: Django Shell
```bash
cd meeva
python manage.py shell
```
Then run:
```python
from vendor.test_email import test_email
test_email()
```

### Method 2: Register Test Vendor
1. Go to: http://localhost:8000/vendor/register/
2. Fill in registration form with test data
3. Check email inbox for confirmation

---

## 🔍 Troubleshooting:

### Error: "Authentication failed"
- **Solution**: Use App Password instead of regular password
- Generate from: https://myaccount.google.com/apppasswords

### Error: "SMTPAuthenticationError"
- **Solution**: Enable 2FA and create App Password

### Error: "Connection refused"
- **Check**: Port 587 is not blocked by firewall
- **Check**: EMAIL_USE_TLS=True in settings

### Email not received
- **Check**: Spam/Junk folder
- **Check**: Email address is correct
- **Try**: Send test email first

---

## 📧 Email Flow:

```
Vendor Registration
      ↓
  Send Email → "Registration Successful" 
      ↓
Admin Reviews
      ↓
  ┌─── Approve → Send Email → "Application Approved"
  │
  └─── Reject → Send Email → "Application Rejected"

Later:
  ┌─── Suspend → Send Email → "Account Suspended"
  │
  └─── Activate → Send Email → "Account Reactivated"
```

---

## 🎯 Production Deployment Notes:

For production:
1. Use environment variables for email credentials
2. Consider using services like SendGrid, Amazon SES
3. Never commit .env file to version control
4. Add email logging for debugging
5. Implement retry mechanism for failed emails

---

## 📝 Files Modified:

- `meeva/settings.py` - Email configuration
- `.env` - Email credentials
- `vendor/emails.py` - Email utility functions
- `vendor/views.py` - Registration email
- `admin/views.py` - Approval/Rejection/Suspend/Activate emails
- `vendor/test_email.py` - Email testing utility

---

**Note**: After updating the App Password in `.env`, restart the Django server for changes to take effect.
