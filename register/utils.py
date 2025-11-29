import os
from django.conf import settings


def upload_file_to_supabase(file, username):
    """
    Helper function for uploading files to Supabase Storage.
    This is separate from ORM - just for file storage.
    """
    try:
        from supabase import create_client

        SUPABASE_URL = getattr(settings, "SUPABASE_URL")
        SUPABASE_KEY = getattr(settings, "SUPABASE_KEY")
        SUPABASE_BUCKET = getattr(settings, "SUPABASE_BUCKET", "id_proof")

        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        filename = f"{username}_{file.name}"
        file_bytes = file.read()

        supabase.storage.from_(SUPABASE_BUCKET).upload(
            filename,
            file_bytes,
            file_options={"content-type": file.content_type}
        )

        pub = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(filename)
        return pub.get("publicUrl") if isinstance(pub, dict) else str(pub)

    except Exception as e:
        print(f"Upload error: {str(e)}")
        return None