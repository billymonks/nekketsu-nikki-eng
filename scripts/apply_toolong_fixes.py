#!/usr/bin/env python3
"""
Apply shortened translations from toolong reports back to original batch files.

Reads each *_toolong.csv file from translations/toolong_reports/
and updates the corresponding batch file with the shortened English translations.
"""
import csv
import io
from pathlib import Path


def load_toolong_fixes(toolong_path: Path) -> dict:
    """Load fixes from a toolong CSV. Returns dict mapping japanese -> new english."""
    fixes = {}
    
    with open(toolong_path, 'r', encoding='utf-8') as f:
        content = f.read().replace('\x00', '')
    
    reader = csv.DictReader(io.StringIO(content))
    for row in reader:
        jp = row.get('japanese', '').strip()
        en = row.get('english', '').strip()
        if jp and en:
            fixes[jp] = en
    
    return fixes


def apply_fixes_to_batch(batch_path: Path, fixes: dict) -> tuple[int, list]:
    """
    Apply fixes to a batch file.
    Returns (number of fixes applied, list of unmatched japanese texts).
    """
    # Read original batch file
    with open(batch_path, 'r', encoding='utf-8') as f:
        content = f.read().replace('\x00', '')
    
    reader = csv.DictReader(io.StringIO(content))
    fieldnames = reader.fieldnames
    rows = list(reader)
    
    # Track what we matched
    matched_jp = set()
    fixes_applied = 0
    
    # Apply fixes
    for row in rows:
        jp = row.get('japanese', '').strip()
        if jp in fixes:
            old_en = row.get('english', '')
            new_en = fixes[jp]
            if old_en != new_en:
                row['english'] = new_en
                fixes_applied += 1
            matched_jp.add(jp)
    
    # Find unmatched
    unmatched = [jp for jp in fixes.keys() if jp not in matched_jp]
    
    # Write back
    with open(batch_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)
    
    return fixes_applied, unmatched


def main():
    project_dir = Path(__file__).parent.parent
    batch_dir = project_dir / "translations" / "mgdata_62_63_batches"
    toolong_dir = project_dir / "translations" / "toolong_reports"
    
    if not toolong_dir.exists():
        print(f"ERROR: Toolong reports directory not found: {toolong_dir}")
        return 1
    
    toolong_files = sorted(toolong_dir.glob("*_toolong.csv"))
    
    if not toolong_files:
        print("No toolong CSV files found.")
        return 0
    
    print(f"Found {len(toolong_files)} toolong report files")
    print("=" * 80)
    
    total_fixes = 0
    all_unmatched = []
    
    for toolong_path in toolong_files:
        # Derive original batch filename
        # mgdata_62_63_batch_001_toolong.csv -> mgdata_62_63_batch_001.csv
        batch_name = toolong_path.stem.replace("_toolong", "") + ".csv"
        batch_path = batch_dir / batch_name
        
        if not batch_path.exists():
            print(f"WARNING: Original batch not found: {batch_path}")
            continue
        
        # Load fixes
        fixes = load_toolong_fixes(toolong_path)
        
        if not fixes:
            continue
        
        # Apply fixes
        fixes_applied, unmatched = apply_fixes_to_batch(batch_path, fixes)
        
        if fixes_applied > 0 or unmatched:
            print(f"{batch_name}: {fixes_applied} fixes applied", end="")
            if unmatched:
                print(f", {len(unmatched)} unmatched")
                for jp in unmatched:
                    all_unmatched.append((batch_name, jp))
            else:
                print()
        
        total_fixes += fixes_applied
    
    print("=" * 80)
    print(f"Total fixes applied: {total_fixes}")
    
    if all_unmatched:
        print(f"\n⚠️  {len(all_unmatched)} Japanese texts not found in original batches:")
        for batch_name, jp in all_unmatched:
            print(f"  [{batch_name}] {jp[:60]}{'...' if len(jp) > 60 else ''}")
    else:
        print("\n✅ All Japanese texts matched successfully!")
    
    return 0


if __name__ == '__main__':
    exit(main())
