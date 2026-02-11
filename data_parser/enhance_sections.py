#!/usr/bin/env python3
"""
Script to enhance existing sections data with complete CPA 2019 coverage.
Adds page number tracking and source PDF references.
"""

import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from data_parser.pdf_section_ingest import enhance_existing_sections

def main():
    """Enhance existing sections data with metadata."""
    root_path = Path(__file__).parent.parent
    sections_data_path = root_path / "knowledge_graph/nodes/sections.data.json"
    pdf_path = root_path / "data_parser/source_pdfs/consumer_protection_act_2019.pdf"
    
    print("Enhancing sections data with complete CPA 2019 coverage...")
    
    # Enhance existing sections
    enhanced_sections = enhance_existing_sections(sections_data_path, pdf_path)
    
    # Write enhanced data back
    with open(sections_data_path, 'w', encoding='utf-8') as f:
        json.dump(enhanced_sections, f, indent=2, ensure_ascii=False)
    
    print(f"Enhanced {len(enhanced_sections)} sections with metadata")
    
    # Print sample of enhanced data
    if enhanced_sections:
        sample = enhanced_sections[0]
        print("\nSample enhanced section:")
        for key, value in sample.items():
            print(f"  {key}: {value}")

if __name__ == "__main__":
    main()