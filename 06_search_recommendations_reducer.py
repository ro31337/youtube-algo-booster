#!/usr/bin/env python3
"""
Search Recommendations Reducer - Randomly selects a subset of videos and shorts from search results
Reduces the data size to prevent AI timeout when analyzing results
"""

import json
import random
from pathlib import Path
from datetime import datetime
import sys

def load_search_results():
    """Load the full search results from the previous script"""
    json_file = Path("05_youtube_search_recommendations.json")
    
    if not json_file.exists():
        print("❌ ERROR: File '05_youtube_search_recommendations.json' not found!")
        print("\nYou need to run the search script first:")
        print("1. Run: python 05_youtube_search_recommendations.py")
        print("2. Then run this script again")
        sys.exit(1)
    
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def reduce_search_results(search_data, videos_per_search=3, shorts_per_search=3):
    """
    Randomly select a subset of videos and shorts from each search
    
    Args:
        search_data: Original search results data
        videos_per_search: Number of videos to keep per search (default: 3)
        shorts_per_search: Number of shorts to keep per search (default: 3)
    
    Returns:
        Reduced search results data
    """
    
    reduced_data = {
        "original_search_time": search_data.get("search_time"),
        "reduction_time": datetime.now().isoformat(),
        "reduction_params": {
            "videos_per_search": videos_per_search,
            "shorts_per_search": shorts_per_search
        },
        "searches": []
    }
    
    for search in search_data.get("searches", []):
        videos = search.get("videos", [])
        shorts = search.get("shorts", [])
        
        # Randomly select videos and shorts
        selected_videos = random.sample(videos, min(videos_per_search, len(videos)))
        selected_shorts = random.sample(shorts, min(shorts_per_search, len(shorts)))
        
        reduced_search = {
            "search_term": search.get("search_term"),
            "original_counts": {
                "videos": len(videos),
                "shorts": len(shorts)
            },
            "videos": selected_videos,
            "shorts": selected_shorts
        }
        
        # Include error if present
        if "error" in search:
            reduced_search["error"] = search["error"]
        
        reduced_data["searches"].append(reduced_search)
    
    return reduced_data

def save_reduced_results(reduced_data):
    """Save the reduced results to a new JSON file"""
    output_file = Path("06_search_recommendations_reduced.json")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(reduced_data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Reduced results saved to: {output_file}")
    return output_file

def display_summary(original_data, reduced_data):
    """Display summary of the reduction process"""
    print("\n" + "=" * 60)
    print("SEARCH RESULTS REDUCTION SUMMARY")
    print("=" * 60)
    
    # Original counts
    original_total_videos = sum(len(s.get("videos", [])) for s in original_data.get("searches", []))
    original_total_shorts = sum(len(s.get("shorts", [])) for s in original_data.get("searches", []))
    
    # Reduced counts
    reduced_total_videos = sum(len(s.get("videos", [])) for s in reduced_data.get("searches", []))
    reduced_total_shorts = sum(len(s.get("shorts", [])) for s in reduced_data.get("searches", []))
    
    print(f"\n📊 Reduction Statistics:")
    print(f"  Original videos: {original_total_videos}")
    print(f"  Reduced videos: {reduced_total_videos} ({reduced_total_videos/original_total_videos*100:.1f}%)")
    print(f"  Original shorts: {original_total_shorts}")
    print(f"  Reduced shorts: {reduced_total_shorts} ({reduced_total_shorts/original_total_shorts*100:.1f}%)")
    
    # Per search breakdown
    print(f"\n📚 Per Search Breakdown:")
    for idx, search in enumerate(reduced_data.get("searches", []), 1):
        search_term = search.get("search_term", "Unknown")
        original_counts = search.get("original_counts", {})
        print(f"  {idx}. \"{search_term}\"")
        print(f"     Videos: {original_counts.get('videos', 0)} → {len(search.get('videos', []))}")
        print(f"     Shorts: {original_counts.get('shorts', 0)} → {len(search.get('shorts', []))}")
    
    print("\n" + "=" * 60)

def main():
    """Main entry point"""
    print("=" * 60)
    print("Search Recommendations Reducer")
    print("=" * 60)
    
    # Set random seed for reproducibility (optional - comment out for true randomness)
    # random.seed(42)
    
    # Load original search results
    print("\n📂 Loading original search results...")
    original_data = load_search_results()
    
    total_searches = len(original_data.get("searches", []))
    print(f"  Found {total_searches} searches")
    
    # Reduce the results
    print("\n🔄 Reducing search results...")
    print("  Selecting 3 random videos and 3 random shorts per search...")
    reduced_data = reduce_search_results(original_data, videos_per_search=3, shorts_per_search=3)
    
    # Save reduced results
    output_file = save_reduced_results(reduced_data)
    
    # Display summary
    display_summary(original_data, reduced_data)
    
    print(f"\n✅ Reduction complete!")
    print(f"   Next step: Run python 07_content_curator.py to analyze the reduced results")

if __name__ == "__main__":
    main()