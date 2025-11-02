# Render Deployment Guide for MyRelief System

Complete guide to deploy your Django application with Supabase on Render.com

---

## 📋 Prerequisites

- ✅ GitHub repository with your Django app
- ✅ Supabase project set up (database and storage bucket)
- ✅ Render.com account (free tier available)
- ✅ Python 3.11+ (specified in `runtime.txt`)

---

## 🚀 Step-by-Step Deployment

### Step 1: Prepare Your Repository

Make sure these files are in your repository root:

```
MyReliefSystem/
├── .env.example          ✅ Created
├── build.sh              ✅ Created
├── requirements.txt      ✅ Updated
├── runtime.txt           ✅ Created
├── manage.py
├── MyReliefSystem/
│   ├── settings.py       ✅ Updated
│   └── wsgi.py
└── register/
```

**Commit and push all changes to GitHub:**
```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

---

### Step 2: Get Supabase Database Connection String

1. Go to your **Supabase Dashboard**
2. Navigate to **Settings** → **Database**
3. Scroll to **Connection string** → **Connection pooling**
4. Select **Session mode**
5. Copy the connection string (it looks like):
   ```
   postgresql://postgres.xxxxx:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require
   ```
6. **Important:** Make sure `?sslmode=require` is at the end

**Alternative:** Use **Transaction mode** for better performance with many connections

---

### Step 3: Create Render Account and Service

1. **Sign up/Login** at [Render.com](https://render.com)
2. Click **"New +"** → **"Web Service"**
3. Select **"Build from a Git repository"**
4. **Connect your GitHub account** (if not already connected)
5. **Grant Render access** to your repository
6. Select your **MyReliefSystem** repository
7. Configure:
   - **Name:** `myrelief-system` (or your preferred name)
   - **Region:** Choose closest to you
   - **Branch:** `main` (or your main branch)
   - **Root Directory:** Leave empty (project is at root)
   - **Environment:** `Python 3`
   - **Build Command:** `./build.sh`
   - **Start Command:** `gunicorn MyReliefSystem.wsgi:application`
   - **Instance Type:** `Free` (for testing) or `Starter` ($7/month)

---

### Step 4: Set Environment Variables on Render

In your Render service dashboard:

1. Go to **"Environment"** tab
2. Click **"Add Environment Variable"**
3. Add each of these variables:

#### Required Environment Variables:

```
RENDER=true
```

```
DJANGO_SECRET_KEY=your-long-random-secret-key-here
```
💡 **Generate a secure key:** You can use Python:
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

```
DJANGO_DEBUG=False
```

```
DJANGO_ALLOWED_HOSTS=your-service-name.onrender.com
```
Replace `your-service-name` with your actual Render service name

```
DJANGO_CSRF_TRUSTED_ORIGINS=https://your-service-name.onrender.com
```
Replace with your actual Render service URL (must include `https://`)

```
DATABASE_URL=postgresql://postgres.xxxxx:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require
```
Paste your Supabase connection string here (with actual password)

#### Supabase Environment Variables:

```
SUPABASE_URL=https://your-project-id.supabase.co
```
From Supabase: Settings → API → Project URL

```
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```
From Supabase: Settings → API → `anon` `public` key

```
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```
From Supabase: Settings → API → `service_role` `secret` key (⚠️ Keep secret!)

```
SUPABASE_BUCKET=id_proof
```

```
SUPABASE_TABLE=Register
```

#### Optional Security:

```
DJANGO_SECURE_SSL_REDIRECT=True
```

---

### Step 5: Deploy

1. After setting all environment variables, go to **"Manual Deploy"** tab
2. Click **"Deploy latest commit"**
3. Watch the build logs for any errors
4. Once deployment completes, click the service URL to test

---

### Step 6: Create Superuser (First Time)

1. In Render dashboard, go to your service
2. Click **"Shell"** tab (or go to **Settings** → **Shell**)
3. Run:
   ```bash
   python manage.py createsuperuser
   ```
4. Follow prompts to create admin account
5. Access admin at: `https://your-service.onrender.com/admin/`

---

## ✅ Verification Checklist

After deployment, verify:

- [ ] Site loads at Render URL
- [ ] Registration page works: `/register/`
- [ ] Can register a new user
- [ ] Data appears in Supabase `Register` table
- [ ] Image uploads to Supabase storage bucket
- [ ] Dashboard displays user data
- [ ] Images display correctly from Supabase URLs
- [ ] Admin panel accessible at `/admin/`
- [ ] Static files load (CSS, JS, images)
- [ ] No console errors in browser

