#!/usr/bin/env python3
"""
Check for translations where English is longer than Japanese (in Shift-JIS bytes).
These will be truncated during replacement and may cause issues.

Outputs a _toolong.csv file for each batch with issues.
"""
import csv
import io
from pathlib import Path


def get_byte_length(text: str) -> int:
    """Get the byte length of text in Shift-JIS encoding."""
    try:
        return len(text.encode('shift_jis'))
    except UnicodeEncodeError:
        # If it can't be encoded, estimate based on character types
        length = 0
        for char in text:
            if ord(char) < 128:
                length += 1
            else:
                length += 2
        return length


def check_csv(csv_path: Path) -> list:
    """Check a CSV file for translations that are too long. Returns list of issues with full row data."""
    issues = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        content = f.read().replace('\x00', '')
    
    reader = csv.DictReader(io.StringIO(content))
    for line_num, row in enumerate(reader, start=2):  # Start at 2 (header is line 1)
        jp = row.get('japanese', '').strip()
        en = row.get('english', '').strip()
        context = row.get('context', '').strip()
        notes = row.get('notes', '').strip()
        
        if not jp or not en:
            continue
        
        jp_bytes = get_byte_length(jp)
        en_bytes = get_byte_length(en)
        
        if en_bytes > jp_bytes:
            overflow = en_bytes - jp_bytes
            issues.append({
                'line': line_num,
                'japanese': jp,
                'english': en,
                'context': context,
                'notes': notes,
                'jp_bytes': jp_bytes,
                'en_bytes': en_bytes,
                'overflow': overflow
            })
    
    return issues


def write_issues_csv(batch_path: Path, issues: list, output_dir: Path):
    """Write issues to a CSV file for a specific batch."""
    # Create output filename
    output_name = batch_path.stem + "_toolong.csv"
    output_path = output_dir / output_name
    
    # Sort by overflow (worst first)
    issues.sort(key=lambda x: x['overflow'], reverse=True)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        # Header with extra columns for byte info
        writer.writerow(['japanese', 'english', 'context', 'notes', 'jp_bytes', 'en_bytes', 'overflow'])
        
        for issue in issues:
            writer.writerow([
                issue['japanese'],
                issue['english'],
                issue['context'],
                issue['notes'],
                issue['jp_bytes'],
                issue['en_bytes'],
                issue['overflow']
            ])
    
    return output_path


def cleanup_empty_reports(output_dir: Path) -> int:
    """Remove toolong report files that only have a header (no issues left)."""
    removed = 0
    
    if not output_dir.exists():
        return 0
    
    for report_file in output_dir.glob("*_toolong.csv"):
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # Count non-empty lines
            lines = [line for line in content.split('\n') if line.strip()]
            
            # If only header line (or empty), delete the file
            if len(lines) <= 1:
                report_file.unlink()
                print(f"  Removed empty report: {report_file.name}")
                removed += 1
        except Exception as e:
            print(f"  Warning: Could not process {report_file.name}: {e}")
    
    return removed


def check_batch_dir(batch_dir: Path, output_dir: Path):
    """Check all batch CSV files and output issues to separate files."""
    batch_files = sorted(batch_dir.glob("*_batch_*.csv"))
    total_issues = 0
    files_with_issues = 0
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # First, clean up any empty reports from previous runs
    removed = cleanup_empty_reports(output_dir)
    if removed > 0:
        print(f"Cleaned up {removed} empty report(s)")
        print("-" * 40)
    
    for batch_file in batch_files:
        issues = check_csv(batch_file)
        
        if issues:
            output_path = write_issues_csv(batch_file, issues, output_dir)
            print(f"  {batch_file.name}: {len(issues)} issues -> {output_path.name}")
            total_issues += len(issues)
            files_with_issues += 1
        else:
            # If no issues, remove any existing toolong report for this batch
            report_name = batch_file.stem + "_toolong.csv"
            report_path = output_dir / report_name
            if report_path.exists():
                report_path.unlink()
                print(f"  {batch_file.name}: All fixed! Removed {report_name}")
    
    return total_issues, files_with_issues


def main():
    project_dir = Path(__file__).parent.parent
    batch_dir = project_dir / "translations" / "mgdata_62_63_batches"
    output_dir = project_dir / "translations" / "toolong_reports"
    
    if not batch_dir.exists():
        print(f"ERROR: Batch directory not found: {batch_dir}")
        return 1
    
    print("Checking translation lengths...")
    print(f"Output directory: {output_dir}")
    print("=" * 80)
    
    total_issues, files_with_issues = check_batch_dir(batch_dir, output_dir)
    
    print("=" * 80)
    
    if total_issues == 0:
        print("✅ All translations fit within byte limits!")
        return 0
    
    print(f"\n⚠️  Found {total_issues} translations that are TOO LONG")
    print(f"   across {files_with_issues} batch files")
    print(f"\nReports written to: {output_dir}")
    print("\nEach report CSV contains:")
    print("  - japanese: Original text")
    print("  - english: Translation (needs shortening)")
    print("  - context/notes: Original metadata")
    print("  - jp_bytes/en_bytes: Byte lengths")
    print("  - overflow: How many bytes to cut")
    
    return 1


if __name__ == '__main__':
    exit(main())
