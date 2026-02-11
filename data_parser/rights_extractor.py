#!/usr/bin/env python3
"""
Rights extractor to identify consumer rights from legal text.
Builds rights nodes with proper relationships to granting sections.
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Tuple

class RightsExtractor:
    """Extract consumer rights from legal text."""
    
    def __init__(self):
        # Patterns to identify rights in legal text
        self.right_patterns = [
            # Direct right statements
            re.compile(r'right to ([^.;]+)', re.IGNORECASE),
            re.compile(r'entitled to ([^.;]+)', re.IGNORECASE),
            re.compile(r'shall have the right to ([^.;]+)', re.IGNORECASE),
            re.compile(r'consumer.*right.*to ([^.;]+)', re.IGNORECASE),
            
            # Protection statements
            re.compile(r'protected against ([^.;]+)', re.IGNORECASE),
            re.compile(r'protection.*from ([^.;]+)', re.IGNORECASE),
            
            # Remedy and redressal statements
            re.compile(r'seek redressal ([^.;]+)', re.IGNORECASE),
            re.compile(r'compensation for ([^.;]+)', re.IGNORECASE),
            re.compile(r'remedy.*for ([^.;]+)', re.IGNORECASE),
            
            # Procedural rights
            re.compile(r'may file.*complaint ([^.;]+)', re.IGNORECASE),
            re.compile(r'may prefer.*appeal ([^.;]+)', re.IGNORECASE),
            re.compile(r'opportunity.*being heard', re.IGNORECASE),
        ]
        
        # Keywords that indicate rights
        self.right_keywords = [
            'right', 'entitled', 'protection', 'redressal', 'compensation',
            'remedy', 'complaint', 'appeal', 'heard', 'access', 'choice',
            'information', 'safety', 'awareness'
        ]
        
        # Predefined consumer rights from CPA 2019 Section 2
        self.predefined_rights = [
            {
                'description': 'The right to be protected against the marketing of goods, products or services which are hazardous to life and property',
                'right_type': 'consumer_right',
                'beneficiary': 'consumer',
                'scope': 'safety protection',
                'enforcement_mechanism': 'Central Consumer Protection Authority'
            },
            {
                'description': 'The right to be informed about the quality, quantity, potency, purity, standard and price of goods, products or services',
                'right_type': 'consumer_right', 
                'beneficiary': 'consumer',
                'scope': 'information disclosure',
                'enforcement_mechanism': 'Consumer Disputes Redressal Commissions'
            },
            {
                'description': 'The right to be assured, wherever possible, access to a variety of goods, products or services at competitive prices',
                'right_type': 'consumer_right',
                'beneficiary': 'consumer', 
                'scope': 'market access and choice',
                'enforcement_mechanism': 'Market regulation'
            },
            {
                'description': 'The right to be heard and to be assured that consumer interests will receive due consideration at appropriate fora',
                'right_type': 'consumer_right',
                'beneficiary': 'consumer',
                'scope': 'representation and voice',
                'enforcement_mechanism': 'Consumer Disputes Redressal Commissions'
            },
            {
                'description': 'The right to seek redressal against unfair trade practice or restrictive trade practices or unscrupulous exploitation of consumers',
                'right_type': 'consumer_right',
                'beneficiary': 'consumer',
                'scope': 'redressal mechanism',
                'enforcement_mechanism': 'Consumer Disputes Redressal Commissions'
            },
            {
                'description': 'The right to consumer awareness',
                'right_type': 'consumer_right',
                'beneficiary': 'consumer',
                'scope': 'education and awareness',
                'enforcement_mechanism': 'Consumer Protection Councils'
            }
        ]
    
    def extract_rights_from_sections(self, sections: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Extract rights from all sections.
        Returns (rights_list, edges_list).
        """
        all_rights = []
        all_edges = []
        
        # Add predefined consumer rights from Section 2
        section_2 = next((s for s in sections if s['section_id'] == 'CPA_2019_S2'), None)
        if section_2:
            predefined_rights, predefined_edges = self._add_predefined_rights(section_2)
            all_rights.extend(predefined_rights)
            all_edges.extend(predefined_edges)
        
        # Extract additional rights from other sections
        for section in sections:
            rights, edges = self._extract_rights_from_section(section)
            all_rights.extend(rights)
            all_edges.extend(edges)
        
        return all_rights, all_edges
    
    def _add_predefined_rights(self, section_2: Dict) -> Tuple[List[Dict], List[Dict]]:
        """Add predefined consumer rights from Section 2."""
        rights = []
        edges = []
        
        for i, right_data in enumerate(self.predefined_rights, 1):
            right_id = f"CPA_2019_R_{i:03d}"
            
            right = {
                'right_id': right_id,
                'description': right_data['description'],
                'granted_by': section_2['section_id'],
                'right_type': right_data['right_type'],
                'beneficiary': right_data['beneficiary'],
                'scope': right_data['scope'],
                'enforcement_mechanism': right_data['enforcement_mechanism'],
                'related_sections': []
            }
            
            rights.append(right)
            
            # Create edge from section to right
            edges.append({
                'parent': section_2['section_id'],
                'child': right_id,
                'relation': 'grants_right'
            })
        
        return rights, edges
    
    def _extract_rights_from_section(self, section: Dict) -> Tuple[List[Dict], List[Dict]]:
        """Extract rights from a single section."""
        rights = []
        edges = []
        
        section_text = section.get('text', '')
        section_id = section['section_id']
        
        # Skip Section 2 as we handle it separately
        if section_id == 'CPA_2019_S2':
            return rights, edges
        
        # Look for procedural rights and remedies
        procedural_rights = self._extract_procedural_rights(section)
        for right in procedural_rights:
            right_id = f"{section_id}_R_{len(rights) + 1:03d}"
            
            right_obj = {
                'right_id': right_id,
                'description': right['description'],
                'granted_by': section_id,
                'right_type': right['right_type'],
                'beneficiary': right['beneficiary'],
                'scope': right.get('scope', ''),
                'enforcement_mechanism': right.get('enforcement_mechanism', ''),
                'related_sections': []
            }
            
            rights.append(right_obj)
            
            # Create edge
            edges.append({
                'parent': section_id,
                'child': right_id,
                'relation': 'grants_right'
            })
        
        return rights, edges
    
    def _extract_procedural_rights(self, section: Dict) -> List[Dict]:
        """Extract procedural rights from section text."""
        rights = []
        text = section.get('text', '')
        section_num = section.get('section_number', '')
        
        # Complaint filing rights
        if 'complaint' in text.lower() and ('file' in text.lower() or 'made' in text.lower()):
            rights.append({
                'description': f'Right to file complaint as provided in Section {section_num}',
                'right_type': 'procedural_right',
                'beneficiary': 'consumer',
                'scope': 'complaint filing',
                'enforcement_mechanism': 'Consumer Disputes Redressal Commissions'
            })
        
        # Appeal rights
        if 'appeal' in text.lower() and 'prefer' in text.lower():
            rights.append({
                'description': f'Right to prefer appeal as provided in Section {section_num}',
                'right_type': 'procedural_right',
                'beneficiary': 'aggrieved person',
                'scope': 'appellate remedy',
                'enforcement_mechanism': 'Higher Consumer Commission'
            })
        
        # Hearing rights
        if 'opportunity' in text.lower() and 'heard' in text.lower():
            rights.append({
                'description': f'Right to opportunity of being heard as provided in Section {section_num}',
                'right_type': 'procedural_right',
                'beneficiary': 'party to proceedings',
                'scope': 'fair hearing',
                'enforcement_mechanism': 'Consumer Disputes Redressal Commissions'
            })
        
        # Mediation rights
        if 'mediation' in text.lower():
            rights.append({
                'description': f'Right to mediation as provided in Section {section_num}',
                'right_type': 'procedural_right',
                'beneficiary': 'parties to dispute',
                'scope': 'alternative dispute resolution',
                'enforcement_mechanism': 'Consumer Mediation Cell'
            })
        
        # Compensation rights
        if 'compensation' in text.lower():
            rights.append({
                'description': f'Right to compensation as provided in Section {section_num}',
                'right_type': 'remedy_right',
                'beneficiary': 'consumer',
                'scope': 'monetary relief',
                'enforcement_mechanism': 'Consumer Disputes Redressal Commissions'
            })
        
        # Product liability rights
        if 'product liability' in text.lower():
            rights.append({
                'description': f'Right to product liability action as provided in Section {section_num}',
                'right_type': 'remedy_right',
                'beneficiary': 'consumer',
                'scope': 'defective product claims',
                'enforcement_mechanism': 'Consumer Disputes Redressal Commissions'
            })
        
        return rights

