from src.log import log_progress
from src.transform import transform
from src.extract import extract
from src.load_to_csv import load_data

target_file = "data/transformed_data.csv" 

if __name__ == "__main__":
    # Log the initialization of the ETL process 
    log_progress("ETL Job Started") 
 
    # Log the beginning of the Extraction process 
    log_progress("Extract phase Started") 
    extracted_data = extract() 
 
    # Log the completion of the Extraction process 
    log_progress("Extract phase Ended") 
 
    # Log the beginning of the Transformation process 
    log_progress("Transform phase Started") 
    transformed_data = transform(extracted_data) 
    print("Transformed Data") 
    print(transformed_data) 
 
    # Log the completion of the Transformation process 
    log_progress("Transform phase Ended") 
 
    # Log the beginning of the Loading process 
    log_progress("Load phase Started") 
    load_data(target_file,transformed_data) 
 
    # Log the completion of the Loading process 
    log_progress("Load phase Ended") 
 
    # Log the completion of the ETL process 
    log_progress("ETL Job Ended") 
