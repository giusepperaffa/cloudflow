# ========================================
# Import Python Modules (Standard Library)
# ========================================
import os

# =========
# Functions
# =========
def handler(event, context):
    kms_key_alias = os.environ['KMS_KEY_ALIAS']
    region = os.getenv('REGION')
