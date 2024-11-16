from celery import shared_task
import pandas as pd
from .models import Company
from celery.result import AsyncResult

@shared_task
def example_task(x, y):
    return x + y

@shared_task(bind=True)
def process_upload(self, file_path):
    print("Processing started...") 
    """
    This task processes the uploaded CSV file and saves data to the database.
    """
    try:
        # Read the CSV file
        data = pd.read_csv(file_path)
        print("CSV file read successfully.")

        # Get the total number of rows to process
        total_rows = len(data)
        print(f"Total rows to process: {total_rows}")

        # Process each row and save to the database
        for index, row in data.iterrows():
            Company.objects.create(
                name=row['name'],
                domain=row['domain'],
                year_founded=row['year_founded'],
                industry=row['industry'],
                size_range=row['size_range'],
                locality=row['locality'],
                country=row['country'],
                linkedin_url=row['linkedin_url'],
                current_employee_estimate=row['current_employee_estimate'],
                total_employee_estimate=row['total_employee_estimate'],
            )
            
            progress = (index + 1) / total_rows * 100
            self.update_state(state='PROGRESS', meta={'progress': progress})
            print(f"Processed row {index + 1}/{total_rows}") 
        
        return "CSV File Processed Successfully"
    except Exception as e:
        return str(e)
