"""
Evaluation Script for Legal Document FAISS Index

This script evaluates the performance of the FAISS-based legal clause retrieval system
by calculating precision, recall, F1-score, and accuracy metrics.
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
import sys

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from query_legal_index import LegalSearchEngine

class LegalIndexEvaluator:
    """Evaluates the performance of legal clause retrieval system"""
    
    def __init__(self, index_dir: str = "./index"):
        """
        Initialize evaluator with FAISS index
        
        Args:
            index_dir: Directory containing FAISS index files
        """
        self.search_engine = LegalSearchEngine(index_dir)
        self.search_engine.load_index()
        
    def create_test_dataset(self) -> List[Dict]:
        """
        Create a test dataset with known query-clause pairs
        
        Returns:
            List of test cases with queries and expected relevant clause IDs
        """
        test_cases = [
            {
                "query": "agreements void for uncertainty",
                "relevant_clauses": ["Section_29"],
                "description": "Section 29 - Uncertainty in agreements"
            },
            {
                "query": "contract without consideration is void",
                "relevant_clauses": ["Section_25"],
                "description": "Section 25 - Agreement without consideration"
            },
            {
                "query": "fraud misrepresentation in contract",
                "relevant_clauses": ["Section_17", "Section_18", "Section_19"],
                "description": "Fraud and misrepresentation"
            },
            {
                "query": "coercion undue influence",
                "relevant_clauses": ["Section_15", "Section_16"],
                "description": "Coercion and undue influence"
            },
            {
                "query": "breach of contract damages compensation",
                "relevant_clauses": ["Section_73", "Section_74"],
                "description": "Breach of contract remedies"
            },
            {
                "query": "agent authority and liability",
                "relevant_clauses": ["Section_182", "Section_186", "Section_188"],
                "description": "Agency law"
            },
            {
                "query": "voidable contract free consent",
                "relevant_clauses": ["Section_13", "Section_14", "Section_19"],
                "description": "Voidable contracts"
            },
            {
                "query": "guarantee surety liability",
                "relevant_clauses": ["Section_126", "Section_128", "Section_133"],
                "description": "Guarantee and surety"
            },
            {
                "query": "bailment bailee responsibilities duties",
                "relevant_clauses": ["Section_148", "Section_151", "Section_152"],
                "description": "Bailment law"
            },
            {
                "query": "contract performance obligation",
                "relevant_clauses": ["Section_37", "Section_40", "Section_51"],
                "description": "Contract performance"
            },
            {
                "query": "illegal unlawful consideration void",
                "relevant_clauses": ["Section_23", "Section_24"],
                "description": "Unlawful consideration"
            },
            {
                "query": "contingent contract uncertain event",
                "relevant_clauses": ["Section_31", "Section_32", "Section_33"],
                "description": "Contingent contracts"
            },
            {
                "query": "offer acceptance proposal communication",
                "relevant_clauses": ["Section_2(a)", "Section_2(b)", "Section_3", "Section_4"],
                "description": "Offer and acceptance"
            },
            {
                "query": "mistake contract void agreement",
                "relevant_clauses": ["Section_20", "Section_21", "Section_22"],
                "description": "Mistake in contracts"
            },
            {
                "query": "indemnity indemnifier loss promise",
                "relevant_clauses": ["Section_124", "Section_125"],
                "description": "Indemnity contracts"
            },
            {
                "query": "capacity to contract minor competent",
                "relevant_clauses": ["Section_11", "Section_12"],
                "description": "Capacity to contract"
            },
            {
                "query": "communication acceptance revocation",
                "relevant_clauses": ["Section_5", "Section_6", "Section_7", "Section_8"],
                "description": "Communication rules"
            },
            {
                "query": "quasi contract obligation law",
                "relevant_clauses": ["Section_68", "Section_69", "Section_70"],
                "description": "Quasi-contracts"
            },
            {
                "query": "time place performance contract",
                "relevant_clauses": ["Section_46", "Section_47", "Section_48", "Section_49"],
                "description": "Time and place of performance"
            },
            {
                "query": "novation rescission alteration",
                "relevant_clauses": ["Section_62", "Section_63", "Section_64"],
                "description": "Novation and alteration"
            }
        ]
        
        return test_cases
    
    def evaluate_query(self, query: str, relevant_clauses: List[str], 
                      top_k: int = 10, threshold: float = 0.65) -> Dict:
        """
        Evaluate a single query against ground truth
        
        Args:
            query: Search query text
            relevant_clauses: List of relevant clause IDs (ground truth)
            top_k: Number of results to retrieve
            threshold: Minimum similarity threshold
            
        Returns:
            Dictionary with evaluation metrics for this query
        """
        # Search for clauses
        results = self.search_engine.search(query, top_k=top_k)
        
        # Filter by threshold (use 'similarity_score' key)
        filtered_results = [r for r in results if r['similarity_score'] >= threshold]
        
        # Extract retrieved clause IDs
        retrieved_ids = [r['id'] for r in filtered_results]
        
        # Calculate confusion matrix values
        true_positives = len(set(retrieved_ids) & set(relevant_clauses))
        false_positives = len(set(retrieved_ids) - set(relevant_clauses))
        false_negatives = len(set(relevant_clauses) - set(retrieved_ids))
        
        # Calculate metrics
        precision = true_positives / len(retrieved_ids) if retrieved_ids else 0
        recall = true_positives / len(relevant_clauses) if relevant_clauses else 0
        f1_score = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        # Accuracy calculation (for retrieval: how many of top_k are correct)
        accuracy = true_positives / top_k if top_k > 0 else 0
        
        return {
            'query': query,
            'retrieved_count': len(retrieved_ids),
            'relevant_count': len(relevant_clauses),
            'true_positives': true_positives,
            'false_positives': false_positives,
            'false_negatives': false_negatives,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'accuracy': accuracy,
            'retrieved_ids': retrieved_ids,
            'relevant_ids': relevant_clauses
        }
    
    def evaluate_all(self, top_k: int = 10, threshold: float = 0.65) -> Dict:
        """
        Evaluate all test cases and calculate aggregate metrics
        
        Args:
            top_k: Number of results to retrieve per query
            threshold: Minimum similarity threshold
            
        Returns:
            Dictionary with aggregate evaluation results
        """
        test_cases = self.create_test_dataset()
        results = []
        
        print(f"Evaluating {len(test_cases)} test cases...")
        print(f"Top-K: {top_k}, Threshold: {threshold}")
        print("=" * 80)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n[{i}/{len(test_cases)}] {test_case['description']}")
            print(f"Query: {test_case['query']}")
            print(f"Expected clauses: {test_case['relevant_clauses']}")
            
            result = self.evaluate_query(
                test_case['query'],
                test_case['relevant_clauses'],
                top_k=top_k,
                threshold=threshold
            )
            
            result['description'] = test_case['description']
            results.append(result)
            
            print(f"Retrieved: {result['retrieved_ids']}")
            print(f"Precision: {result['precision']:.3f}, Recall: {result['recall']:.3f}, "
                  f"F1: {result['f1_score']:.3f}, Accuracy: {result['accuracy']:.3f}")
        
        # Calculate aggregate metrics
        avg_precision = np.mean([r['precision'] for r in results])
        avg_recall = np.mean([r['recall'] for r in results])
        avg_f1 = np.mean([r['f1_score'] for r in results])
        avg_accuracy = np.mean([r['accuracy'] for r in results])
        
        # Micro-averaged metrics (sum all TP, FP, FN)
        total_tp = sum([r['true_positives'] for r in results])
        total_fp = sum([r['false_positives'] for r in results])
        total_fn = sum([r['false_negatives'] for r in results])
        
        micro_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
        micro_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
        micro_f1 = (2 * micro_precision * micro_recall) / (micro_precision + micro_recall) if (micro_precision + micro_recall) > 0 else 0
        
        aggregate_results = {
            'test_cases_count': len(test_cases),
            'top_k': top_k,
            'threshold': threshold,
            'macro_averaged': {
                'precision': avg_precision,
                'recall': avg_recall,
                'f1_score': avg_f1,
                'accuracy': avg_accuracy
            },
            'micro_averaged': {
                'precision': micro_precision,
                'recall': micro_recall,
                'f1_score': micro_f1,
                'total_true_positives': total_tp,
                'total_false_positives': total_fp,
                'total_false_negatives': total_fn
            },
            'individual_results': results
        }
        
        return aggregate_results
    
    def print_summary(self, results: Dict):
        """
        Print a formatted summary of evaluation results
        
        Args:
            results: Evaluation results from evaluate_all()
        """
        print("\n" + "=" * 80)
        print("EVALUATION SUMMARY")
        print("=" * 80)
        print(f"\nTest Configuration:")
        print(f"  Total Test Cases: {results['test_cases_count']}")
        print(f"  Top-K Retrieved: {results['top_k']}")
        print(f"  Similarity Threshold: {results['threshold']}")
        
        print(f"\n📊 MACRO-AVERAGED METRICS (Average across all queries):")
        print(f"  Precision: {results['macro_averaged']['precision']:.4f} ({results['macro_averaged']['precision']*100:.2f}%)")
        print(f"  Recall:    {results['macro_averaged']['recall']:.4f} ({results['macro_averaged']['recall']*100:.2f}%)")
        print(f"  F1-Score:  {results['macro_averaged']['f1_score']:.4f} ({results['macro_averaged']['f1_score']*100:.2f}%)")
        print(f"  Accuracy:  {results['macro_averaged']['accuracy']:.4f} ({results['macro_averaged']['accuracy']*100:.2f}%)")
        
        print(f"\n📊 MICRO-AVERAGED METRICS (Aggregated across all predictions):")
        print(f"  Precision: {results['micro_averaged']['precision']:.4f} ({results['micro_averaged']['precision']*100:.2f}%)")
        print(f"  Recall:    {results['micro_averaged']['recall']:.4f} ({results['micro_averaged']['recall']*100:.2f}%)")
        print(f"  F1-Score:  {results['micro_averaged']['f1_score']:.4f} ({results['micro_averaged']['f1_score']*100:.2f}%)")
        
        print(f"\n📈 CONFUSION MATRIX TOTALS:")
        print(f"  True Positives:  {results['micro_averaged']['total_true_positives']}")
        print(f"  False Positives: {results['micro_averaged']['total_false_positives']}")
        print(f"  False Negatives: {results['micro_averaged']['total_false_negatives']}")
        
        # Best and worst performing queries
        sorted_by_f1 = sorted(results['individual_results'], key=lambda x: x['f1_score'], reverse=True)
        
        print(f"\n✅ TOP 3 BEST PERFORMING QUERIES:")
        for i, result in enumerate(sorted_by_f1[:3], 1):
            print(f"  {i}. {result['description']}")
            print(f"     F1: {result['f1_score']:.3f}, Precision: {result['precision']:.3f}, Recall: {result['recall']:.3f}")
        
        print(f"\n⚠️  TOP 3 WORST PERFORMING QUERIES:")
        for i, result in enumerate(sorted_by_f1[-3:], 1):
            print(f"  {i}. {result['description']}")
            print(f"     F1: {result['f1_score']:.3f}, Precision: {result['precision']:.3f}, Recall: {result['recall']:.3f}")
        
        print("\n" + "=" * 80)
    
    def save_results(self, results: Dict, output_file: str = "evaluation_results.json"):
        """
        Save evaluation results to JSON file
        
        Args:
            results: Evaluation results
            output_file: Output file path
        """
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {output_path.absolute()}")

def main():
    """Main evaluation function"""
    print("Legal Index FAISS Evaluation")
    print("=" * 80)
    
    # Initialize evaluator
    evaluator = LegalIndexEvaluator(index_dir="./index")
    
    # Run evaluation with different configurations
    configurations = [
        {'top_k': 5, 'threshold': 0.70},
        {'top_k': 7, 'threshold': 0.65},
        {'top_k': 10, 'threshold': 0.60},
    ]
    
    all_results = []
    
    for config in configurations:
        print(f"\n\n{'='*80}")
        print(f"Configuration: Top-K={config['top_k']}, Threshold={config['threshold']}")
        print(f"{'='*80}")
        
        results = evaluator.evaluate_all(
            top_k=config['top_k'],
            threshold=config['threshold']
        )
        
        evaluator.print_summary(results)
        all_results.append(results)
    
    # Save best configuration results
    best_config = max(all_results, key=lambda x: x['macro_averaged']['f1_score'])
    evaluator.save_results(best_config, "best_evaluation_results.json")
    
    # Save all configurations
    evaluator.save_results({
        'all_configurations': all_results,
        'best_configuration': {
            'top_k': best_config['top_k'],
            'threshold': best_config['threshold'],
            'f1_score': best_config['macro_averaged']['f1_score']
        }
    }, "all_evaluation_results.json")
    
    print(f"\n🎯 BEST CONFIGURATION:")
    print(f"   Top-K: {best_config['top_k']}, Threshold: {best_config['threshold']}")
    print(f"   F1-Score: {best_config['macro_averaged']['f1_score']:.4f}")

if __name__ == "__main__":
    main()
