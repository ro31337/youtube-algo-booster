#!/usr/bin/env python3
"""
YouTube Action List Generator - Creates a list of videos to like and dislike
Takes videos to dislike from homepage analysis and videos to like from search results
"""

import json
import random
from pathlib import Path
from datetime import datetime
import sys

def load_homepage_results():
    """Load the homepage content curator results"""
    json_file = Path("04_content_curator.json")
    
    if not json_file.exists():
        print("❌ ERROR: File '04_content_curator.json' not found!")
        print("\nYou need to run the homepage content curator first:")
        print("1. Run: python 04_content_curator.py")
        sys.exit(1)
    
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_search_results():
    """Load the search results content curator results"""
    json_file = Path("07_content_curator.json")
    
    if not json_file.exists():
        print("❌ ERROR: File '07_content_curator.json' not found!")
        print("\nYou need to run all scripts in order:")
        print("1. Run: python 04_content_curator.py")
        print("2. Run: python 05_youtube_search_recommendations.py")
        print("3. Run: python 06_search_recommendations_reducer.py")
        print("4. Run: python 07_content_curator.py")
        print("5. Then run this script")
        sys.exit(1)
    
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_videos_to_dislike(homepage_data):
    """Extract all videos and shorts marked for dislike from homepage"""
    dislike_list = []
    
    # Get videos to dislike
    for video in homepage_data.get("videos", []):
        if not video.get("like", True):  # If like is false or missing
            dislike_list.append({
                "url": video.get("url"),
                "type": "video",
                "action": "dislike",
                "source": "homepage"
            })
    
    # Get shorts to dislike
    for short in homepage_data.get("shorts", []):
        if not short.get("like", True):  # If like is false or missing
            dislike_list.append({
                "url": short.get("url"),
                "type": "short",
                "action": "dislike",
                "source": "homepage"
            })
    
    return dislike_list

def extract_videos_to_like(search_data, max_videos=15, max_shorts=15):
    """
    Extract random videos and shorts marked for like from search results
    
    Args:
        search_data: Search results data with like/dislike marks
        max_videos: Maximum number of videos to like (default: 10)
        max_shorts: Maximum number of shorts to like (default: 10)
    
    Returns:
        List of items to like
    """
    all_liked_videos = []
    all_liked_shorts = []
    
    # Collect all liked videos and shorts from all searches
    for search in search_data.get("searches", []):
        search_term = search.get("search_term", "Unknown")
        
        # Collect liked videos
        for video in search.get("videos", []):
            if video.get("like", False):
                all_liked_videos.append({
                    "url": video.get("url"),
                    "type": "video",
                    "action": "like",
                    "source": f"search: {search_term}"
                })
        
        # Collect liked shorts
        for short in search.get("shorts", []):
            if short.get("like", False):
                all_liked_shorts.append({
                    "url": short.get("url"),
                    "type": "short",
                    "action": "like",
                    "source": f"search: {search_term}"
                })
    
    # Randomly select up to max_videos and max_shorts
    selected_videos = random.sample(all_liked_videos, min(max_videos, len(all_liked_videos)))
    selected_shorts = random.sample(all_liked_shorts, min(max_shorts, len(all_liked_shorts)))
    
    # Combine and return
    like_list = selected_videos + selected_shorts
    
    return like_list, len(all_liked_videos), len(all_liked_shorts)

def create_action_list(dislike_list, like_list):
    """Create the final action list with all items"""
    action_list = {
        "creation_time": datetime.now().isoformat(),
        "summary": {
            "total_to_dislike": len(dislike_list),
            "total_to_like": len(like_list),
            "videos_to_dislike": sum(1 for item in dislike_list if item["type"] == "video"),
            "shorts_to_dislike": sum(1 for item in dislike_list if item["type"] == "short"),
            "videos_to_like": sum(1 for item in like_list if item["type"] == "video"),
            "shorts_to_like": sum(1 for item in like_list if item["type"] == "short")
        },
        "actions": []
    }
    
    # Add all items to the actions list
    # First add dislikes, then likes
    for item in dislike_list:
        action_list["actions"].append({
            "url": item["url"],
            "type": item["type"],
            "action": item["action"]
        })
    
    for item in like_list:
        action_list["actions"].append({
            "url": item["url"],
            "type": item["type"],
            "action": item["action"]
        })
    
    return action_list

def save_action_list(action_list):
    """Save the action list to a JSON file"""
    output_file = Path("08_youtube_action_list.json")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(action_list, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Action list saved to: {output_file}")
    return output_file

def display_summary(action_list, total_available_videos, total_available_shorts):
    """Display summary of the action list"""
    print("\n" + "=" * 60)
    print("YOUTUBE ACTION LIST SUMMARY")
    print("=" * 60)
    
    summary = action_list["summary"]
    
    print(f"\n👎 VIDEOS TO DISLIKE (from homepage):")
    print(f"  Videos: {summary['videos_to_dislike']}")
    print(f"  Shorts: {summary['shorts_to_dislike']}")
    print(f"  Total: {summary['total_to_dislike']}")
    
    print(f"\n👍 VIDEOS TO LIKE (from search results):")
    print(f"  Videos: {summary['videos_to_like']} (randomly selected from {total_available_videos} available)")
    print(f"  Shorts: {summary['shorts_to_like']} (randomly selected from {total_available_shorts} available)")
    print(f"  Total: {summary['total_to_like']}")
    
    print(f"\n📊 TOTAL ACTIONS:")
    print(f"  Total items in action list: {len(action_list['actions'])}")
    
    # Show some examples
    print(f"\n📝 Sample Actions (first 5 of each type):")
    
    # Show dislike samples
    dislike_samples = [a for a in action_list["actions"] if a["action"] == "dislike"][:5]
    if dislike_samples:
        print("  Dislike samples:")
        for item in dislike_samples:
            print(f"    - {item['type']}: {item['url'][:60]}...")
    
    # Show like samples
    like_samples = [a for a in action_list["actions"] if a["action"] == "like"][:5]
    if like_samples:
        print("  Like samples:")
        for item in like_samples:
            print(f"    - {item['type']}: {item['url'][:60]}...")
    
    print("\n" + "=" * 60)

def main():
    """Main entry point"""
    print("=" * 60)
    print("YouTube Action List Generator")
    print("=" * 60)
    
    # Load data from both sources
    print("\n📂 Loading homepage analysis...")
    homepage_data = load_homepage_results()
    
    print("📂 Loading search results analysis...")
    search_data = load_search_results()
    
    # Extract videos to dislike (unlimited from homepage)
    print("\n🔍 Extracting videos to dislike from homepage...")
    dislike_list = extract_videos_to_dislike(homepage_data)
    print(f"  Found {len(dislike_list)} items to dislike")
    
    # Extract videos to like (max 10 videos, 10 shorts from search)
    print("\n🔍 Extracting videos to like from search results...")
    like_list, total_videos, total_shorts = extract_videos_to_like(search_data, max_videos=15, max_shorts=15)
    print(f"  Selected {len(like_list)} items to like")
    
    # Create the action list
    print("\n📝 Creating action list...")
    action_list = create_action_list(dislike_list, like_list)
    
    # Save the action list
    output_file = save_action_list(action_list)
    
    # Display summary
    display_summary(action_list, total_videos, total_shorts)
    
    print(f"\n✅ Action list generated successfully!")
    print(f"   The list contains all videos to dislike from homepage")
    print(f"   and up to 10 videos + 10 shorts to like from search results")
    print(f"   Next step: Use this list to perform like/dislike actions on YouTube")

if __name__ == "__main__":
    main()