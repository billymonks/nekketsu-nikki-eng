"""
Split a large translation CSV into smaller batch files of 100 strings each.
"""
import csv
import io
from pathlib import Path

BATCH_SIZE = 100

def split_csv(input_path: Path, output_dir: Path):
    """Split a CSV file into smaller batch files."""
    
    # Read the CSV (handle any NUL characters)
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read().replace('\x00', '')
    
    rows = list(csv.DictReader(io.StringIO(content)))
    total_rows = len(rows)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get the base name without extension
    base_name = input_path.stem  # e.g., "mgdata_62_63"
    
    # Split into batches
    batch_num = 1
    for i in range(0, total_rows, BATCH_SIZE):
        batch_rows = rows[i:i + BATCH_SIZE]
        
        # Create batch filename with zero-padded number
        batch_file = output_dir / f"{base_name}_batch_{batch_num:03d}.csv"
        
        with open(batch_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(
                f, 
                fieldnames=['japanese', 'english', 'context', 'notes'],
                quoting=csv.QUOTE_ALL
            )
            writer.writeheader()
            writer.writerows(batch_rows)
        
        print(f"Created {batch_file.name} ({len(batch_rows)} strings)")
        batch_num += 1
    
    print(f"\nDone! Split {total_rows} strings into {batch_num - 1} batch files.")
    print(f"Output directory: {output_dir}")

if __name__ == "__main__":
    project_dir = Path(__file__).parent.parent
    
    input_csv = project_dir / "translations" / "mgdata_62_63.csv"
    output_dir = project_dir / "translations" / "mgdata_62_63_batches"
    
    if not input_csv.exists():
        print(f"ERROR: Input file not found: {input_csv}")
        exit(1)
    
    split_csv(input_csv, output_dir)
