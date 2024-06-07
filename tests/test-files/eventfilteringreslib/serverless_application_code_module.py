# ========================================
# Import Python Modules (Standard Library)
# ========================================
import os

# =========
# Functions
# =========
def handler(event, context):
    s3_bucket_key_1 = 'uploads/my-file.txt'
    s3_bucket_key_2 = 'upload-folder/my-file.txt'
    s3_bucket_key_3 = os.getenv('BUCKET_KEY')
