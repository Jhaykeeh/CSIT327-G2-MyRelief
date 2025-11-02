import uuid
import os
from django.conf import settings
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "id_proof")

# Initialize Supabase client
from supabase import create_client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_to_supabase(file, username):
    """Uploads an image to Supabase Storage and returns the public URL."""

    # Create a unique file name for each upload
    file_extension = file.name.split('.')[-1]
    file_name = f"{username}_{uuid.uuid4()}.{file_extension}"

    # Read file bytes
    file_bytes = file.read()

    # Upload to Supabase bucket
    try:
        response = supabase.storage.from_(SUPABASE_BUCKET).upload(
            path=file_name,
            file=file_bytes,
            file_options={"content-type": file.content_type}
        )

        # If upload failed
        if response is None or "error" in str(response).lower():
            raise Exception(f"Upload failed: {response}")

        # Get the public URL
        public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(file_name)
        return public_url

    except Exception as e:
        print(f"❌ Supabase upload error: {e}")
        return None
