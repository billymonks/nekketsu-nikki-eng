"""
Merge translated batch CSV files back into a single file.
"""
import csv
import io
from pathlib import Path

def merge_batches(batch_dir: Path, output_file: Path):
    """Merge all batch CSV files back into one file."""
    
    # Find all batch files, sorted by number
    batch_files = sorted(batch_dir.glob("*_batch_*.csv"))
    
    if not batch_files:
        print(f"ERROR: No batch files found in {batch_dir}")
        return
    
    print(f"Found {len(batch_files)} batch files")
    
    all_rows = []
    
    for batch_file in batch_files:
        with open(batch_file, 'r', encoding='utf-8') as f:
            content = f.read().replace('\x00', '')
        
        rows = list(csv.DictReader(io.StringIO(content)))
        all_rows.extend(rows)
        
        # Count translated lines in this batch
        translated = sum(1 for r in rows if r.get('english'))
        print(f"  {batch_file.name}: {len(rows)} strings, {translated} translated")
    
    # Write merged file
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=['japanese', 'english', 'context', 'notes'],
            quoting=csv.QUOTE_ALL
        )
        writer.writeheader()
        writer.writerows(all_rows)
    
    total_translated = sum(1 for r in all_rows if r.get('english'))
    print(f"\nMerged {len(all_rows)} strings into {output_file.name}")
    print(f"Total translated: {total_translated}/{len(all_rows)} ({100*total_translated//len(all_rows)}%)")

if __name__ == "__main__":
    project_dir = Path(__file__).parent.parent
    
    batch_dir = project_dir / "translations" / "mgdata_62_63_batches"
    output_file = project_dir / "translations" / "mgdata_62_63.csv"
    
    if not batch_dir.exists():
        print(f"ERROR: Batch directory not found: {batch_dir}")
        exit(1)
    
    merge_batches(batch_dir, output_file)
