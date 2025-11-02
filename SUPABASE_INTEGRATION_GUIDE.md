# Complete Supabase Integration Guide

This guide explains how Django is connected to Supabase for database operations and image uploads.

---

## 📋 Table of Contents

1. [Configuration](#configuration)
2. [How It Works](#how-it-works)
3. [Code Structure](#code-structure)
4. [RLS Policy Considerations](#rls-policy-considerations)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)

---

## 🔧 Configuration

### 1. Environment Variables (.env file)

Create a `.env` file in your project root with:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-public-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key  # Recommended for backend operations
SUPABASE_BUCKET=id_proof
SUPABASE_TABLE=Register
```

**Where to find these:**
- Go to Supabase Dashboard → Settings → API
- **SUPABASE_URL**: Project URL
- **SUPABASE_KEY**: `anon` `public` key (for client-side operations)
- **SUPABASE_SERVICE_ROLE_KEY**: `service_role` `secret` key (for backend, bypasses RLS)

⚠️ **Important**: The `service_role` key bypasses Row Level Security (RLS). Keep it secret and never expose it to the frontend!

### 2. Django Settings (settings.py)

The Supabase configuration is automatically loaded from environment variables:

```python
# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "id_proof")
SUPABASE_TABLE = os.getenv("SUPABASE_TABLE", "Register")
```

---

## 🔄 How It Works

### Registration Flow (register_view)

1. **Form Validation**: Django form validates user input
2. **Django User Creation**: Creates Django User for authentication
3. **Image Upload**: 
   - Image uploaded to Supabase Storage bucket `id_proof`
   - Returns public URL of the uploaded image
4. **Data Storage**: 
   - All data saved to Supabase `Register` table
   - Image URL stored in `id_proof` column
   - Password hashed before storage
5. **Local Backup**: Data also saved to local Django database (backward compatibility)

### Dashboard/Profile Flow (dashboard_view)

1. **Retrieve from Supabase**: Queries Supabase `Register` table by username
2. **Display Data**: 
   - Shows username, address, contact from Supabase
   - Displays image using Supabase public URL
3. **Fallback**: If Supabase data not found, uses local database

---

## 📁 Code Structure

### register/utils.py

Contains three main functions:

#### 1. `upload_to_supabase(file, username)`
- Uploads image to Supabase Storage
- Returns public URL of uploaded file
- Handles errors and duplicate files

```python
id_proof_url = upload_to_supabase(id_proof, username)
# Returns: "https://your-project.supabase.co/storage/v1/object/public/id_proof/username_uuid.jpg"
```

#### 2. `save_to_supabase_table(username, password, address, contact, id_proof_url)`
- Inserts data into Supabase `Register` table
- Hashes password using Django's password hasher
- Stores image URL in `id_proof` column

```python
success = save_to_supabase_table(
    username="john_doe",
    password="plaintext_password",
    address="123 Main St",
    contact="1234567890",
    id_proof_url="https://..."
)
```

#### 3. `get_from_supabase_table(username)`
- Retrieves user data from Supabase table
- Returns dictionary with user information

```python
user_data = get_from_supabase_table("john_doe")
# Returns: {'username': 'john_doe', 'address': '123 Main St', 'id_proof': 'https://...', ...}
```

---

## 🔒 RLS Policy Considerations

### Your Current RLS Policy

You mentioned this policy for storage:
```sql
(bucket_id = 'id_proof') AND (auth.uid()::text = (storage.foldername(name))[1])
```

### Problem

This policy uses `auth.uid()` which requires Supabase Auth authentication. Since Django handles authentication separately, this policy won't work for Django backend operations.

### Solutions

#### Option 1: Use Service Role Key (Recommended)

The code automatically uses `SUPABASE_SERVICE_ROLE_KEY` if available, which bypasses RLS:

```env
SUPABASE_SERVICE_ROLE_KEY=your-service-role-secret-key
```

**Advantages:**
- ✅ Bypasses all RLS policies
- ✅ Works seamlessly with Django backend
- ✅ No policy changes needed

**Security:**
- ⚠️ Only use on backend (server-side)
- ⚠️ Never expose to frontend/client
- ⚠️ Keep in `.env` file (already in `.gitignore`)

#### Option 2: Modify Storage RLS Policy

Create a policy that allows authenticated service role access:

1. Go to Supabase Dashboard → Storage → Policies
2. Click on `id_proof` bucket
3. Add new policy:

```sql
-- Allow service role (Django backend) to upload
(bucket_id = 'id_proof') AND (
  auth.uid()::text = (storage.foldername(name))[1] OR
  auth.jwt() ->> 'role' = 'service_role'
)
```

#### Option 3: Disable RLS for Storage (Not Recommended)

Only for development/testing:
1. Go to Storage → `id_proof` bucket
2. Disable RLS (not recommended for production)

### Table RLS Policy

For the `Register` table, you may also need RLS policies:

**Option A: Allow authenticated service role**
```sql
-- Allow service role to insert/select
CREATE POLICY "Allow service role operations"
ON "Register"
FOR ALL
USING (auth.jwt() ->> 'role' = 'service_role');
```

**Option B: Disable RLS temporarily (Development only)**
1. Go to Table Editor → `Register` table
2. Click on "Disable RLS" (only for development)

---

## 🧪 Testing

### Test Registration

1. Start Django server:
   ```bash
   python manage.py runserver
   ```

2. Go to registration page:
   ```
   http://127.0.0.1:8000/register/
   ```

3. Fill in form and submit

4. Check Supabase:
   - **Table**: Go to Table Editor → `Register` table → Should see new row
   - **Storage**: Go to Storage → `id_proof` bucket → Should see uploaded image

### Test Dashboard

1. Login with registered user
2. Go to dashboard:
   ```
   http://127.0.0.1:8000/dashboard/<user_id>/
   ```
3. Verify:
   - Username, address, contact displayed
   - Image displayed from Supabase URL

### Console Output

Check your terminal for:
- ✅ `Successfully uploaded to Supabase: filename.jpg`
- ✅ `Successfully saved to Supabase table: username`
- ✅ `Successfully retrieved from Supabase: username`

Or errors:
- ❌ `Supabase upload error: ...`
- ❌ `Supabase table insert error: ...`

---

## 🔍 Troubleshooting

### Issue: "Upload failed" or "403 Forbidden"

**Cause**: RLS policy blocking upload

**Solutions**:
1. Add `SUPABASE_SERVICE_ROLE_KEY` to `.env` file
2. Or modify storage RLS policy (see above)
3. Check bucket is set to "Public"

### Issue: "Table insert error: duplicate key"

**Cause**: Username already exists in Supabase table (unique constraint)

**Solution**: Use a different username or delete existing record

### Issue: "Column 'id_proof' does not exist"

**Cause**: Supabase table missing `id_proof` column

**Solution**: 
1. Go to Table Editor → `Register` table
2. Add column `id_proof` (type: text/varchar)

### Issue: Image not displaying

**Cause**: 
- Image URL not saved correctly
- Bucket not public
- Incorrect URL format

**Solution**:
1. Check Supabase Storage → Bucket settings → Make sure "Public" is checked
2. Verify URL format in database
3. Check browser console for image loading errors

### Issue: "No user found in Supabase"

**Cause**: User data not in Supabase table

**Solution**:
- Data may only be in local database
- Check if registration actually saved to Supabase
- Review console output for errors

---

## 📝 Supabase Table Structure

Your `Register` table should have these columns:

| Column Name | Type | Constraints |
|------------|------|-------------|
| `id` | bigint / serial | Primary Key, Auto-increment |
| `username` | text / varchar | Unique, Not Null |
| `password` | text / varchar | Not Null (hashed) |
| `address` | text / varchar | Not Null |
| `contact` | text / varchar | Not Null |
| `id_proof` | text / varchar | Nullable (stores URL) |

---

## 🔐 Security Best Practices

1. **Never commit `.env` file** (already in `.gitignore`)
2. **Use service_role key only on backend** (never expose to frontend)
3. **Hash passwords** (already implemented using Django's hasher)
4. **Enable RLS in production** (configure policies correctly)
5. **Validate file types** (add validation for image files)
6. **Limit file sizes** (configure Supabase storage limits)

---

## 📚 API Reference

### Supabase Client Methods Used

```python
# Storage Operations
supabase.storage.from_('bucket_name').upload(path, file, options)
supabase.storage.from_('bucket_name').get_public_url(path)

# Table Operations
supabase.table('table_name').insert(data).execute()
supabase.table('table_name').select('*').eq('column', value).execute()
```

---

## ✅ Checklist

- [ ] `.env` file created with Supabase credentials
- [ ] `SUPABASE_SERVICE_ROLE_KEY` added (for RLS bypass)
- [ ] Supabase `Register` table created with correct columns
- [ ] Supabase `id_proof` storage bucket created (public)
- [ ] RLS policies configured (or using service_role key)
- [ ] Packages installed: `django`, `supabase`, `python-dotenv`
- [ ] Tested registration flow
- [ ] Tested dashboard/profile display
- [ ] Verified data in Supabase table
- [ ] Verified images in Supabase storage

---

## 🚀 Next Steps

- Add image update functionality to dashboard
- Sync profile updates to Supabase
- Add image deletion when user updates profile
- Implement proper error handling and user feedback
- Add image validation (file type, size limits)

---

**Need Help?** Check console output for detailed error messages!

