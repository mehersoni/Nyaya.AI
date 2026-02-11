import re
from pathlib import Path
import json
from typing import List, Dict, Tuple

# Enhanced clause patterns for Indian legal documents
CLAUSE_PATTERNS = {
    # Primary clauses: (1), (2), (3) ...
    'numeric': re.compile(r'\((\d+)\)'),
    # Sub-clauses: (a), (b), (c) ...
    'alpha': re.compile(r'\(([a-z])\)'),
    # Roman sub-clauses: (i), (ii), (iii), (iv), (v) ...
    'roman': re.compile(r'\(([ivxlc]+)\)'),
    # Sub-sections: sub-section (1), sub-section (2) ...
    'subsection': re.compile(r'sub-section\s*\((\d+)\)', re.IGNORECASE),
    # Proviso clauses: "Provided that", "Provided further that"
    'proviso': re.compile(r'(Provided\s+(?:further\s+)?that)', re.IGNORECASE),
    # Explanation clauses: "Explanation", "Explanation 1", "Explanation 2"
    'explanation': re.compile(r'(Explanation(?:\s+\d+)?)', re.IGNORECASE),
    # Colon-separated clauses: text ending with colon followed by content
    'colon_clause': re.compile(r':\s*(?=[A-Z])', re.IGNORECASE),
    # Semicolon-separated items in lists
    'semicolon_item': re.compile(r';\s*(?=and\s+[a-z])', re.IGNORECASE),
    # "and" separated final items in lists
    'and_item': re.compile(r';\s*and\s+', re.IGNORECASE)
}

# Enhanced sentence boundary patterns
SENTENCE_BOUNDARIES = re.compile(r'[.;:](?=\s+[A-Z(])')

# Legal list patterns for structured content
LIST_PATTERNS = {
    # Numbered lists: 1., 2., 3.
    'numbered_list': re.compile(r'(?:^|\s)(\d+)\.\s+(?=[A-Z])', re.MULTILINE),
    # Lettered lists: a., b., c.
    'lettered_list': re.compile(r'(?:^|\s)([a-z])\.\s+(?=[A-Z])', re.MULTILINE),
    # Dash/bullet lists: -, •, *
    'bullet_list': re.compile(r'(?:^|\s)[-•*]\s+(?=[A-Z])', re.MULTILINE)
}


