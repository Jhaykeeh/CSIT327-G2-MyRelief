# Supabase Setup Guide for MyRelief System

This guide will walk you through setting up and running the MyRelief System with Supabase integration.

---

## 📋 Prerequisites

- Python 3.8 or higher installed
- A Supabase account (sign up at https://supabase.com)
- Git (if cloning the repository)

---

## 🚀 Step-by-Step Setup

### Step 1: Clone or Navigate to Project

If cloning:
```bash
git clone https://github.com/Jhaykeeh/CSIT327-G2-MyRelief.git
cd MyRelief-System
```

Or navigate to your existing project directory:
```bash
cd C:\Users\Judd\Desktop\MyReliefSystem
```

---

### Step 2: Set Up Virtual Environment

**Windows:**
```bash
python -m venv env
env\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv env
source env/bin/activate
```

You should see `(env)` at the beginning of your terminal prompt when activated.

---

### Step 3: Install Required Packages

Install all dependencies:
```bash
pip install django supabase python-dotenv
```

Or if you have a requirements.txt file:
```bash
pip install -r requirements.txt
```

---

### Step 4: Set Up Supabase Project

#### 4.1 Create Supabase Project
1. Go to https://supabase.com and sign in
2. Click "New Project"
3. Fill in:
   - **Name:** MyRelief (or your preferred name)
   - **Database Password:** (create a strong password, save it!)
   - **Region:** Choose closest to you
4. Click "Create new project" and wait 2-3 minutes for setup

#### 4.2 Get Supabase Credentials
1. In your Supabase dashboard, go to **Settings** (gear icon) → **API**
2. Copy these values:
   - **Project URL** (under "Project URL")
   - **anon public** key (under "Project API keys")

---

### Step 5: Create Supabase Table

1. In Supabase dashboard, go to **Table Editor** (left sidebar)
2. Click **"New table"**
3. Configure the table:
   - **Name:** `Register` (exact name, case-sensitive)
   - Click **"Save"**
4. Add columns (click **"+ Insert Column"** for each):

   | Column Name | Type | Default | Nullable |
   |------------|------|---------|----------|
   | `id` | int8 | Auto (serial) | ❌ No (Primary Key) |
   | `username` | text | - | ❌ No (Unique) |
   | `password` | text | - | ❌ No |
   | `address` | text | - | ❌ No |
   | `contact` | text | - | ❌ No |

5. For each column:
   - Click **"+ Insert Column"**
   - Enter column name
   - Select type
   - For `username`: Check **"Is Unique"** checkbox
   - Click **"Save"**
6. Make sure `id` is set as Primary Key (should be automatic)

---

### Step 6: Create Storage Bucket

1. In Supabase dashboard, go to **Storage** (left sidebar)
2. Click **"New bucket"**
3. Configure:
   - **Name:** `id_proof` (exact name)
   - **Public bucket:** ✅ Check this (so images are accessible)
4. Click **"Create bucket"**
5. Set up bucket policies (optional but recommended):
   - Go to **Storage** → **Policies**
   - Click on `id_proof` bucket
   - Add policy for uploads if needed

---

### Step 7: Configure Environment Variables

1. Create a `.env` file in the project root directory (same level as `manage.py`):

   **Windows:**
   ```bash
   # In your project root directory
   type nul > .env
   ```

   **Mac/Linux:**
   ```bash
   touch .env
   ```

2. Open `.env` file and add your Supabase credentials:

   ```env
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_KEY=your-anon-public-key-here
   SUPABASE_BUCKET=id_proof
   SUPABASE_TABLE=Register
   ```

   **Replace:**
   - `https://your-project-id.supabase.co` with your actual Project URL
   - `your-anon-public-key-here` with your actual anon public key

   **Example:**
   ```env
   SUPABASE_URL=https://abcdefghijklmnop.supabase.co
   SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFiY2RlZmdoaWprbG1ub3AiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTYzMjg1NjAwMCwiZXhwIjoxOTQ4NDMyMDAwfQ.example_key
   SUPABASE_BUCKET=id_proof
   SUPABASE_TABLE=Register
   ```

3. **Important:** Make sure `.env` is in `.gitignore` (it should be already) to keep your credentials safe!

---

### Step 8: Run Django Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

This sets up your local SQLite database (still needed for Django authentication).

---

### Step 9: Start the Development Server

```bash
python manage.py runserver
```

You should see:
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

---

### Step 10: Test the Application

1. Open your browser and go to: **http://127.0.0.1:8000/**
2. You should see the login page
3. Click **"Register here"** or go to **http://127.0.0.1:8000/register/**
4. Fill in the registration form:
   - Username
   - Password
   - Address
   - Contact Number
   - Upload ID Proof (image file)
5. Click **"Register"**

---

### Step 11: Verify Data in Supabase

1. **Check Table Data:**
   - Go to Supabase dashboard → **Table Editor**
   - Click on `Register` table
   - You should see your registered user data

2. **Check Storage:**
   - Go to Supabase dashboard → **Storage**
   - Click on `id_proof` bucket
   - You should see uploaded image files

---

## 🔧 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'supabase'"
**Solution:**
```bash
pip install supabase python-dotenv
```

### Issue: "Supabase connection error"
**Solutions:**
1. Check your `.env` file has correct credentials
2. Make sure `.env` is in the project root (same folder as `manage.py`)
3. Verify your Supabase URL and Key are correct (no extra spaces)
4. Check your internet connection

### Issue: "Table 'Register' not found"
**Solution:**
1. Make sure table name is exactly `Register` (case-sensitive)
2. Go to Supabase dashboard and verify table exists
3. Check table columns match the required structure

### Issue: "Bucket 'id_proof' not found"
**Solution:**
1. Make sure bucket name is exactly `id_proof` (case-sensitive)
2. Go to Supabase Storage and verify bucket exists
3. Make sure bucket is set to "Public"

### Issue: "Registration successful but Supabase save failed"
**Solutions:**
1. Check your terminal/console for detailed error messages
2. Verify your Supabase credentials in `.env`
3. Check table column names match exactly (username, password, address, contact)
4. Make sure table columns allow the data types you're inserting

### Issue: "Image upload failed"
**Solutions:**
1. Make sure `id_proof` bucket exists and is public
2. Check file size (Supabase has limits)
3. Verify file is a valid image format (jpg, png, etc.)
4. Check Supabase Storage policies allow uploads

---

## 📝 Additional Notes

- **Password Storage:** Passwords are hashed using Django's password hasher before saving to Supabase
- **Local Database:** The app still uses SQLite locally for Django authentication
- **Dual Storage:** Data is saved to both Supabase and local database for compatibility
- **Error Handling:** If Supabase save fails, registration still succeeds locally (with a warning)

---

## 🎯 Quick Reference

**Environment Variables Needed:**
```env
SUPABASE_URL=your-project-url
SUPABASE_KEY=your-anon-key
SUPABASE_BUCKET=id_proof
SUPABASE_TABLE=Register
```

**Required Supabase Resources:**
- ✅ Table: `Register` (with columns: username, password, address, contact)
- ✅ Storage Bucket: `id_proof` (public)

**Install Commands:**
```bash
pip install django supabase python-dotenv
```

**Run Commands:**
```bash
python manage.py migrate
python manage.py runserver
```

---

## ✅ Success Checklist

- [ ] Virtual environment created and activated
- [ ] All packages installed (`django`, `supabase`, `python-dotenv`)
- [ ] Supabase project created
- [ ] `Register` table created with correct columns
- [ ] `id_proof` storage bucket created (public)
- [ ] `.env` file created with correct credentials
- [ ] Django migrations run successfully
- [ ] Server starts without errors
- [ ] Can register a new user
- [ ] Data appears in Supabase table
- [ ] Image appears in Supabase storage

---

**Need Help?** Check the terminal/console output for detailed error messages that will help identify issues.

