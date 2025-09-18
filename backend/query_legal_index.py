#!/usr/bin/env python3
"""
Legal Search Query Utility

Simple command-line interface for querying the legal document index

Usage:
    python query_legal_index.py "your search query here"
    python query_legal_index.py --interactive
"""

import sys
import json
import argparse
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from build_legal_index import LegalSearchEngine

def format_search_results(results):
    """Format search results for display"""
    if not results:
        print("No relevant sections found.")
        return
    
    print(f"\nFound {len(results)} relevant sections:\n")
    print("=" * 80)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['title']}")
        print(f"   Score: {result['similarity_score']:.3f} | Type: {result['section_type']}")
        if result['chapter']:
            print(f"   Chapter: {result['chapter']}")
        
        # Format text with proper wrapping
        text = result['text']
        if len(text) > 300:
            text = text[:300] + "..."
        
        # Wrap text to reasonable line length
        words = text.split()
        wrapped_lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 <= 70:
                current_line.append(word)
                current_length += len(word) + 1
            else:
                if current_line:
                    wrapped_lines.append(" ".join(current_line))
                current_line = [word]
                current_length = len(word)
        
        if current_line:
            wrapped_lines.append(" ".join(current_line))
        
        for line in wrapped_lines:
            print(f"   {line}")
        
        print("-" * 80)

def interactive_mode(search_engine):
    """Interactive query mode"""
    print("\n🔍 Interactive Legal Document Search")
    print("=" * 50)
    print("Enter your queries below. Type 'quit' to exit.")
    print("You can also use commands:")
    print("  'help' - Show help information")
    print("  'stats' - Show index statistics") 
    print("  'settings' - Modify search settings")
    print("=" * 50)
    
    # Default settings
    settings = {
        'top_k': 5,
        'min_score': 0.3
    }
    
    while True:
        try:
            query = input("\n📝 Query: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            elif query.lower() == 'help':
                print("\n📖 Help:")
                print("- Enter natural language queries about contract law")
                print("- Examples: 'breach of contract', 'void agreements', 'consideration'")
                print("- Use specific terms for better results")
                print("- Adjust settings with 'settings' command")
                continue
                
            elif query.lower() == 'stats':
                print(f"\n📊 Index Statistics:")
                print(f"- Total sections: {len(search_engine.sections)}")
                print(f"- Section types: {set(s.section_type for s in search_engine.sections)}")
                print(f"- Embedding dimension: {search_engine.index.d}")
                continue
                
            elif query.lower() == 'settings':
                print(f"\n⚙️  Current settings:")
                print(f"- Top results: {settings['top_k']}")
                print(f"- Minimum score: {settings['min_score']}")
                
                try:
                    new_k = input(f"New top_k value (current: {settings['top_k']}): ").strip()
                    if new_k:
                        settings['top_k'] = int(new_k)
                    
                    new_score = input(f"New min_score (current: {settings['min_score']}): ").strip()
                    if new_score:
                        settings['min_score'] = float(new_score)
                        
                    print("Settings updated!")
                except ValueError:
                    print("Invalid input. Settings unchanged.")
                continue
            
            elif not query:
                continue
            
            # Perform search
            print(f"\n🔍 Searching for: '{query}'")
            results = search_engine.search(
                query, 
                top_k=settings['top_k'],
                min_score=settings['min_score']
            )
            
            format_search_results(results)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Query the legal document index')
    parser.add_argument('query', nargs='?', help='Search query')
    parser.add_argument('--interactive', '-i', action='store_true', 
                       help='Interactive mode')
    parser.add_argument('--top-k', type=int, default=5,
                       help='Number of top results to return (default: 5)')
    parser.add_argument('--min-score', type=float, default=0.3,
                       help='Minimum similarity score (default: 0.3)')
    parser.add_argument('--index-dir', default='./index',
                       help='Path to index directory (default: ./index)')
    parser.add_argument('--json', action='store_true',
                       help='Output results in JSON format')
    
    args = parser.parse_args()
    
    # Check if index exists
    if not Path(args.index_dir).exists():
        print(f"Error: Index directory '{args.index_dir}' not found.")
        print("Please run 'python build_legal_index.py' first to create the index.")
        return
    
    # Initialize search engine
    print("🔄 Loading search index...")
    search_engine = LegalSearchEngine(args.index_dir)
    search_engine.load_index()
    print(f"✅ Loaded index with {len(search_engine.sections)} sections")
    
    if args.interactive:
        interactive_mode(search_engine)
    
    elif args.query:
        # Single query mode
        results = search_engine.search(
            args.query,
            top_k=args.top_k,
            min_score=args.min_score
        )
        
        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            print(f"\n🔍 Query: '{args.query}'")
            format_search_results(results)
    
    else:
        # No query provided, show help
        parser.print_help()
        print("\nExamples:")
        print("  python query_legal_index.py 'breach of contract'")
        print("  python query_legal_index.py --interactive")
        print("  python query_legal_index.py 'consideration' --top-k 3 --json")

if __name__ == "__main__":
    main()
