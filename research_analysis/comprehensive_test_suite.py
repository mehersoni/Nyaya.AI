#!/usr/bin/env python3
"""
Comprehensive Test Suite for Nyayamrit GraphRAG System
Tests the system on 100 diverse queries to validate performance with enhanced clause coverage.
"""

import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Any
import statistics

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from query_engine.graphrag_engine import GraphRAGEngine

class ComprehensiveTestSuite:
    def __init__(self):
        self.engine = GraphRAGEngine()
        self.test_queries = self._generate_test_queries()
        self.results = []
        
    def _generate_test_queries(self) -> List[Dict[str, Any]]:
        """Generate 100 diverse test queries across all intent types and complexity levels."""
        
        queries = []
        
        # Definition Lookup Queries (25 queries)
        definition_queries = [
            {"query": "What does consumer mean?", "expected_intent": "definition_lookup"},
            {"query": "Define unfair trade practice", "expected_intent": "definition_lookup"},
            {"query": "What is the meaning of defective goods?", "expected_intent": "definition_lookup"},
            {"query": "Explain misleading advertisement", "expected_intent": "definition_lookup"},
            {"query": "What does complainant mean in legal terms?", "expected_intent": "definition_lookup"},
            {"query": "Define trader under CPA", "expected_intent": "definition_lookup"},
            {"query": "What is meant by service in consumer law?", "expected_intent": "definition_lookup"},
            {"query": "Explain the term product liability", "expected_intent": "definition_lookup"},
            {"query": "What does Central Authority mean?", "expected_intent": "definition_lookup"},
            {"query": "Define District Commission", "expected_intent": "definition_lookup"},
            {"query": "What is State Commission?", "expected_intent": "definition_lookup"},
            {"query": "Explain National Commission", "expected_intent": "definition_lookup"},
            {"query": "What does e-commerce mean in CPA?", "expected_intent": "definition_lookup"},
            {"query": "Define product seller", "expected_intent": "definition_lookup"},
            {"query": "What is meant by product manufacturer?", "expected_intent": "definition_lookup"},
            {"query": "Explain consumer dispute", "expected_intent": "definition_lookup"},
            {"query": "What does harm mean in consumer context?", "expected_intent": "definition_lookup"},
            {"query": "Define express warranty", "expected_intent": "definition_lookup"},
            {"query": "What is implied warranty?", "expected_intent": "definition_lookup"},
            {"query": "Explain restrictive trade practice", "expected_intent": "definition_lookup"},
            {"query": "What does pecuniary jurisdiction mean?", "expected_intent": "definition_lookup"},
            {"query": "Define territorial jurisdiction", "expected_intent": "definition_lookup"},
            {"query": "What is meant by consumer protection council?", "expected_intent": "definition_lookup"},
            {"query": "Explain the term mediation", "expected_intent": "definition_lookup"},
            {"query": "What does investigation wing mean?", "expected_intent": "definition_lookup"}
        ]
        
        # Section Retrieval Queries (25 queries)
        section_queries = [
            {"query": "Show me section 2", "expected_intent": "section_retrieval"},
            {"query": "Get section 18 of CPA", "expected_intent": "section_retrieval"},
            {"query": "What does section 35 say?", "expected_intent": "section_retrieval"},
            {"query": "Display section 21 content", "expected_intent": "section_retrieval"},
            {"query": "Find section 47 provisions", "expected_intent": "section_retrieval"},
            {"query": "Section 12 details", "expected_intent": "section_retrieval"},
            {"query": "Show section 23", "expected_intent": "section_retrieval"},
            {"query": "Section 34 text", "expected_intent": "section_retrieval"},
            {"query": "Get me section 41", "expected_intent": "section_retrieval"},
            {"query": "Section 58 provisions", "expected_intent": "section_retrieval"},
            {"query": "What is in section 67?", "expected_intent": "section_retrieval"},
            {"query": "Section 72 content", "expected_intent": "section_retrieval"},
            {"query": "Show section 15", "expected_intent": "section_retrieval"},
            {"query": "Section 28 details", "expected_intent": "section_retrieval"},
            {"query": "Get section 36", "expected_intent": "section_retrieval"},
            {"query": "Section 49 text", "expected_intent": "section_retrieval"},
            {"query": "What does section 51 contain?", "expected_intent": "section_retrieval"},
            {"query": "Section 63 provisions", "expected_intent": "section_retrieval"},
            {"query": "Show me section 74", "expected_intent": "section_retrieval"},
            {"query": "Section 19 content", "expected_intent": "section_retrieval"},
            {"query": "Get section 25", "expected_intent": "section_retrieval"},
            {"query": "Section 31 details", "expected_intent": "section_retrieval"},
            {"query": "What is section 44?", "expected_intent": "section_retrieval"},
            {"query": "Section 56 text", "expected_intent": "section_retrieval"},
            {"query": "Show section 69", "expected_intent": "section_retrieval"}
        ]
        
        # Rights Query Queries (25 queries)
        rights_queries = [
            {"query": "What are my consumer rights?", "expected_intent": "rights_query"},
            {"query": "What rights do I have as a buyer?", "expected_intent": "rights_query"},
            {"query": "Consumer protection rights under CPA", "expected_intent": "rights_query"},
            {"query": "Rights against unfair trade practices", "expected_intent": "rights_query"},
            {"query": "What can consumers claim for defective products?", "expected_intent": "rights_query"},
            {"query": "Rights to information about products", "expected_intent": "rights_query"},
            {"query": "Consumer rights for service deficiency", "expected_intent": "rights_query"},
            {"query": "Rights against misleading advertisements", "expected_intent": "rights_query"},
            {"query": "What rights do online buyers have?", "expected_intent": "rights_query"},
            {"query": "Consumer rights for warranty claims", "expected_intent": "rights_query"},
            {"query": "Rights to compensation for damages", "expected_intent": "rights_query"},
            {"query": "Consumer rights in e-commerce", "expected_intent": "rights_query"},
            {"query": "Rights against overcharging", "expected_intent": "rights_query"},
            {"query": "Consumer rights for product safety", "expected_intent": "rights_query"},
            {"query": "Rights to file complaints", "expected_intent": "rights_query"},
            {"query": "Consumer rights for refunds", "expected_intent": "rights_query"},
            {"query": "Rights against discrimination", "expected_intent": "rights_query"},
            {"query": "Consumer rights for privacy", "expected_intent": "rights_query"},
            {"query": "Rights to choose products freely", "expected_intent": "rights_query"},
            {"query": "Consumer rights for education", "expected_intent": "rights_query"},
            {"query": "Rights against hazardous goods", "expected_intent": "rights_query"},
            {"query": "Consumer rights for representation", "expected_intent": "rights_query"},
            {"query": "Rights to seek redressal", "expected_intent": "rights_query"},
            {"query": "Consumer rights for fair treatment", "expected_intent": "rights_query"},
            {"query": "Rights against exploitation", "expected_intent": "rights_query"}
        ]
        
        # Scenario Analysis Queries (25 queries)
        scenario_queries = [
            {"query": "I bought a defective product, what can I do?", "expected_intent": "scenario_analysis"},
            {"query": "Seller is refusing refund, what are my options?", "expected_intent": "scenario_analysis"},
            {"query": "Misleading advertisement caused loss, how to complain?", "expected_intent": "scenario_analysis"},
            {"query": "Service provider overcharging, is this legal?", "expected_intent": "scenario_analysis"},
            {"query": "Received damaged goods, what compensation can I get?", "expected_intent": "scenario_analysis"},
            {"query": "Online purchase not delivered, what to do?", "expected_intent": "scenario_analysis"},
            {"query": "Product caused injury, can I claim damages?", "expected_intent": "scenario_analysis"},
            {"query": "Warranty expired but product failed early, any recourse?", "expected_intent": "scenario_analysis"},
            {"query": "Restaurant served contaminated food, what action?", "expected_intent": "scenario_analysis"},
            {"query": "Bank charged unauthorized fees, how to complain?", "expected_intent": "scenario_analysis"},
            {"query": "Insurance claim rejected unfairly, what options?", "expected_intent": "scenario_analysis"},
            {"query": "Mobile service poor quality, can I get compensation?", "expected_intent": "scenario_analysis"},
            {"query": "Airline cancelled flight without notice, what rights?", "expected_intent": "scenario_analysis"},
            {"query": "Hospital overcharged for treatment, is this allowed?", "expected_intent": "scenario_analysis"},
            {"query": "Courier lost my package, what compensation?", "expected_intent": "scenario_analysis"},
            {"query": "Gym refusing membership cancellation, what to do?", "expected_intent": "scenario_analysis"},
            {"query": "Car dealer sold defective vehicle, what recourse?", "expected_intent": "scenario_analysis"},
            {"query": "Real estate agent misled about property, can I complain?", "expected_intent": "scenario_analysis"},
            {"query": "Educational institution charging hidden fees, is this legal?", "expected_intent": "scenario_analysis"},
            {"query": "Electricity bill seems wrong, how to dispute?", "expected_intent": "scenario_analysis"},
            {"query": "Medicine caused side effects not mentioned, what action?", "expected_intent": "scenario_analysis"},
            {"query": "Appliance repair service damaged my item, what compensation?", "expected_intent": "scenario_analysis"},
            {"query": "Travel agency cancelled trip last minute, what rights?", "expected_intent": "scenario_analysis"},
            {"query": "Software purchase doesn't work as advertised, what options?", "expected_intent": "scenario_analysis"},
            {"query": "Subscription service won't let me cancel, what to do?", "expected_intent": "scenario_analysis"}
        ]
        
        # Add all queries with metadata
        for i, q in enumerate(definition_queries):
            queries.append({**q, "id": f"DEF_{i+1:03d}", "category": "definition_lookup"})
            
        for i, q in enumerate(section_queries):
            queries.append({**q, "id": f"SEC_{i+1:03d}", "category": "section_retrieval"})
            
        for i, q in enumerate(rights_queries):
            queries.append({**q, "id": f"RGT_{i+1:03d}", "category": "rights_query"})
            
        for i, q in enumerate(scenario_queries):
            queries.append({**q, "id": f"SCN_{i+1:03d}", "category": "scenario_analysis"})
        
        return queries
    
    def run_single_query(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single query and collect detailed metrics."""
        
        start_time = time.time()
        
        try:
            # Process query
            response = self.engine.process_query(
                query=query_data["query"],
                audience="citizen"
            )
            
            end_time = time.time()
            latency = (end_time - start_time) * 1000  # Convert to milliseconds
            
            # Extract metrics from GraphRAGResponse object
            metrics = {
                "query_id": query_data["id"],
                "query_text": query_data["query"],
                "expected_intent": query_data["expected_intent"],
                "category": query_data["category"],
                "success": True,
                "latency_ms": round(latency, 2),
                "intent_detected": response.query_intent.intent_type.value,
                "confidence": response.get_confidence_score(),
                "nodes_retrieved": len(response.graph_context.nodes),
                "context_length": response.llm_context.get_total_length(),
                "citations_count": response.llm_context.get_citation_count(),
                "reasoning_steps": len(response.processing_metadata.get("reasoning_steps", [])),
                "human_review_flagged": response.requires_human_review(),
                "error": None
            }
            
            # Validate intent classification
            metrics["intent_correct"] = (
                metrics["intent_detected"] == metrics["expected_intent"]
            )
            
        except Exception as e:
            end_time = time.time()
            latency = (end_time - start_time) * 1000
            
            metrics = {
                "query_id": query_data["id"],
                "query_text": query_data["query"],
                "expected_intent": query_data["expected_intent"],
                "category": query_data["category"],
                "success": False,
                "latency_ms": round(latency, 2),
                "intent_detected": "error",
                "confidence": 0.0,
                "nodes_retrieved": 0,
                "context_length": 0,
                "citations_count": 0,
                "reasoning_steps": 0,
                "human_review_flagged": True,
                "intent_correct": False,
                "error": str(e)
            }
        
        return metrics
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all 100 queries and collect comprehensive statistics."""
        
        print("Starting Comprehensive Test Suite (100 queries)")
        print("=" * 60)
        
        # Run all queries
        for i, query_data in enumerate(self.test_queries, 1):
            print(f"Testing query {i:3d}/100: {query_data['query'][:50]}...")
            
            result = self.run_single_query(query_data)
            self.results.append(result)
            
            # Show progress every 25 queries
            if i % 25 == 0:
                success_rate = sum(1 for r in self.results if r["success"]) / len(self.results) * 100
                print(f"  Progress: {i}/100 queries completed ({success_rate:.1f}% success rate)")
        
        # Calculate comprehensive statistics
        stats = self._calculate_statistics()
        
        # Save detailed results
        self._save_results(stats)
        
        return stats
    
    def _calculate_statistics(self) -> Dict[str, Any]:
        """Calculate comprehensive statistics from test results."""
        
        successful_results = [r for r in self.results if r["success"]]
        
        # Overall statistics
        overall_stats = {
            "total_queries": len(self.results),
            "successful_queries": len(successful_results),
            "failed_queries": len(self.results) - len(successful_results),
            "success_rate": len(successful_results) / len(self.results) * 100,
            "error_rate": (len(self.results) - len(successful_results)) / len(self.results) * 100
        }
        
        if successful_results:
            # Performance statistics
            latencies = [r["latency_ms"] for r in successful_results]
            confidences = [r["confidence"] for r in successful_results]
            nodes_retrieved = [r["nodes_retrieved"] for r in successful_results]
            context_lengths = [r["context_length"] for r in successful_results]
            citations = [r["citations_count"] for r in successful_results]
            
            performance_stats = {
                "latency": {
                    "mean": statistics.mean(latencies),
                    "median": statistics.median(latencies),
                    "std_dev": statistics.stdev(latencies) if len(latencies) > 1 else 0,
                    "min": min(latencies),
                    "max": max(latencies),
                    "p95": sorted(latencies)[int(0.95 * len(latencies))]
                },
                "confidence": {
                    "mean": statistics.mean(confidences),
                    "median": statistics.median(confidences),
                    "std_dev": statistics.stdev(confidences) if len(confidences) > 1 else 0,
                    "min": min(confidences),
                    "max": max(confidences)
                },
                "nodes_retrieved": {
                    "mean": statistics.mean(nodes_retrieved),
                    "median": statistics.median(nodes_retrieved),
                    "min": min(nodes_retrieved),
                    "max": max(nodes_retrieved)
                },
                "context_length": {
                    "mean": statistics.mean(context_lengths),
                    "median": statistics.median(context_lengths),
                    "min": min(context_lengths),
                    "max": max(context_lengths)
                },
                "citations": {
                    "mean": statistics.mean(citations),
                    "median": statistics.median(citations),
                    "min": min(citations),
                    "max": max(citations)
                }
            }
        else:
            performance_stats = {}
        
        # Intent classification accuracy
        intent_stats = {}
        for category in ["definition_lookup", "section_retrieval", "rights_query", "scenario_analysis"]:
            category_results = [r for r in self.results if r["category"] == category]
            if category_results:
                correct = sum(1 for r in category_results if r["intent_correct"])
                intent_stats[category] = {
                    "total": len(category_results),
                    "correct": correct,
                    "accuracy": correct / len(category_results) * 100
                }
        
        # Category-wise performance
        category_stats = {}
        for category in ["definition_lookup", "section_retrieval", "rights_query", "scenario_analysis"]:
            category_results = [r for r in successful_results if r["category"] == category]
            if category_results:
                category_stats[category] = {
                    "count": len(category_results),
                    "avg_latency": statistics.mean([r["latency_ms"] for r in category_results]),
                    "avg_confidence": statistics.mean([r["confidence"] for r in category_results]),
                    "avg_nodes": statistics.mean([r["nodes_retrieved"] for r in category_results]),
                    "avg_context_length": statistics.mean([r["context_length"] for r in category_results]),
                    "avg_citations": statistics.mean([r["citations_count"] for r in category_results]),
                    "human_review_rate": sum(1 for r in category_results if r["human_review_flagged"]) / len(category_results) * 100
                }
        
        # Error analysis
        errors = [r for r in self.results if not r["success"]]
        error_stats = {
            "total_errors": len(errors),
            "error_types": {},
            "failed_queries": [{"id": r["query_id"], "query": r["query_text"], "error": r["error"]} for r in errors]
        }
        
        # Count error types
        for error in errors:
            error_type = type(error.get("error", "Unknown")).__name__
            error_stats["error_types"][error_type] = error_stats["error_types"].get(error_type, 0) + 1
        
        return {
            "test_metadata": {
                "test_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_queries": 100,
                "query_categories": ["definition_lookup", "section_retrieval", "rights_query", "scenario_analysis"],
                "queries_per_category": 25
            },
            "overall_performance": overall_stats,
            "performance_metrics": performance_stats,
            "intent_classification": intent_stats,
            "category_performance": category_stats,
            "error_analysis": error_stats,
            "detailed_results": self.results
        }
    
    def _save_results(self, stats: Dict[str, Any]) -> None:
        """Save comprehensive test results to files."""
        
        # Create results directory
        results_dir = Path("research_analysis/data")
        results_dir.mkdir(exist_ok=True)
        
        # Save comprehensive statistics
        with open(results_dir / "comprehensive_test_results.json", "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        # Save detailed results
        with open(results_dir / "detailed_query_results.json", "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        # Generate summary report
        self._generate_summary_report(stats, results_dir / "comprehensive_test_summary.txt")
        
        print(f"\n✓ Results saved to: {results_dir}")
    
    def _generate_summary_report(self, stats: Dict[str, Any], output_path: Path) -> None:
        """Generate a human-readable summary report."""
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("NYAYAMRIT GRAPHRAG COMPREHENSIVE TEST REPORT (100 QUERIES)\n")
            f.write("=" * 70 + "\n\n")
            
            # Test metadata
            f.write("TEST METADATA:\n")
            f.write(f"- Test Date: {stats['test_metadata']['test_date']}\n")
            f.write(f"- Total Queries: {stats['test_metadata']['total_queries']}\n")
            f.write(f"- Categories: {', '.join(stats['test_metadata']['query_categories'])}\n")
            f.write(f"- Queries per Category: {stats['test_metadata']['queries_per_category']}\n\n")
            
            # Overall performance
            f.write("OVERALL PERFORMANCE:\n")
            overall = stats["overall_performance"]
            f.write(f"- Success Rate: {overall['success_rate']:.1f}% ({overall['successful_queries']}/{overall['total_queries']})\n")
            f.write(f"- Error Rate: {overall['error_rate']:.1f}% ({overall['failed_queries']}/{overall['total_queries']})\n\n")
            
            # Performance metrics
            if stats["performance_metrics"]:
                f.write("PERFORMANCE METRICS:\n")
                perf = stats["performance_metrics"]
                
                f.write(f"Latency (ms):\n")
                f.write(f"  - Mean: {perf['latency']['mean']:.2f}\n")
                f.write(f"  - Median: {perf['latency']['median']:.2f}\n")
                f.write(f"  - 95th Percentile: {perf['latency']['p95']:.2f}\n")
                f.write(f"  - Range: {perf['latency']['min']:.2f} - {perf['latency']['max']:.2f}\n\n")
                
                f.write(f"Confidence Scores:\n")
                f.write(f"  - Mean: {perf['confidence']['mean']:.3f}\n")
                f.write(f"  - Median: {perf['confidence']['median']:.3f}\n")
                f.write(f"  - Range: {perf['confidence']['min']:.3f} - {perf['confidence']['max']:.3f}\n\n")
                
                f.write(f"Retrieval Metrics:\n")
                f.write(f"  - Avg Nodes Retrieved: {perf['nodes_retrieved']['mean']:.1f}\n")
                f.write(f"  - Avg Context Length: {perf['context_length']['mean']:.0f} chars\n")
                f.write(f"  - Avg Citations: {perf['citations']['mean']:.1f}\n\n")
            
            # Intent classification accuracy
            f.write("INTENT CLASSIFICATION ACCURACY:\n")
            for category, data in stats["intent_classification"].items():
                f.write(f"- {category.replace('_', ' ').title()}: {data['accuracy']:.1f}% ({data['correct']}/{data['total']})\n")
            f.write("\n")
            
            # Category performance
            f.write("CATEGORY-WISE PERFORMANCE:\n")
            for category, data in stats["category_performance"].items():
                f.write(f"{category.replace('_', ' ').title()}:\n")
                f.write(f"  - Queries: {data['count']}\n")
                f.write(f"  - Avg Latency: {data['avg_latency']:.2f}ms\n")
                f.write(f"  - Avg Confidence: {data['avg_confidence']:.3f}\n")
                f.write(f"  - Avg Nodes: {data['avg_nodes']:.1f}\n")
                f.write(f"  - Avg Citations: {data['avg_citations']:.1f}\n")
                f.write(f"  - Human Review Rate: {data['human_review_rate']:.1f}%\n\n")
            
            # Error analysis
            if stats["error_analysis"]["total_errors"] > 0:
                f.write("ERROR ANALYSIS:\n")
                f.write(f"- Total Errors: {stats['error_analysis']['total_errors']}\n")
                f.write("- Error Types:\n")
                for error_type, count in stats["error_analysis"]["error_types"].items():
                    f.write(f"  - {error_type}: {count}\n")
                f.write("\n")


def main():
    """Run the comprehensive test suite."""
    
    test_suite = ComprehensiveTestSuite()
    results = test_suite.run_comprehensive_test()
    
    print("\n" + "=" * 60)
    print("COMPREHENSIVE TEST COMPLETED")
    print("=" * 60)
    
    # Print summary
    overall = results["overall_performance"]
    print(f"✓ Success Rate: {overall['success_rate']:.1f}% ({overall['successful_queries']}/{overall['total_queries']})")
    
    if results["performance_metrics"]:
        perf = results["performance_metrics"]
        print(f"✓ Average Latency: {perf['latency']['mean']:.2f}ms")
        print(f"✓ Average Confidence: {perf['confidence']['mean']:.3f}")
        print(f"✓ 95th Percentile Latency: {perf['latency']['p95']:.2f}ms")
    
    print(f"✓ Intent Classification Accuracy:")
    for category, data in results["intent_classification"].items():
        print(f"  - {category.replace('_', ' ').title()}: {data['accuracy']:.1f}%")
    
    if results["error_analysis"]["total_errors"] > 0:
        print(f"⚠ Errors: {results['error_analysis']['total_errors']}")
    else:
        print("✓ No Errors Detected")
    
    print(f"\n✓ Detailed results saved to: research_analysis/data/")


if __name__ == "__main__":
    main()