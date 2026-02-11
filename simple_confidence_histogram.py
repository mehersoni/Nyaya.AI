#!/usr/bin/env python3
"""
Simple ASCII Confidence Histogram for Nyayamrit
"""

import json
import numpy as np

def load_confidence_scores():
    """Load confidence scores from evaluation results"""
    with open('final_evaluation_results.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    scores = []
    types = []
    for result in data['query_results']:
        if result['success']:
            scores.append(result['confidence_score'])
            types.append(result['query_type'])
    
    return scores, types

def create_ascii_histogram(scores, bins=10):
    """Create ASCII histogram of confidence scores"""
    
    # Calculate histogram
    hist, bin_edges = np.histogram(scores, bins=bins)
    
    # Find max count for scaling
    max_count = max(hist)
    scale = 50 / max_count if max_count > 0 else 1
    
    print("📊 NYAYAMRIT CONFIDENCE SCORE DISTRIBUTION")
    print("=" * 60)
    print()
    
    for i in range(len(hist)):
        bin_start = bin_edges[i]
        bin_end = bin_edges[i + 1]
        count = hist[i]
        bar_length = int(count * scale)
        
        # Create bar
        bar = "█" * bar_length
        
        print(f"{bin_start:.2f}-{bin_end:.2f} │{bar:<50} {count}")
    
    print()
    print("=" * 60)

def print_statistics(scores, types):
    """Print detailed statistics"""
    
    print("📈 CONFIDENCE STATISTICS")
    print("=" * 40)
    print(f"Total Queries:     {len(scores)}")
    print(f"Mean Confidence:   {np.mean(scores):.3f}")
    print(f"Median Confidence: {np.median(scores):.3f}")
    print(f"Std Deviation:     {np.std(scores):.3f}")
    print(f"Min Confidence:    {np.min(scores):.3f}")
    print(f"Max Confidence:    {np.max(scores):.3f}")
    print()
    
    # Confidence levels
    high = sum(1 for s in scores if s >= 0.8)
    medium = sum(1 for s in scores if 0.6 <= s < 0.8)
    low = sum(1 for s in scores if s < 0.6)
    
    print("🎯 CONFIDENCE LEVELS")
    print("=" * 40)
    print(f"High (≥0.8):       {high:2d} queries ({high/len(scores)*100:4.1f}%)")
    print(f"Medium (0.6-0.8):  {medium:2d} queries ({medium/len(scores)*100:4.1f}%)")
    print(f"Low (<0.6):        {low:2d} queries ({low/len(scores)*100:4.1f}%)")
    print()
    
    # By query type
    type_stats = {}
    for score, qtype in zip(scores, types):
        if qtype not in type_stats:
            type_stats[qtype] = []
        type_stats[qtype].append(score)
    
    print("🔍 BY QUERY TYPE")
    print("=" * 40)
    for qtype, qscores in sorted(type_stats.items(), key=lambda x: np.mean(x[1]), reverse=True):
        display_name = qtype.replace('_', ' ').title()
        mean_conf = np.mean(qscores)
        count = len(qscores)
        print(f"{display_name:<18} {mean_conf:.3f} ({count} queries)")

def main():
    """Generate simple confidence analysis"""
    
    print("🔍 Loading confidence scores...")
    scores, types = load_confidence_scores()
    
    print(f"📊 Analyzing {len(scores)} confidence scores...\n")
    
    # Create ASCII histogram
    create_ascii_histogram(scores)
    
    # Print statistics
    print_statistics(scores, types)
    
    print("\n✅ Analysis complete!")

if __name__ == "__main__":
    main()