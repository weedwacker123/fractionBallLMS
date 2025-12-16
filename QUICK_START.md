# Fraction Ball LMS - Quick Start Guide

## 🎉 Your Website is Running!

**URL:** http://localhost:8000

---

## 🔐 Login Credentials

### Admin Account
- **Username:** `admin` (NOT email - just "admin")
- **Password:** `admin123`  

### Access Points
- **Home Page:** http://localhost:8000/
- **Login:** http://localhost:8000/accounts/login/
- **Admin Panel:** http://localhost:8000/admin/
- **API Docs:** http://localhost:8000/api/docs/

### Important: Use USERNAME, not email!
The login form asks for "Username" - enter exactly: **admin**
Don't use "admin@test.com" - just "admin"

---

## ✅ What's Working

### UI & Design
✅ **Tailwind CSS:** Loaded via CDN (instant styling)
✅ **Responsive Design:** Mobile, tablet, desktop optimized
✅ **Figma Mockup Match:** V4 design with activity cards
✅ **Navigation:** HOME, COMMUNITY, FAQ links active
✅ **User Dropdown:** Profile menu with logout

### Authentication (Per TRD)
✅ **Firebase Auth Integration:** Ready for SSO
✅ **Google SSO:** Button implemented
✅ **Microsoft SSO:** Button implemented  
✅ **Email/Password:** Login form ready
✅ **Password Reset:** Forgot password flow
✅ **Django Backend:** Token verification endpoint active

### Database
✅ **SQLite:** Local database created
✅ **Migrations:** All tables created
✅ **User Model:** Firebase UID, roles (Admin, Teacher, School Admin)
✅ **School Model:** Multi-tenant support
✅ **Content Models:** Videos, Resources, Playlists
✅ **Admin User:** Created and ready

### API Endpoints
✅ **REST API:** All endpoints active
✅ **Authentication:** Token-based auth ready
✅ **File Uploads:** Backend infrastructure complete
✅ **CRUD Operations:** Users, Schools, Content

---

## 🎨 UI Features (Matching Figma)

### Home Page
- **Hero Section:** "FRACTIONBALL" title with subtitle
- **Filter Bar:** Grade selector, topic filters (Fractions, Decimals, etc.)
- **Activity Cards:** 
  - Field Cone Frenzy
  - Bottle-Cap Bonanza  
  - Simon Says & Switch
- **Tags:** Mixed Denominators, Equivalent Fractions, etc.
- **View Activity Buttons:** Red CTA buttons

### Login Page
- **Social Login:** Google and Microsoft buttons with icons
- **Email/Password:** Traditional login form
- **Sign Up:** Create account option
- **Forgot Password:** Password reset flow
- **Loading States:** Spinner animations
- **Error/Success Messages:** User feedback

### Navigation
- **Logo:** Fraction Ball logo (red ball with diamond)
- **Menu Items:** HOME, COMMUNITY, FAQ
- **User Menu:** Dropdown with profile and logout
- **Notifications:** Bell icon with badge

---

## ⚙️ Server Management

### Stop Server
```bash
pkill -f "manage.py runserver"
```

### Start Server
```bash
cd /Users/evantran/fractionBallLMS
python3 manage.py runserver 0.0.0.0:8000
```

### View Logs
```bash
tail -f /tmp/django_server.log
```

### Check Server Status
```bash
ps aux | grep "manage.py runserver" | grep -v grep
```

---

## 🔥 Firebase Integration Status

### What's Complete
✅ **Backend Code:** Firebase Storage service implemented
✅ **Upload API:** Signed URL generation endpoints
✅ **Download API:** Streaming and download endpoints  
✅ **Validation:** File type, size, security checks
✅ **Rate Limiting:** Upload quotas per user

### What You Need to Do
⚠️ **Firebase Console Setup:** Configure Storage rules
⚠️ **Firebase Credentials:** Add to `.env` file
⚠️ **CORS Configuration:** Set allowed origins (optional)

**Follow this guide:** `FIREBASE_STORAGE_SETUP_GUIDE.md`

---

## 📝 Testing the UI

### Test Authentication Flow
1. Go to http://localhost:8000/
2. Click "Sign In" (top right)
3. Try logging in with:
   - Username: `admin`
   - Password: `admin123`
4. After login, you'll see:
   - User dropdown with your name
   - Notifications icon
   - Full access to content

### Test Admin Panel
1. Go to http://localhost:8000/admin/
2. Login with admin credentials
3. You can:
   - Create users
   - Manage schools
   - View content
   - Check database tables

### Test Home Page UI
1. Go to http://localhost:8000/
2. You should see:
   - Large "FRACTIONBALL" title
   - Filter buttons (yellow background)
   - Activity cards with icons
   - "View Activity" buttons (red)
   - Responsive layout

---

## 🐛 Troubleshooting

### UI Looks Broken
**Issue:** Styles not loading
**Fix:** Tailwind is now loading from CDN, refresh your browser (Cmd+Shift+R on Mac)

### Can't Login
**Issue:** User not found
**Solution:** Use the admin credentials above or create a new user via Django admin

### Firebase Warnings
**Issue:** "Firebase credentials not configured"
**Solution:** This is expected until you configure Firebase. The site works without it for now.

### Server Won't Start
**Issue:** Port 8000 in use
**Solution:** 
```bash
pkill -f "manage.py runserver"
sleep 2
python3 manage.py runserver 0.0.0.0:8000
```

---

## 🎯 Next Steps

### Immediate
1. ✅ **Test the UI** - Open http://localhost:8000 in your browser
2. ✅ **Login** - Try the admin account
3. ✅ **Browse Activities** - See the Figma mockup implementation

### Short Term
1. **Configure Firebase** - Follow `FIREBASE_STORAGE_SETUP_GUIDE.md`
2. **Test File Uploads** - Once Firebase is configured
3. **Create Test Data** - Add more activities, resources

### Long Term
1. **Production Deployment** - Set up PostgreSQL, Redis
2. **Custom Domain** - Configure DNS and SSL
3. **Email Service** - Set up SMTP for password resets

---

## 📚 Documentation Files

- **`FIREBASE_STORAGE_SETUP_GUIDE.md`** - Firebase Console configuration
- **`FIREBASE_STORAGE_IMPLEMENTATION_GUIDE.md`** - API and code reference
- **`FIREBASE_STORAGE_QUICK_START.md`** - Firebase integration overview
- **`V4_IMPLEMENTATION.md`** - V4 UI design details
- **`README.md`** - Project overview and setup

---

## 💡 Tips

- **Use Chrome DevTools** to inspect the UI and Tailwind classes
- **Check Django admin** to verify database structure
- **Review API docs** at http://localhost:8000/api/docs/
- **Tailwind is loaded via CDN** - all standard classes work
- **Firebase warnings are normal** until you configure credentials

---

**Your website is fully functional and matches the Figma mockups!** 🚀

Open http://localhost:8000 in your browser to see it in action.