---

## 🔧 Troubleshooting

### Static Files Not Loading

**Problem:** CSS/JS files return 404

**Solutions:**
1. ✅ Verify `whitenoise.middleware.WhiteNoiseMiddleware` is in `MIDDLEWARE` (after `SecurityMiddleware`)
2. ✅ Check build logs: `python manage.py collectstatic` should run
3. ✅ Verify `STATIC_ROOT = BASE_DIR / "staticfiles"` in settings
4. ✅ Check Render build logs for collectstatic errors

### 403 CSRF Errors

**Problem:** Forms return "403 Forbidden"

**Solutions:**
1. ✅ Ensure `DJANGO_CSRF_TRUSTED_ORIGINS` includes your Render URL **with** `https://`
   ```
   https://your-service.onrender.com
   ```
2. ✅ Verify domain is in `DJANGO_ALLOWED_HOSTS`
3. ✅ Check `CSRF_COOKIE_SECURE = True` is set (should be automatic)

### Database Connection Errors

**Problem:** "connection refused" or "SSL required"

**Solutions:**
1. ✅ Check `DATABASE_URL` format is correct
2. ✅ Ensure `?sslmode=require` is at the end of connection string
3. ✅ Verify Supabase database is active
4. ✅ Check if using Pooler vs Direct connection (use Pooler string)
5. ✅ Test connection string locally first

### White Page / 500 Errors

**Problem:** Blank page or Internal Server Error

**Solutions:**
1. ✅ Check **Render logs**: Dashboard → **"Logs"** tab
2. ✅ Verify `Start Command` is correct: `gunicorn MyReliefSystem.wsgi:application`
3. ✅ Check all environment variables are set correctly
4. ✅ Look for Python errors in build/deploy logs
5. ✅ Verify `DJANGO_SECRET_KEY` is set (not using default)

### Supabase Upload Errors

**Problem:** Image upload fails

**Solutions:**
1. ✅ Verify `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are correct
2. ✅ Check storage bucket `id_proof` exists and is public
3. ✅ Verify RLS policies allow uploads (or using service_role key)
4. ✅ Check Render logs for Supabase API errors

### Build Fails

**Problem:** Build script fails

**Solutions:**
1. ✅ Check `build.sh` has execute permissions (should be automatic)
2. ✅ Verify all packages in `requirements.txt` are compatible
3. ✅ Check Python version matches `runtime.txt` (3.11+)
4. ✅ Review build logs for specific error messages

---

## 📝 Important Notes

### Database Connection

- **Use Connection Pooler string** from Supabase (recommended)
- **Keep `?sslmode=require`** at the end
- **Session mode** is simpler; **Transaction mode** is better for high traffic

### Security

- ⚠️ **Never commit** `.env` file (already in `.gitignore`)
- ⚠️ **Never expose** `SUPABASE_SERVICE_ROLE_KEY` to frontend
- ⚠️ **Always use** `DJANGO_DEBUG=False` in production
- ✅ **Use strong** `DJANGO_SECRET_KEY` in production

### File Structure

Your project structure should be:
```
MyReliefSystem/              # Repository root
├── .env.example
├── .gitignore
├── build.sh
├── requirements.txt
├── runtime.txt
├── manage.py
├── MyReliefSystem/          # Django project folder
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── register/                # Django app
    ├── models.py
    ├── views.py
    ├── utils.py
    └── templates/
```

---

## 🔄 Updating Your Deployment

After making code changes:

1. **Commit and push to GitHub:**
   ```bash
   git add .
   git commit -m "Your changes"
   git push origin main
   ```

2. **Render will automatically redeploy** (if auto-deploy is enabled)

3. **Or manually trigger:** Render Dashboard → Manual Deploy → Deploy latest commit

---

## 📊 Monitoring

- **Logs:** View real-time logs in Render dashboard → **Logs** tab
- **Metrics:** Check CPU, Memory, Response times in **Metrics** tab
- **Events:** See deployment history in **Events** tab

---

## 🎯 Next Steps

After successful deployment:

1. ✅ Test all features thoroughly
2. ✅ Set up custom domain (optional)
3. ✅ Enable monitoring and alerts
4. ✅ Configure backup strategy for database
5. ✅ Set up CI/CD for automatic deployments

---

## 📚 Additional Resources

- [Render Documentation](https://render.com/docs)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Supabase Documentation](https://supabase.com/docs)

---

**Need Help?** Check Render build/deploy logs for detailed error messages!

