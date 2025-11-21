"""
Evaluation Script for Contract-to-Policy Comparison

This script evaluates the performance of the contract comparison system
by testing it against labeled test contracts with known compliance issues.
"""

import json
import sys
import asyncio
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from services.deterministic_policy_processor import get_policy_processor
from services.policy_startup_service import get_startup_service

class ContractComparisonEvaluator:
    """Evaluates contract-to-policy comparison accuracy"""
    
    def __init__(self):
        self.processor = get_policy_processor()
        self.startup_service = get_startup_service()
        
    def create_test_contracts(self) -> List[Dict]:
        """
        Create test contracts with known compliance issues
        
        Returns:
            List of test cases with contracts and expected violations
        """
        test_cases = [
            {
                "name": "Valid Service Agreement",
                "contract": """
SERVICE AGREEMENT

This Service Agreement is entered into on 15th January 2024 between:
- Company XYZ Private Limited (the "Client")
- ABC Services Pvt Ltd (the "Service Provider")

TERMS AND CONDITIONS:
1. Services: The Service Provider shall provide IT consulting services to the Client.
2. Payment: The Client shall pay Rs. 5,00,000 per month within 30 days of invoice.
3. Term: This agreement is valid for 12 months from the date of signing.
4. Termination: Either party may terminate with 60 days written notice.
5. Confidentiality: Both parties agree to maintain confidentiality of sensitive information.
6. Governing Law: This agreement is governed by Indian law and courts of Delhi.
7. Dispute Resolution: Any disputes shall be resolved through arbitration in Delhi.

Signatures:
For Company XYZ: [Authorized Signatory]
For ABC Services: [Authorized Signatory]
Date: 15th January 2024
                """,
                "policy_id": "companies-act-2013",
                "expected_violations": [],
                "expected_compliant": True,
                "description": "Fully compliant service agreement"
            },
            {
                "name": "Missing Consideration",
                "contract": """
AGREEMENT

This agreement is entered into between Party A and Party B.

Party A agrees to provide consulting services to Party B.
Party B agrees to accept the services.

The services shall commence from 1st February 2024.

Signed by both parties.
                """,
                "policy_id": "companies-act-2013",
                "expected_violations": ["consideration", "payment terms"],
                "expected_compliant": False,
                "description": "Missing consideration/payment terms"
            },
            {
                "name": "Vague Termination Clause",
                "contract": """
EMPLOYMENT CONTRACT

Employee: John Doe
Employer: Tech Corp Ltd
Position: Software Developer
Salary: Rs. 80,000 per month

Terms:
1. The employee shall work 40 hours per week.
2. The employee is entitled to 20 days paid leave annually.
3. Either party can terminate this contract.
4. Confidential information must be protected.

Signed: 1st March 2024
                """,
                "policy_id": "companies-act-2013",
                "expected_violations": ["termination notice", "notice period"],
                "expected_compliant": False,
                "description": "Unclear termination provisions"
            },
            {
                "name": "No Dispute Resolution",
                "contract": """
VENDOR AGREEMENT

Vendor: Supplies Inc.
Client: Manufacturing Ltd.

1. Vendor shall supply raw materials as per purchase orders.
2. Payment terms: Net 45 days from delivery.
3. Quality standards: ISO 9001 compliance required.
4. Delivery: Within 7 days of order confirmation.
5. Contract period: 2 years from signing date.

This agreement is binding upon both parties.
Date: 10th April 2024
                """,
                "policy_id": "companies-act-2013",
                "expected_violations": ["dispute resolution", "governing law"],
                "expected_compliant": False,
                "description": "Missing dispute resolution mechanism"
            },
            {
                "name": "Incomplete Contract Elements",
                "contract": """
PARTNERSHIP DEED

Partners: Mr. A and Mr. B

We agree to start a business together.
Profits will be shared equally.
The business will operate in Delhi.

Signatures of both partners.
                """,
                "policy_id": "companies-act-2013",
                "expected_violations": ["business details", "capital contribution", "management", "dissolution"],
                "expected_compliant": False,
                "description": "Missing essential partnership terms"
            },
            {
                "name": "Good Lease Agreement",
                "contract": """
LEASE AGREEMENT

Lessor: Property Owners Ltd.
Lessee: Business Solutions Pvt Ltd.

Property: Office Space, 2000 sq ft, Connaught Place, Delhi

Terms:
1. Lease Period: 3 years from 1st May 2024 to 30th April 2027
2. Monthly Rent: Rs. 2,00,000 payable by 5th of each month
3. Security Deposit: Rs. 6,00,000 (refundable)
4. Maintenance: Lessee responsible for interior maintenance
5. Termination: 3 months written notice required
6. Renewal: Option to renew for 2 years with 10% rent increase
7. Dispute Resolution: Arbitration in Delhi under Arbitration Act
8. Governing Law: Indian Contract Act and Delhi Rent Control Act

Signatures:
Lessor: [Authorized Signatory]
Lessee: [Authorized Signatory]
Date: 1st May 2024
                """,
                "policy_id": "companies-act-2013",
                "expected_violations": [],
                "expected_compliant": True,
                "description": "Comprehensive lease agreement"
            },
            {
                "name": "Unenforceable Terms",
                "contract": """
EMPLOYMENT AGREEMENT

This is to certify that Mr. X is employed by Company Y.

Salary: Rs. 50,000 per month
Working Hours: As required by company
Leave: At management discretion
Termination: Company can terminate anytime without notice
Employee cannot join competitor for 10 years after leaving

Signed by employer only.
                """,
                "policy_id": "companies-act-2013",
                "expected_violations": ["one-sided termination", "unreasonable restraint", "notice period"],
                "expected_compliant": False,
                "description": "Contains potentially unenforceable clauses"
            },
            {
                "name": "Missing Parties Details",
                "contract": """
SALES CONTRACT

Product: Industrial Machinery
Quantity: 5 units
Price: Rs. 25,00,000
Delivery: Within 60 days

Payment: 50% advance, 50% on delivery
Warranty: 1 year parts and service

This contract is effective immediately.
                """,
                "policy_id": "companies-act-2013",
                "expected_violations": ["party identification", "addresses", "signatures"],
                "expected_compliant": False,
                "description": "Missing party details and signatures"
            }
        ]
        
        return test_cases
    
    async def evaluate_single_contract(self, test_case: Dict) -> Dict:
        """
        Evaluate a single contract comparison
        
        Args:
            test_case: Test case with contract and expected results
            
        Returns:
            Dictionary with evaluation results
        """
        print(f"\n{'='*80}")
        print(f"Test: {test_case['name']}")
        print(f"Description: {test_case['description']}")
        print(f"Expected: {'Compliant' if test_case['expected_compliant'] else 'Non-Compliant'}")
        
        try:
            # Perform comparison
            result = self.processor.compare_contract_with_policy(
                contract_text=test_case['contract'],
                policy_id=test_case['policy_id'],
                use_cache=False
            )
            
            if result is None:
                print("❌ Comparison failed - returned None")
                return {
                    'test_name': test_case['name'],
                    'success': False,
                    'error': 'Comparison returned None'
                }
            
            # Extract violations
            detected_violations = result.violations if hasattr(result, 'violations') else []
            detected_violation_texts = [v.get('violation', '').lower() if isinstance(v, dict) else str(v).lower() 
                                       for v in detected_violations]
            
            compliance_score = result.meta.get('compliance_score', 0.0)
            
            # Determine if system thinks it's compliant
            system_compliant = len(detected_violations) == 0 or compliance_score >= 0.8
            
            # Check for expected violations
            expected_violations_lower = [v.lower() for v in test_case['expected_violations']]
            
            # Count matches
            violations_found = []
            violations_missed = []
            
            for expected_v in expected_violations_lower:
                found = any(expected_v in detected_text for detected_text in detected_violation_texts)
                if found:
                    violations_found.append(expected_v)
                else:
                    violations_missed.append(expected_v)
            
            # False positives (violations detected but not expected)
            false_positives = []
            if test_case['expected_compliant'] and len(detected_violations) > 0:
                false_positives = detected_violations
            
            # Calculate metrics
            true_positive = len(violations_found)
            false_negative = len(violations_missed)
            false_positive_count = len(false_positives)
            true_negative = 1 if (test_case['expected_compliant'] and system_compliant) else 0
            
            # Precision and Recall for violation detection
            precision = true_positive / (true_positive + false_positive_count) if (true_positive + false_positive_count) > 0 else 0
            recall = true_positive / len(expected_violations_lower) if len(expected_violations_lower) > 0 else (1 if system_compliant and test_case['expected_compliant'] else 0)
            f1_score = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            # Overall compliance classification accuracy
            classification_correct = (system_compliant == test_case['expected_compliant'])
            
            print(f"\n📊 Results:")
            print(f"   Compliance Score: {compliance_score:.2f}")
            print(f"   System Classification: {'Compliant' if system_compliant else 'Non-Compliant'}")
            print(f"   Classification Correct: {'✅ Yes' if classification_correct else '❌ No'}")
            print(f"   Violations Detected: {len(detected_violations)}")
            print(f"   Expected Violations Found: {true_positive}/{len(expected_violations_lower)}")
            print(f"   Precision: {precision:.3f}")
            print(f"   Recall: {recall:.3f}")
            print(f"   F1-Score: {f1_score:.3f}")
            
            if violations_found:
                print(f"   ✅ Found: {violations_found}")
            if violations_missed:
                print(f"   ❌ Missed: {violations_missed}")
            if false_positives:
                print(f"   ⚠️  False Positives: {len(false_positives)}")
            
            return {
                'test_name': test_case['name'],
                'success': True,
                'expected_compliant': test_case['expected_compliant'],
                'system_compliant': system_compliant,
                'classification_correct': classification_correct,
                'compliance_score': compliance_score,
                'expected_violations_count': len(expected_violations_lower),
                'detected_violations_count': len(detected_violations),
                'true_positives': true_positive,
                'false_negatives': false_negative,
                'false_positives': false_positive_count,
                'true_negatives': true_negative,
                'precision': precision,
                'recall': recall,
                'f1_score': f1_score,
                'violations_found': violations_found,
                'violations_missed': violations_missed
            }
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'test_name': test_case['name'],
                'success': False,
                'error': str(e)
            }
    
    async def evaluate_all(self) -> Dict:
        """
        Evaluate all test contracts
        
        Returns:
            Aggregate evaluation results
        """
        # Initialize services
        print("🔄 Initializing services...")
        await self.startup_service.initialize_policies()
        
        test_cases = self.create_test_contracts()
        results = []
        
        print(f"\n{'='*80}")
        print(f"EVALUATING CONTRACT COMPARISON SYSTEM")
        print(f"Total Test Cases: {len(test_cases)}")
        print(f"{'='*80}")
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n[{i}/{len(test_cases)}] Running test...")
            result = await self.evaluate_single_contract(test_case)
            results.append(result)
        
        # Calculate aggregate metrics
        successful_tests = [r for r in results if r.get('success', False)]
        
        if not successful_tests:
            print("\n❌ No successful tests to aggregate")
            return {'error': 'All tests failed'}
        
        # Classification metrics
        total_correct = sum(1 for r in successful_tests if r.get('classification_correct', False))
        classification_accuracy = total_correct / len(successful_tests)
        
        # Violation detection metrics
        total_tp = sum(r.get('true_positives', 0) for r in successful_tests)
        total_fp = sum(r.get('false_positives', 0) for r in successful_tests)
        total_fn = sum(r.get('false_negatives', 0) for r in successful_tests)
        total_tn = sum(r.get('true_negatives', 0) for r in successful_tests)
        
        # Aggregate precision, recall, F1
        avg_precision = np.mean([r.get('precision', 0) for r in successful_tests])
        avg_recall = np.mean([r.get('recall', 0) for r in successful_tests])
        avg_f1 = np.mean([r.get('f1_score', 0) for r in successful_tests])
        
        # Micro-averaged metrics
        micro_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
        micro_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
        micro_f1 = (2 * micro_precision * micro_recall) / (micro_precision + micro_recall) if (micro_precision + micro_recall) > 0 else 0
        
        # Overall accuracy (correct predictions / total)
        overall_accuracy = (total_tp + total_tn) / (total_tp + total_tn + total_fp + total_fn) if (total_tp + total_tn + total_fp + total_fn) > 0 else 0
        
        aggregate_results = {
            'total_tests': len(test_cases),
            'successful_tests': len(successful_tests),
            'failed_tests': len(test_cases) - len(successful_tests),
            'classification_accuracy': classification_accuracy,
            'overall_accuracy': overall_accuracy,
            'macro_averaged': {
                'precision': avg_precision,
                'recall': avg_recall,
                'f1_score': avg_f1
            },
            'micro_averaged': {
                'precision': micro_precision,
                'recall': micro_recall,
                'f1_score': micro_f1
            },
            'confusion_matrix': {
                'true_positives': total_tp,
                'false_positives': total_fp,
                'false_negatives': total_fn,
                'true_negatives': total_tn
            },
            'individual_results': results
        }
        
        return aggregate_results
    
    def print_summary(self, results: Dict):
        """Print formatted summary of results"""
        print(f"\n{'='*80}")
        print("EVALUATION SUMMARY - CONTRACT COMPARISON SYSTEM")
        print(f"{'='*80}")
        
        print(f"\n📋 Test Statistics:")
        print(f"   Total Tests: {results['total_tests']}")
        print(f"   Successful: {results['successful_tests']}")
        print(f"   Failed: {results['failed_tests']}")
        
        print(f"\n🎯 CLASSIFICATION ACCURACY:")
        print(f"   Accuracy: {results['classification_accuracy']:.4f} ({results['classification_accuracy']*100:.2f}%)")
        
        print(f"\n📊 VIOLATION DETECTION - MACRO-AVERAGED METRICS:")
        print(f"   Precision: {results['macro_averaged']['precision']:.4f} ({results['macro_averaged']['precision']*100:.2f}%)")
        print(f"   Recall:    {results['macro_averaged']['recall']:.4f} ({results['macro_averaged']['recall']*100:.2f}%)")
        print(f"   F1-Score:  {results['macro_averaged']['f1_score']:.4f} ({results['macro_averaged']['f1_score']*100:.2f}%)")
        
        print(f"\n📊 VIOLATION DETECTION - MICRO-AVERAGED METRICS:")
        print(f"   Precision: {results['micro_averaged']['precision']:.4f} ({results['micro_averaged']['precision']*100:.2f}%)")
        print(f"   Recall:    {results['micro_averaged']['recall']:.4f} ({results['micro_averaged']['recall']*100:.2f}%)")
        print(f"   F1-Score:  {results['micro_averaged']['f1_score']:.4f} ({results['micro_averaged']['f1_score']*100:.2f}%)")
        
        print(f"\n📈 OVERALL ACCURACY (All Predictions):")
        print(f"   Accuracy: {results['overall_accuracy']:.4f} ({results['overall_accuracy']*100:.2f}%)")
        
        print(f"\n📈 CONFUSION MATRIX:")
        print(f"   True Positives:  {results['confusion_matrix']['true_positives']}")
        print(f"   False Positives: {results['confusion_matrix']['false_positives']}")
        print(f"   True Negatives:  {results['confusion_matrix']['true_negatives']}")
        print(f"   False Negatives: {results['confusion_matrix']['false_negatives']}")
        
        # Best and worst
        successful = [r for r in results['individual_results'] if r.get('success', False)]
        sorted_by_f1 = sorted(successful, key=lambda x: x.get('f1_score', 0), reverse=True)
        
        print(f"\n✅ TOP 3 BEST PERFORMING TESTS:")
        for i, r in enumerate(sorted_by_f1[:3], 1):
            print(f"   {i}. {r['test_name']}")
            print(f"      F1: {r.get('f1_score', 0):.3f}, Precision: {r.get('precision', 0):.3f}, Recall: {r.get('recall', 0):.3f}")
        
        print(f"\n⚠️  TOP 3 WORST PERFORMING TESTS:")
        for i, r in enumerate(sorted_by_f1[-3:], 1):
            print(f"   {i}. {r['test_name']}")
            print(f"      F1: {r.get('f1_score', 0):.3f}, Precision: {r.get('precision', 0):.3f}, Recall: {r.get('recall', 0):.3f}")
        
        print(f"\n{'='*80}")
    
    def save_results(self, results: Dict, filename: str = "contract_comparison_evaluation.json"):
        """Save results to JSON file"""
        output_path = Path(filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Results saved to: {output_path.absolute()}")

async def main():
    """Main evaluation function"""
    print("Contract Comparison System Evaluation")
    print("="*80)
    
    evaluator = ContractComparisonEvaluator()
    results = await evaluator.evaluate_all()
    
    if 'error' not in results:
        evaluator.print_summary(results)
        evaluator.save_results(results)
    else:
        print(f"\n❌ Evaluation failed: {results['error']}")

if __name__ == "__main__":
    asyncio.run(main())