def _load(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_list_items(text: str) -> List[Dict]:
    """
    Extract structured list items from legal text.
    """
    list_items = []
    
    for list_type, pattern in LIST_PATTERNS.items():
        for match in pattern.finditer(text):
            list_items.append({
                'type': f'list_{list_type}',
                'label': match.group(0).strip(),
                'identifier': match.group(1) if match.groups() else str(len(list_items) + 1),
                'start': match.start(),
                'end': match.end(),
                'match': match
            })
    
    return list_items


def extract_colon_separated_clauses(text: str) -> List[Dict]:
    """
    Extract clauses separated by colons, which often indicate structured legal content.
    """
    colon_clauses = []
    
    # Find colon positions
    colon_matches = list(re.finditer(r':\s*(?=[A-Z])', text))
    
    for i, match in enumerate(colon_matches):
        # Find the sentence that ends with this colon
        sentence_start = text.rfind('.', 0, match.start())
        if sentence_start == -1:
            sentence_start = 0
        else:
            sentence_start += 1
        
        # The main clause is before the colon
        main_clause = text[sentence_start:match.start()].strip()
        
        if len(main_clause) > 20:  # Only meaningful clauses
            colon_clauses.append({
                'type': 'main_clause',
                'label': 'Main Clause',
                'identifier': f'main_{i+1}',
                'text': main_clause,
                'start': sentence_start,
                'end': match.start()
            })
        
        # Find the dependent clause after the colon
        next_colon = colon_matches[i + 1].start() if i + 1 < len(colon_matches) else len(text)
        next_period = text.find('.', match.end())
        
        if next_period != -1 and next_period < next_colon:
            dependent_end = next_period
        else:
            dependent_end = next_colon
        
        dependent_clause = text[match.end():dependent_end].strip()
        
        if len(dependent_clause) > 20:  # Only meaningful clauses
            colon_clauses.append({
                'type': 'dependent_clause',
                'label': 'Dependent Clause',
                'identifier': f'dep_{i+1}',
                'text': dependent_clause,
                'start': match.end(),
                'end': dependent_end
            })
    
    return colon_clauses


def extract_semicolon_items(text: str) -> List[Dict]:
    """
    Extract items separated by semicolons, common in legal enumerations.
    """
    semicolon_items = []
    
    # Find semicolon-separated items
    semicolon_pattern = re.compile(r'([^;.]+);(?:\s*and\s+([^;.]+))?', re.IGNORECASE)
    
    for match in semicolon_pattern.finditer(text):
        item1 = match.group(1).strip()
        if len(item1) > 10:
            semicolon_items.append({
                'type': 'semicolon_item',
                'label': 'List Item',
                'identifier': str(len(semicolon_items) + 1),
                'text': item1,
                'start': match.start(1),
                'end': match.end(1)
            })
        
        if match.group(2):  # "and" item
            item2 = match.group(2).strip()
            if len(item2) > 10:
                semicolon_items.append({
                    'type': 'final_item',
                    'label': 'Final Item',
                    'identifier': str(len(semicolon_items) + 1),
                    'text': item2,
                    'start': match.start(2),
                    'end': match.end(2)
                })
    
    return semicolon_items


def extract_clause_boundaries(text: str) -> List[Dict]:
    """
    Extract clause boundaries using multiple patterns and heuristics.
    Returns list of clause information with positions.
    """
    boundaries = []
    
    # Find all pattern matches with their positions
    for pattern_name, pattern in CLAUSE_PATTERNS.items():
        for match in pattern.finditer(text):
            boundaries.append({
                'type': pattern_name,
                'label': match.group(0),
                'identifier': match.group(1) if match.groups() else match.group(0),
                'start': match.start(),
                'end': match.end(),
                'match': match
            })
    
    # Add structured list items
    list_items = extract_list_items(text)
    boundaries.extend(list_items)
    
    # Add colon-separated clauses
    colon_clauses = extract_colon_separated_clauses(text)
    boundaries.extend(colon_clauses)
    
    # Add semicolon-separated items
    semicolon_items = extract_semicolon_items(text)
    boundaries.extend(semicolon_items)
    
    # Sort by position in text
    boundaries.sort(key=lambda x: x['start'])
    
    return boundaries


def extract_sentence_clauses(text: str) -> List[Dict]:
    """
    Extract clauses based on sentence boundaries for sections without explicit clause markers.
    Enhanced to handle complex sentence structures.
    """
    # Enhanced sentence splitting that preserves legal structure
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text.strip())
    
    # Also split on colons followed by capital letters (legal structure)
    enhanced_sentences = []
    for sentence in sentences:
        colon_parts = re.split(r':\s+(?=[A-Z])', sentence)
        enhanced_sentences.extend(colon_parts)
    
    # Filter and process sentences
    valid_sentences = []
    for i, sentence in enumerate(enhanced_sentences):
        sentence = sentence.strip()
        
        # Skip section headers (usually just numbers and titles)
        if re.match(r'^\d+\.\s*[A-Z][^.]*\.$', sentence):
            continue
            
        # Skip very short sentences
        if len(sentence) < 25:  # Increased minimum length
            continue
            
        # Skip sentences that are just references
        if re.match(r'^(Section|Chapter|Act|Rule)\s+\d+', sentence, re.IGNORECASE):
            continue
        
        # Skip sentences that are just single words or short phrases
        if len(sentence.split()) < 5:
            continue
            
        valid_sentences.append({
            'type': 'sentence',
            'label': f'Sentence {i+1}',
            'identifier': str(i+1),
            'text': sentence,
            'start': 0,  # We'll calculate this if needed
            'end': len(sentence)
        })
    
    return valid_sentences


def is_valid_clause_start(text: str, boundary: Dict) -> bool:
    """
    Enhanced validation for clause boundaries.
    """
    # Skip validation for structured clauses that we explicitly extracted
    if boundary['type'] in ['main_clause', 'dependent_clause', 'semicolon_item', 'final_item']:
        return True
    
    # Get context around the boundary
    start = max(0, boundary['start'] - 50)
    end = min(len(text), boundary['end'] + 50)
    context = text[start:end]
    
    # Skip if it's a reference to another section/act
    reference_patterns = [
        r'section\s+\d+',
        r'clause\s*\([a-z0-9]+\)\s+of',
        r'sub-section\s*\(\d+\)\s+of\s+section',
        r'under\s+sub-section',
        r'in\s+sub-section',
        r'Code\s+of\s+Criminal\s+Procedure',
        r'Act\s+of\s+\d{4}',
        r'notification\s+dated'
    ]
    
    for ref_pattern in reference_patterns:
        if re.search(ref_pattern, context, re.IGNORECASE):
            return False
    
    # For numeric clauses, ensure they start at sentence boundaries or after colons
    if boundary['type'] == 'numeric':
        # Check if preceded by sentence boundary or colon
        before_text = text[max(0, boundary['start'] - 15):boundary['start']]
        if not (before_text.strip().endswith(('.', ':', ';')) or 
                before_text.strip() == '' or
                re.search(r'[.;:]\s*$', before_text)):
            return False
    
    return True


