import base64
import os
import pandas as pd
from google.cloud import bigquery, pubsub_v1, storage
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from email import message_from_bytes
 from io import BytesIO
   

   # Initialize clients
bigquery_client = bigquery.Client()
storage_client = storage.Client()


from google.cloud import secretmanager
def access_secret(secret_id):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/YOUR_PROJECT_ID/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode('UTF-8')
         
def process_email(email_content):
       """Process the email content and extract attachments."""
       email_message = message_from_bytes(email_content)
       for part in email_message.walk():
           if part.get_content_maintype() == 'multipart':
               continue
           if part.get('Content-Disposition') is None:
               continue

           filename = part.get_filename()
           if filename and (filename.endswith('.csv') or filename.endswith('.xlsx')):
               attachment = part.get_payload(decode=True)
               return filename, attachment
       return None, None
   
def clean_and_load_data(filename, attachment):
       """Clean the data and load it into BigQuery."""
       if filename.endswith('.csv'):
           df = pd.read_csv(BytesIO(attachment))
       elif filename.endswith('.xlsx'):
           df = pd.read_excel(BytesIO(attachment))

       # Perform data cleaning (example: drop null values)
       df = df.dropna()

       # Load data into BigQuery
       table_id = f"your_dataset.{filename.split('.')[0]}"
       job = bigquery_client.load_table_from_dataframe(df, table_id)
       job.result()  # Wait for the job to complete
       print(f"Data loaded into {table_id}")

def process_email_event(event, context):
       # Fetch credentials from Secret Manager
      client_secret = access_secret('client-secret')
      service_account_key = access_secret('service-account-key')

         # Use the credentials
      creds = Credentials.from_authorized_user_info(client_secret)
      service_account_creds = Credentials.from_service_account_info(service_account_key)

       
       pubsub_message = base64.b64decode(event['data']).decode('utf-8')
       email_id = pubsub_message.split()[-1]  # Extract email ID from Pub/Sub message

       # Fetch the email content using Gmail API
       #creds = Credentials.from_service_account_file('service_account.json')
       service = build('gmail', 'v1', credentials=creds)
       email = service.users().messages().get(userId='me', id=email_id, format='raw').execute()
       email_content = base64.urlsafe_b64decode(email['raw'])

       # Process the email
       filename, attachment = process_email(email_content)
       if filename and attachment:
           clean_and_load_data(filename, attachment)
       else:
           print("No valid attachment found.")  

   
   
