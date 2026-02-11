#!/usr/bin/env python3
"""
Reference detector to find section cross-references in legal text.
Creates reference edges in knowledge graph.
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Tuple, Set

class ReferenceDetector:
    """Detect cross-references between legal sections."""
    
    def __init__(self):
        # Patterns to detect section references
        self.reference_patterns = [
            # Direct section references: "section 2", "Section 10", "sections 15 and 16"
            re.compile(r'\bsections?\s+(\d+(?:\s*(?:and|,|to)\s*\d+)*)', re.IGNORECASE),
            
            # Sub-section references: "sub-section (1)", "sub-sections (2) and (3)"
            re.compile(r'\bsub-sections?\s*\((\d+)\)', re.IGNORECASE),
            
            # Clause references: "clause (a)", "clauses (i) and (ii)"
            re.compile(r'\bclauses?\s*\(([a-z]+|[ivx]+)\)', re.IGNORECASE),
            
            # Chapter references: "Chapter II", "Chapters III and IV"
            re.compile(r'\bchapters?\s+([IVXLC]+(?:\s*(?:and|,|to)\s*[IVXLC]+)*)', re.IGNORECASE),
            
            # Act references: "this Act", "the Act"
            re.compile(r'\b(?:this|the)\s+Act\b', re.IGNORECASE),
            
            # Specific legal references
            re.compile(r'\bunder\s+section\s+(\d+)', re.IGNORECASE),
            re.compile(r'\bin\s+accordance\s+with\s+section\s+(\d+)', re.IGNORECASE),
            re.compile(r'\bas\s+provided\s+in\s+section\s+(\d+)', re.IGNORECASE),
            re.compile(r'\breferred\s+to\s+in\s+section\s+(\d+)', re.IGNORECASE),
            re.compile(r'\bspecified\s+in\s+section\s+(\d+)', re.IGNORECASE),
            
            # Procedural references
            re.compile(r'\bunder\s+sub-section\s*\((\d+)\)', re.IGNORECASE),
            re.compile(r'\bprovisions\s+of\s+section\s+(\d+)', re.IGNORECASE),
        ]
        
        # Patterns for different types of references
        self.reference_types = {
            'direct_reference': [
                re.compile(r'\bsection\s+(\d+)', re.IGNORECASE),
                re.compile(r'\bsections\s+(\d+(?:\s*(?:and|,|to)\s*\d+)*)', re.IGNORECASE),
            ],
            'procedural_reference': [
                re.compile(r'\bunder\s+section\s+(\d+)', re.IGNORECASE),
                re.compile(r'\bin\s+accordance\s+with\s+section\s+(\d+)', re.IGNORECASE),
                re.compile(r'\bas\s+provided\s+in\s+section\s+(\d+)', re.IGNORECASE),
            ],
            'definitional_reference': [
                re.compile(r'\bas\s+defined\s+in\s+section\s+(\d+)', re.IGNORECASE),
                re.compile(r'\bmeaning\s+assigned.*section\s+(\d+)', re.IGNORECASE),
            ],
            'conditional_reference': [
                re.compile(r'\bsubject\s+to.*section\s+(\d+)', re.IGNORECASE),
                re.compile(r'\bexcept\s+as\s+provided\s+in\s+section\s+(\d+)', re.IGNORECASE),
            ]
        }
    
    def detect_references_in_sections(self, sections: List[Dict]) -> List[Dict]:
        """
        Detect all cross-references between sections.
        Returns list of reference edges.
        """
        all_references = []
        
        # Create mapping of section numbers to section IDs
        section_map = {s['section_number']: s['section_id'] for s in sections if s.get('section_number')}
        
        for section in sections:
            references = self._detect_references_in_section(section, section_map)
            all_references.extend(references)
        
        # Remove duplicates
        unique_references = []
        seen = set()
        for ref in all_references:
            key = (ref['from'], ref['to'], ref.get('reference_type', ''))
            if key not in seen:
                seen.add(key)
                unique_references.append(ref)
        
        return unique_references
    
    def _detect_references_in_section(self, section: Dict, section_map: Dict[str, str]) -> List[Dict]:
        """Detect references in a single section."""
        references = []
        text = section.get('text', '')
        from_section = section['section_id']
        
        # Detect different types of references
        for ref_type, patterns in self.reference_types.items():
            for pattern in patterns:
                matches = pattern.finditer(text)
                for match in matches:
                    referenced_sections = self._parse_section_numbers(match.group(1))
                    
                    for section_num in referenced_sections:
                        if section_num in section_map:
                            to_section = section_map[section_num]
                            
                            # Don't create self-references
                            if from_section != to_section:
                                references.append({
                                    'from': from_section,
                                    'to': to_section,
                                    'reference_type': ref_type,
                                    'context': self._extract_context(text, match),
                                    'match_text': match.group(0)
                                })
        
        # Detect general section references
        for pattern in self.reference_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                if match.groups():
                    referenced_sections = self._parse_section_numbers(match.group(1))
                    
                    for section_num in referenced_sections:
                        if section_num in section_map:
                            to_section = section_map[section_num]
                            
                            if from_section != to_section:
                                # Check if we already have this reference with a specific type
                                existing = any(
                                    ref['from'] == from_section and ref['to'] == to_section
                                    for ref in references
                                )
                                
                                if not existing:
                                    references.append({
                                        'from': from_section,
                                        'to': to_section,
                                        'reference_type': 'general_reference',
                                        'context': self._extract_context(text, match),
                                        'match_text': match.group(0)
                                    })
        
        return references
    
    def _parse_section_numbers(self, section_text: str) -> List[str]:
        """Parse section numbers from text like '15 and 16' or '10, 11 and 12'."""
        # Handle ranges like "15 to 20"
        range_match = re.search(r'(\d+)\s+to\s+(\d+)', section_text)
        if range_match:
            start, end = int(range_match.group(1)), int(range_match.group(2))
            return [str(i) for i in range(start, end + 1)]
        
        # Handle lists like "15 and 16" or "10, 11 and 12"
        numbers = re.findall(r'\d+', section_text)
        return numbers
    
    def _extract_context(self, text: str, match: re.Match, context_length: int = 100) -> str:
        """Extract context around the match."""
        start = max(0, match.start() - context_length)
        end = min(len(text), match.end() + context_length)
        context = text[start:end].strip()
        
        # Clean up context
        context = ' '.join(context.split())
        return context
    
    def _detect_chapter_references(self, sections: List[Dict]) -> List[Dict]:
        """Detect references to chapters."""
        references = []
        
        # Create chapter mapping
        chapter_map = {}
        for section in sections:
            chapter = section.get('chapter')
            if chapter:
                chapter_map[chapter] = chapter
        
        for section in sections:
            text = section.get('text', '')
            from_section = section['section_id']
            
            # Look for chapter references
            chapter_pattern = re.compile(r'\bchapter\s+([IVXLC]+)', re.IGNORECASE)
            matches = chapter_pattern.finditer(text)
            
            for match in matches:
                roman_num = match.group(1).upper()
                chapter_id = f"CPA_2019_CH{roman_num}"
                
                if chapter_id in chapter_map and chapter_id != section.get('chapter'):
                    references.append({
                        'from': from_section,
                        'to': chapter_id,
                        'reference_type': 'chapter_reference',
                        'context': self._extract_context(text, match),
                        'match_text': match.group(0)
                    })
        
        return references

def detect_and_save_references(root_path: Path):
    """Detect references from sections and save to files."""
    
    # Load sections data
    sections_path = root_path / 'knowledge_graph/nodes/sections.data.json'
    with open(sections_path, 'r', encoding='utf-8') as f:
        sections = json.load(f)
    
    # Detect references
    detector = ReferenceDetector()
    references = detector.detect_references_in_sections(sections)
    
    # Also detect chapter references
    chapter_references = detector._detect_chapter_references(sections)
    references.extend(chapter_references)
    
    # Save references data
    references_path = root_path / 'knowledge_graph/edges/references.data.json'
    with open(references_path, 'w', encoding='utf-8') as f:
        json.dump(references, f, indent=2, ensure_ascii=False)
    
    # Update references schema to include new fields
    references_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "SectionReferences",
        "type": "array",
        "items": {
            "type": "object",
            "required": ["from", "to"],
            "properties": {
                "from": {
                    "type": "string",
                    "description": "Section ID that makes the reference"
                },
                "to": {
                    "type": "string", 
                    "description": "Section ID that is referenced"
                },
                "reference_type": {
                    "type": "string",
                    "enum": [
                        "direct_reference", "procedural_reference", 
                        "definitional_reference", "conditional_reference",
                        "general_reference", "chapter_reference"
                    ],
                    "description": "Type of reference relationship"
                },
                "context": {
                    "type": "string",
                    "description": "Context text around the reference"
                },
                "match_text": {
                    "type": "string",
                    "description": "Exact text that matched the reference pattern"
                }
            },
            "additionalProperties": False
        }
    }
    
    references_schema_path = root_path / 'knowledge_graph/edges/references.schema.json'
    with open(references_schema_path, 'w', encoding='utf-8') as f:
        json.dump(references_schema, f, indent=2, ensure_ascii=False)
    
    print(f"Detected {len(references)} cross-references")
    
    # Print sample references
    if references:
        print("\nSample references:")
        for ref in references[:5]:
            print(f"  {ref['from']} -> {ref['to']} ({ref.get('reference_type', 'unknown')})")
            print(f"    Context: {ref.get('context', '')[:100]}...")
    
    return references

if __name__ == "__main__":
    root_path = Path(__file__).parent.parent
    detect_and_save_references(root_path)