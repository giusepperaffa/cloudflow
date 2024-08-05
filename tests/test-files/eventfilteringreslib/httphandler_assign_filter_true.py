# ---------------------
# Import Python Modules
# ---------------------
import boto3
import os

# -------
# Handler 
# -------
def onHTTPPostEvent(event, context):
    # ---------------------
    # Retrieve message body
    # ---------------------
    msgBodyDict = event['body']
    # -----------------
    # Set S3 bucket key
    # -----------------
    # Folder within the bucket and name of the uploaded file 
    uploadFileName = msgBodyDict + '.txt'
    s3BucketKey = 'uploads/test_file.txt'
    # --------------------------------------------------------
    # Set local path (where the file to be uploaded is stored)
    # --------------------------------------------------------
    localFile = os.path.join('/tmp', uploadFileName)
    # --------------------
    # Call upload_file API
    # --------------------
    # Create a boto3 client object instance
    s3_client = boto3.client('s3')
    s3_client.upload_file(localFile, os.environ['BUCKET_NAME'], s3BucketKey)
    return