def extract_and_save_rights(root_path: Path):
    """Extract rights from sections and save to files."""
    
    # Load sections data
    sections_path = root_path / 'knowledge_graph/nodes/sections.data.json'
    with open(sections_path, 'r', encoding='utf-8') as f:
        sections = json.load(f)
    
    # Extract rights
    extractor = RightsExtractor()
    rights, edges = extractor.extract_rights_from_sections(sections)
    
    # Save rights data
    rights_path = root_path / 'knowledge_graph/nodes/rights.data.json'
    with open(rights_path, 'w', encoding='utf-8') as f:
        json.dump(rights, f, indent=2, ensure_ascii=False)
    
    # Save grants_right edges
    grants_edges_path = root_path / 'knowledge_graph/edges/grants_right.data.json'
    with open(grants_edges_path, 'w', encoding='utf-8') as f:
        json.dump(edges, f, indent=2, ensure_ascii=False)
    
    # Create schema for grants_right edges
    grants_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "GrantsRightEdges",
        "type": "array",
        "items": {
            "type": "object",
            "required": ["parent", "child", "relation"],
            "properties": {
                "parent": {"type": "string", "description": "Section ID that grants the right"},
                "child": {"type": "string", "description": "Right ID that is granted"},
                "relation": {"type": "string", "enum": ["grants_right"]}
            },
            "additionalProperties": False
        }
    }
    
    grants_schema_path = root_path / 'knowledge_graph/edges/grants_right.schema.json'
    with open(grants_schema_path, 'w', encoding='utf-8') as f:
        json.dump(grants_schema, f, indent=2, ensure_ascii=False)
    
    print(f"Extracted {len(rights)} rights and {len(edges)} grant relationships")
    return rights, edges

if __name__ == "__main__":
    root_path = Path(__file__).parent.parent
    extract_and_save_rights(root_path)