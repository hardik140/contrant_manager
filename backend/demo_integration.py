#!/usr/bin/env python3
"""
Legal Document Index Integration Example

Demonstrates how to integrate the legal search functionality with the existing contract management system
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from build_legal_index import LegalSearchEngine
import json

class ContractLegalAnalyzer:
    """
    Integrates legal document search with contract analysis
    """
    
    def __init__(self, index_dir="./index"):
        """Initialize with legal document index"""
        self.search_engine = LegalSearchEngine(index_dir)
        self.search_engine.load_index()
        print(f"✅ Loaded legal index with {len(self.search_engine.sections)} sections")
    
    def find_relevant_legal_provisions(self, contract_text: str, top_k: int = 5) -> list:
        """
        Find legal provisions relevant to a contract
        
        Args:
            contract_text: Full text of the contract
            top_k: Number of relevant provisions to return
            
        Returns:
            List of relevant legal provisions with scores
        """
        # Extract key terms and phrases from contract for better search
        key_phrases = self._extract_key_legal_phrases(contract_text)
        
        all_results = []
        
        # Search for each key phrase
        for phrase in key_phrases:
            results = self.search_engine.search(phrase, top_k=3, min_score=0.4)
            for result in results:
                result['search_phrase'] = phrase
                all_results.append(result)
        
        # Remove duplicates and sort by score
        seen_ids = set()
        unique_results = []
        for result in sorted(all_results, key=lambda x: x['similarity_score'], reverse=True):
            if result['id'] not in seen_ids:
                seen_ids.add(result['id'])
                unique_results.append(result)
        
        return unique_results[:top_k]
    
    def _extract_key_legal_phrases(self, contract_text: str) -> list:
        """Extract key legal phrases from contract text for search"""
        # Common legal concepts to search for
        legal_concepts = [
            "breach of contract",
            "consideration",
            "void agreement",
            "voidable contract", 
            "contract formation",
            "termination",
            "performance",
            "remedies",
            "damages",
            "liability",
            "indemnity",
            "confidentiality",
            "assignment",
            "force majeure"
        ]
        
        # Find which concepts are mentioned in the contract
        relevant_concepts = []
        contract_lower = contract_text.lower()
        
        for concept in legal_concepts:
            if any(word in contract_lower for word in concept.split()):
                relevant_concepts.append(concept)
        
        # Add some generic searches if no specific concepts found
        if not relevant_concepts:
            relevant_concepts = ["agreement", "contract", "obligation"]
        
        return relevant_concepts[:5]  # Limit to avoid too many searches
    
    def analyze_contract_compliance(self, contract_text: str) -> dict:
        """
        Analyze contract against Indian Contract Act provisions
        
        Args:
            contract_text: Full text of the contract
            
        Returns:
            Analysis report with relevant legal provisions
        """
        print("🔍 Analyzing contract against Indian Contract Act...")
        
        # Find relevant provisions
        relevant_provisions = self.find_relevant_legal_provisions(contract_text)
        
        # Categorize provisions by type
        analysis = {
            "total_provisions_found": len(relevant_provisions),
            "provisions_by_type": {},
            "high_relevance_provisions": [],
            "recommendations": [],
            "detailed_provisions": relevant_provisions
        }
        
        # Group by section type
        for provision in relevant_provisions:
            section_type = provision['section_type']
            if section_type not in analysis["provisions_by_type"]:
                analysis["provisions_by_type"][section_type] = []
            analysis["provisions_by_type"][section_type].append(provision)
        
        # Identify high relevance provisions (score > 0.6)
        analysis["high_relevance_provisions"] = [
            p for p in relevant_provisions if p['similarity_score'] > 0.6
        ]
        
        # Generate recommendations
        analysis["recommendations"] = self._generate_recommendations(relevant_provisions)
        
        return analysis
    
    def _generate_recommendations(self, provisions: list) -> list:
        """Generate recommendations based on found provisions"""
        recommendations = []
        
        # Check for common compliance issues
        provision_titles = [p['title'].lower() for p in provisions]
        
        if any('void' in title for title in provision_titles):
            recommendations.append(
                "⚠️  Found provisions related to void agreements. "
                "Ensure contract terms comply with Indian Contract Act requirements."
            )
        
        if any('consideration' in title for title in provision_titles):
            recommendations.append(
                "✅ Contract involves consideration. "
                "Verify that consideration is lawful and sufficient."
            )
        
        if any('breach' in title for title in provision_titles):
            recommendations.append(
                "📋 Contract may involve breach scenarios. "
                "Review remedy and compensation clauses."
            )
        
        if len(provisions) < 3:
            recommendations.append(
                "🔍 Limited legal provisions found. "
                "Consider more specific legal review for complex terms."
            )
        
        return recommendations

def demo_integration():
    """Demonstrate the integration with sample contract"""
    
    # Sample contract text
    sample_contract = """
    Service Agreement
    
    This Service Agreement is entered into on January 1, 2024, between 
    Company A (Service Provider) and Company B (Client).
    
    1. SERVICES: Company A agrees to provide software development services
    for a period of 12 months.
    
    2. CONSIDERATION: Client agrees to pay $50,000 for the services, 
    payable in monthly installments of $4,167.
    
    3. PERFORMANCE: Service Provider shall deliver services with professional
    competence and in accordance with industry standards.
    
    4. TERMINATION: Either party may terminate this agreement with 30 days 
    written notice. Upon termination, all outstanding amounts shall be paid.
    
    5. BREACH: In case of material breach, the non-breaching party may 
    seek damages and specific performance.
    
    6. CONFIDENTIALITY: Both parties agree to maintain confidentiality 
    of proprietary information exchanged during the term.
    
    7. FORCE MAJEURE: Neither party shall be liable for delays due to 
    circumstances beyond their reasonable control.
    """
    
    print("🚀 Legal Document Index Integration Demo")
    print("=" * 60)
    
    try:
        # Initialize analyzer
        analyzer = ContractLegalAnalyzer()
        
        # Analyze the sample contract
        print(f"\n📄 Analyzing sample contract...")
        print(f"Contract length: {len(sample_contract)} characters")
        
        analysis = analyzer.analyze_contract_compliance(sample_contract)
        
        # Display results
        print("\n📊 Analysis Results:")
        print(f"- Total relevant provisions found: {analysis['total_provisions_found']}")
        print(f"- High relevance provisions: {len(analysis['high_relevance_provisions'])}")
        
        print(f"\n📋 Provisions by type:")
        for ptype, provisions in analysis['provisions_by_type'].items():
            print(f"  - {ptype.title()}: {len(provisions)} provisions")
        
        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(analysis['recommendations'], 1):
            print(f"  {i}. {rec}")
        
        print(f"\n🔍 Top Relevant Legal Provisions:")
        for i, provision in enumerate(analysis['detailed_provisions'][:3], 1):
            print(f"\n{i}. {provision['title']}")
            print(f"   Relevance Score: {provision['similarity_score']:.3f}")
            print(f"   Search Phrase: '{provision['search_phrase']}'")
            print(f"   Text: {provision['text'][:150]}...")
            
        print("\n" + "=" * 60)
        print("✅ Integration demo completed successfully!")
        
        return analysis
        
    except Exception as e:
        print(f"❌ Error in demo: {e}")
        return None

def export_analysis_report(analysis: dict, filename: str = "legal_analysis_report.json"):
    """Export analysis to JSON file"""
    if analysis:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        print(f"📄 Analysis report exported to: {filename}")

if __name__ == "__main__":
    # Run the demo
    analysis_result = demo_integration()
    
    if analysis_result:
        # Export the results
        export_analysis_report(analysis_result)
        
        # Show final summary
        print(f"\n🎯 Integration Summary:")
        print(f"✅ Legal document index successfully integrated")
        print(f"✅ Contract analysis completed") 
        print(f"✅ {analysis_result['total_provisions_found']} relevant provisions identified")
        print(f"✅ Report generated with recommendations")
        
        print(f"\n📁 Files created:")
        print(f"  - ./index/faiss.index - FAISS vector index")
        print(f"  - ./index/act_clauses.jsonl - Legal provisions metadata") 
        print(f"  - ./index/ids.npy - Section ID mappings")
        print(f"  - legal_analysis_report.json - Analysis report")
        
        print(f"\n🔧 Usage in your application:")
        print(f"```python")
        print(f"from build_legal_index import LegalSearchEngine")
        print(f"search_engine = LegalSearchEngine('./index')")
        print(f"search_engine.load_index()")
        print(f"results = search_engine.search('your legal query', top_k=5)")
        print(f"```")
