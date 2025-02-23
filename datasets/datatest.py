import pandas as pd
import os

# Set paths to current working directory
dataset_path = os.path.dirname(os.path.abspath(__file__))
output_folder = os.path.join(dataset_path, "reports")
output_file = os.path.join(output_folder, "data.txt")

# Create output directory if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Get all CSV files
csv_files = [f for f in os.listdir(dataset_path) if f.endswith('.csv')]

# Generate report
report = []
for csv_file in csv_files:
    df = pd.read_csv(os.path.join(dataset_path, csv_file))
    report.append(f"\nReport for {csv_file}:")
    report.append(f"Number of rows: {len(df)}")
    report.append(f"Number of columns: {len(df.columns)}")
    report.append(f"Columns: {', '.join(df.columns)}")
    report.append(f"Data types:\n{df.dtypes.to_string()}")
    report.append(f"Summary statistics:\n{df.describe().to_string()}")
    report.append("-" * 80)

# Write report to file
with open(output_file, 'w') as f:
    f.write('\n'.join(report))