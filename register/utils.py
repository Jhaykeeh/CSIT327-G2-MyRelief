import uuid
import os
from django.conf import settings
from dotenv import load_dotenv
from django.contrib.auth.hashers import make_password

load_dotenv()

# Get Supabase configuration from settings or environment
SUPABASE_URL = getattr(settings, 'SUPABASE_URL', os.getenv("SUPABASE_URL"))
SUPABASE_KEY = getattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', None) or getattr(settings, 'SUPABASE_KEY', os.getenv("SUPABASE_KEY"))
SUPABASE_BUCKET = getattr(settings, 'SUPABASE_BUCKET', os.getenv("SUPABASE_BUCKET", "id_proof"))
SUPABASE_TABLE = getattr(settings, 'SUPABASE_TABLE', os.getenv("SUPABASE_TABLE", "Register"))

# Initialize Supabase client
# Using service_role key if available to bypass RLS, otherwise use anon key
from supabase import create_client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_to_supabase(file, username):
    """
    Uploads an image to Supabase Storage and returns the public URL.
    
    Args:
        file: Django UploadedFile object
        username: Username to associate with the file
        
    Returns:
        str: Public URL of the uploaded file, or None if upload fails
    """
    if not file:
        return None
    
    # Reset file pointer in case it was already read
    file.seek(0)
    
    # Create a unique file name for each upload
    file_extension = file.name.split('.')[-1]
    file_name = f"{username}_{uuid.uuid4()}.{file_extension}"

    # Read file bytes
    file_bytes = file.read()
    
    # Reset file pointer after reading (in case it's used elsewhere)
    file.seek(0)

    # Upload to Supabase bucket
    try:
        # Upload file to Supabase storage
        response = supabase.storage.from_(SUPABASE_BUCKET).upload(
            path=file_name,
            file=file_bytes,
            file_options={"content-type": file.content_type, "upsert": "false"}
        )

        # Check if upload was successful
        if response is None:
            raise Exception("Upload returned None response")
        
        # Check for errors in response
        if hasattr(response, 'error') and response.error:
            raise Exception(f"Upload error: {response.error}")

        # Get the public URL
        public_url_response = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(file_name)
        
        # Extract URL from response
        if isinstance(public_url_response, dict):
            public_url = public_url_response.get('publicUrl', str(public_url_response))
        else:
            public_url = str(public_url_response)
        
        print(f"✅ Successfully uploaded to Supabase: {file_name}")
        return public_url

    except Exception as e:
        error_msg = str(e)
        print(f"❌ Supabase upload error: {error_msg}")
        # Check for specific error types
        if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
            # File already exists, try to get existing URL
            try:
                existing_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(file_name)
                print(f"⚠️ File exists, returning existing URL")
                return str(existing_url) if isinstance(existing_url, dict) else existing_url
            except:
                pass
        return None


def save_to_supabase_table(username, password, address, contact, id_proof_url=None):
    """
    Saves registration data to Supabase Register table.
    
    Args:
        username: User's username
        password: Plain text password (will be hashed)
        address: User's address
        contact: User's contact number
        id_proof_url: Optional URL of the uploaded ID proof image
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Hash the password using Django's password hasher
        hashed_password = make_password(password)
        
        # Prepare data for Supabase table
        data = {
            "username": username,
            "password": hashed_password,  # Store hashed password
            "address": address,
            "contact": contact
        }
        
        # Add id_proof_url if provided (column must exist in Supabase table)
        if id_proof_url:
            data["id_proof"] = id_proof_url  # Using 'id_proof' as column name matching the model
        
        # Insert into Supabase table
        response = supabase.table(SUPABASE_TABLE).insert(data).execute()
        
        # Check if insertion was successful
        # Supabase returns a PostgrestResponse object with .data attribute
        if hasattr(response, 'data'):
            if response.data and len(response.data) > 0:
                print(f"✅ Successfully saved to Supabase table: {username}")
                return True
            else:
                print(f"⚠️ Supabase insert returned no data: {response}")
                return False
        else:
            print(f"❌ Supabase insert error - unexpected response format: {response}")
            return False
            
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Supabase table insert error: {error_msg}")
        # Check if it's a duplicate username error
        if "duplicate" in error_msg.lower() or "unique" in error_msg.lower() or "violates unique constraint" in error_msg.lower():
            print(f"   Username '{username}' already exists in Supabase")
        return False


def get_from_supabase_table(username):
    """
    Retrieves user data from Supabase Register table.
    
    Args:
        username: Username to search for
        
    Returns:
        dict: User data if found, None otherwise
    """
    try:
        # Query Supabase table
        response = supabase.table(SUPABASE_TABLE).select("*").eq("username", username).execute()
        
        # Check if data was found
        if hasattr(response, 'data') and response.data and len(response.data) > 0:
            user_data = response.data[0]
            print(f"✅ Successfully retrieved from Supabase: {username}")
            return user_data
        else:
            print(f"⚠️ No user found in Supabase: {username}")
            return None
            
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Supabase table retrieve error: {error_msg}")
        return None