def extract_clause_text(text: str, current_boundary: Dict, next_boundary: Dict = None) -> str:
    """
    Extract text for a clause between boundaries.
    Enhanced to handle structured clauses.
    """
    # For structured clauses, return the pre-extracted text
    if 'text' in current_boundary:
        return current_boundary['text']
    
    start = current_boundary['end']
    
    if next_boundary:
        end = next_boundary['start']
    else:
        end = len(text)
    
    clause_text = text[start:end].strip()
    
    # Clean up clause text
    # Remove trailing punctuation that belongs to the next clause
    clause_text = re.sub(r'[;,]\s*$', '.', clause_text)
    
    # Ensure it ends with proper punctuation
    if clause_text and not clause_text.endswith(('.', ';', ':')):
        clause_text += '.'
    
    return clause_text


def parse_clauses_from_text(section_id: str, text: str) -> Tuple[List[Dict], List[Dict]]:
    """
    Enhanced clause parsing with support for multiple clause types and legal structures.
    """
    clauses = []
    edges = []
    
    # Extract all potential clause boundaries
    boundaries = extract_clause_boundaries(text)
    
    # Filter valid clause boundaries
    valid_boundaries = [b for b in boundaries if is_valid_clause_start(text, b)]
    
    # If no explicit clause markers found, try sentence-based extraction for longer sections
    if not valid_boundaries and len(text) > 200:
        sentence_clauses = extract_sentence_clauses(text)
        if len(sentence_clauses) > 1:  # Only if multiple sentences
            valid_boundaries = sentence_clauses
    
    if not valid_boundaries:
        return clauses, edges
    
    # Process each valid boundary
    for i, boundary in enumerate(valid_boundaries):
        next_boundary = valid_boundaries[i + 1] if i + 1 < len(valid_boundaries) else None
        
        # Extract clause text
        clause_text = extract_clause_text(text, boundary, next_boundary)
        
        if not clause_text or len(clause_text.strip()) < 10:  # Skip very short clauses
            continue
        
        # Generate clause ID based on type
        if boundary['type'] == 'numeric':
            clause_id = f"{section_id}_{boundary['identifier']}"
        elif boundary['type'] == 'alpha':
            clause_id = f"{section_id}_{boundary['identifier']}"
        elif boundary['type'] == 'roman':
            clause_id = f"{section_id}_{boundary['identifier']}"
        elif boundary['type'] == 'subsection':
            clause_id = f"{section_id}_sub_{boundary['identifier']}"
        elif boundary['type'] == 'proviso':
            clause_id = f"{section_id}_proviso_{i}"
        elif boundary['type'] == 'explanation':
            clause_id = f"{section_id}_explanation_{i}"
        elif boundary['type'] == 'main_clause':
            clause_id = f"{section_id}_main_{boundary['identifier']}"
        elif boundary['type'] == 'dependent_clause':
            clause_id = f"{section_id}_dep_{boundary['identifier']}"
        elif boundary['type'] == 'semicolon_item':
            clause_id = f"{section_id}_item_{boundary['identifier']}"
        elif boundary['type'] == 'final_item':
            clause_id = f"{section_id}_final_{boundary['identifier']}"
        elif boundary['type'].startswith('list_'):
            clause_id = f"{section_id}_list_{boundary['identifier']}"
        elif boundary['type'] == 'sentence':
            clause_id = f"{section_id}_sent_{boundary['identifier']}"
        else:
            clause_id = f"{section_id}_clause_{i}"
        
        clauses.append({
            "clause_id": clause_id,
            "parent_section": section_id,
            "label": boundary['label'],
            "text": clause_text,
            "clause_type": boundary['type']
        })
        
        edges.append({
            "parent": section_id,
            "child": clause_id,
            "relation": "contains_clause"
        })
    
    return clauses, edges


def parse_clauses(root: Path):
    sections = _load(root / "knowledge_graph/nodes/sections.data.json")

    all_clauses = []
    all_edges = []

    for section in sections:
        section_id = section["section_id"]
        text = section.get("text", "")

        if not text:
            continue

        clauses, edges = parse_clauses_from_text(section_id, text)

        all_clauses.extend(clauses)
        all_edges.extend(edges)

    return all_clauses, all_edges
