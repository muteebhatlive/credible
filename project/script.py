# import_csv_into_django_model.py
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()
import pandas as pd
from app.models import Customer, Loan

excel_file_path = 'C:/Users/mutee/OneDrive/Documents/credit_system/customer_data.xlsx'
loan_path = 'C:/Users/mutee/OneDrive/Documents/credit_system/loan_data.xlsx'
# Read Excel file into a DataFrame
df = pd.read_excel(excel_file_path)

# Iterate over rows and import into Django model
for index, row in df.iterrows():
    instance = Customer(
        customer_id = row['Customer ID'],
        first_name = row['First Name'],
        last_name = row['Last Name'],
        age = row['Age'],
        phone_number = row['Phone Number'],
        monthly_salary = row['Monthly Salary'],
        approved_limit = row['Approved Limit'],

    )
    instance.save()
    print('done1')
# Read Excel file into a DataFrame
df = pd.read_excel(loan_path)

# Iterate over rows and import into Django model
for index, row in df.iterrows():
    instance = Loan(
        customer_id=row['Customer ID'],
        loan_id=row['Loan ID'],
        loan_amount=row['Loan Amount'],
        tenure=row['Tenure'],
        interest_rate=row['Interest Rate'],
        monthly_payment=row['Monthly payment'],
        emis_paid_on_time=row['EMIs paid on Time'],
        start_date=row['Date of Approval'],  # Assuming Date of Approval is the start date
        end_date=row['End Date'],
    )
    instance.save()
    
    print('done2')
    