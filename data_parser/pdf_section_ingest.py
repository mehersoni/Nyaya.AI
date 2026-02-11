import re
from pathlib import Path
from typing import List, Dict, Optional
from data_parser.pdf_parser import extract_pdf_text

# Enhanced patterns for better section detection
SECTION_RE = re.compile(
    r"^(\d{1,3})\.\s+(.+?)\.?$"
)

CHAPTER_RE = re.compile(r"^CHAPTER\s+([IVXLC]+)", re.IGNORECASE)

# Pattern to detect chapter titles (all caps)
CHAPTER_TITLE_RE = re.compile(r"^[A-Z\s,.-]+\.$")

def extract_sections_from_pdf(pdf_path: Path) -> List[Dict]:
    """
    Enhanced section extraction with complete CPA 2019 coverage.
    Includes page number tracking and source PDF references.
    """
    # Get structured page data instead of raw text
    pages_data = extract_pdf_text(pdf_path)
    
    sections = []
    current_section = None
    current_chapter = None
    current_chapter_title = None
    
    # Process each page to maintain page number tracking
    for page_data in pages_data:
        page_number = page_data["page_number"]
        lines = page_data["text"].split("\n")
        
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detect chapter headers
            chap_match = CHAPTER_RE.match(line)
            if chap_match:
                roman = chap_match.group(1)
                current_chapter = f"CPA_2019_CH{roman}"
                current_chapter_title = None
                continue
            
            # Detect chapter titles (usually all caps after chapter number)
            if current_chapter and not current_chapter_title and CHAPTER_TITLE_RE.match(line):
                current_chapter_title = line
                continue

            # Detect section start
            sec_match = SECTION_RE.match(line)
            if sec_match:
                # Save previous section
                if current_section:
                    sections.append(current_section)

                number = sec_match.group(1)
                title = sec_match.group(2).strip()
                
                current_section = {
                    "section_id": f"CPA_2019_S{number}",
                    "act": "Consumer Protection Act, 2019",
                    "section_number": number,
                    "title": title,
                    "text": line,
                    "chapter": current_chapter,
                    "chapter_title": current_chapter_title,
                    "source_pdf": pdf_path.name,
                    "page_numbers": [page_number],
                    "start_page": page_number
                }
                continue

            # Accumulate section body
            if current_section:
                current_section["text"] += " " + line
                # Track all pages this section spans
                if page_number not in current_section["page_numbers"]:
                    current_section["page_numbers"].append(page_number)

    # Don't forget the last section
    if current_section:
        sections.append(current_section)

    # Post-process to add end page and clean up
    for section in sections:
        section["end_page"] = section["page_numbers"][-1]
        section["page_count"] = len(section["page_numbers"])
        # Convert page_numbers list to comma-separated string for JSON compatibility
        section["page_range"] = f"{section['start_page']}-{section['end_page']}" if section['start_page'] != section['end_page'] else str(section['start_page'])

    return sections

def enhance_existing_sections(sections_data_path: Path, pdf_path: Path) -> List[Dict]:
    """
    Enhance existing sections data with missing metadata.
    """
    import json
    
    # Load existing sections
    with open(sections_data_path, 'r', encoding='utf-8') as f:
        existing_sections = json.load(f)
    
    # Extract enhanced sections from PDF
    enhanced_sections = extract_sections_from_pdf(pdf_path)
    
    # Create mapping for enhancement
    enhanced_map = {s["section_id"]: s for s in enhanced_sections}
    
    # Enhance existing sections
    for section in existing_sections:
        section_id = section["section_id"]
        if section_id in enhanced_map:
            enhanced = enhanced_map[section_id]
            # Add missing fields
            section.update({
                "title": enhanced.get("title", ""),
                "chapter_title": enhanced.get("chapter_title", ""),
                "source_pdf": enhanced.get("source_pdf", ""),
                "page_numbers": enhanced.get("page_numbers", []),
                "start_page": enhanced.get("start_page", 0),
                "end_page": enhanced.get("end_page", 0),
                "page_count": enhanced.get("page_count", 0),
                "page_range": enhanced.get("page_range", "")
            })
    
    return existing_sections
