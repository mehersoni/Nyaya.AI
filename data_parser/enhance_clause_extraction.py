#!/usr/bin/env python3
"""
Enhanced clause extraction script to improve clause coverage.
This script re-processes all sections to extract more clauses using improved patterns.
"""

import json
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from data_parser.clause_parser import parse_clauses

def main():
    """
    Re-run clause extraction with enhanced patterns.
    """
    root = Path(".")
    
    print("Starting enhanced clause extraction...")
    
    # Parse clauses with enhanced algorithm
    all_clauses, all_edges = parse_clauses(root)
    
    print(f"Extracted {len(all_clauses)} clauses from sections")
    print(f"Generated {len(all_edges)} clause containment edges")
    
    # Show breakdown by clause type
    clause_types = {}
    for clause in all_clauses:
        clause_type = clause.get('clause_type', 'unknown')
        clause_types[clause_type] = clause_types.get(clause_type, 0) + 1
    
    print("\nClause breakdown by type:")
    for clause_type, count in sorted(clause_types.items()):
        print(f"  {clause_type}: {count}")
    
    # Save enhanced clauses
    clauses_path = root / "knowledge_graph/nodes/clauses.data.json"
    with open(clauses_path, 'w', encoding='utf-8') as f:
        json.dump(all_clauses, f, indent=2, ensure_ascii=False)
    
    # Save enhanced edges
    edges_path = root / "knowledge_graph/edges/contains_clause.data.json"
    with open(edges_path, 'w', encoding='utf-8') as f:
        json.dump(all_edges, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved enhanced clauses to: {clauses_path}")
    print(f"Saved enhanced edges to: {edges_path}")
    
    # Show some examples
    print("\nExample clauses extracted:")
    for i, clause in enumerate(all_clauses[:5]):
        print(f"\n{i+1}. {clause['clause_id']} ({clause.get('clause_type', 'unknown')})")
        print(f"   Label: {clause['label']}")
        print(f"   Text: {clause['text'][:100]}...")

if __name__ == "__main__":
    main()