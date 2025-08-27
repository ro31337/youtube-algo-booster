#!/usr/bin/env python3
"""
AI-Powered Content Curator - Uses OpenAI to categorize videos as educational or not
Provides recommendations for educational content suitable for a school-age child
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
import openai
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def load_videos_json():
    """Load the videos JSON file from previous script"""
    json_file = Path("03_youtube_get_index_page_videos.json")
    
    if not json_file.exists():
        print("❌ ERROR: File '03_youtube_get_index_page_videos.json' not found!")
        print("\nYou need to run the video extraction first:")
        print("1. Run: python 03_youtube_get_index_page_videos.py")
        print("2. Then run this script again")
        sys.exit(1)
    
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_math_standards():
    """Load 6th grade math standards if available"""
    standards_file = Path("04_current_grade_math_standards.txt")
    if standards_file.exists():
        with open(standards_file, 'r', encoding='utf-8') as f:
            return f.read()
    return None

def create_prompt(videos_data):
    """Create the prompt for OpenAI"""
    
    # Load math standards
    math_standards = load_math_standards()
    
    # Extract themes from video titles for seeding recommendations
    video_titles = [v.get('title', '') for v in videos_data.get('videos', [])]
    short_titles = [s.get('title', '') for s in videos_data.get('shorts', [])]
    all_titles = ' '.join(video_titles + short_titles)
    
    prompt = """Your task is to review this JSON with videos and determine whether each video is desirable or undesirable based on its title. 

Context: An 11-year-old student (born 2013) in 6th grade in California will be watching these videos. The parents' goal is to ensure the child doesn't waste time on YouTube but instead uses it for education and learning.

IMPORTANT: This is an 11-year-old 6th grader, NOT a small child. They are capable of understanding more sophisticated content.

Your objectives:
1. Help the student learn mathematics aligned with 6th grade standards
2. Protect the student's mental health
3. Guide them toward academic success and intellectual development

For each video:
- If the title suggests mind-numbing, time-wasting content, mark it with "like": false
- If the title suggests educational, enriching content, mark it with "like": true

Additionally, at the end of the JSON, add a "recommendations" field as a FLAT LIST of 10 search terms for YouTube.

CRITICAL REQUIREMENTS FOR RECOMMENDATIONS:
1. Return as a FLAT LIST: "recommendations": ["search term 1", "search term 2", ...]
2. Each run should produce DIFFERENT, RANDOMIZED recommendations - vary topics, approaches, and phrasing
3. Base recommendations on themes from the actual video titles provided (gaming, geography, cooking, etc.)
4. Mix 5 MATH and 5 CURIOSITY recommendations randomly in the list

For MATH recommendations (5 items total):
- EXACTLY 2 must include the word "easy" (e.g., "easy 6th grade fractions", "easy ratio problems middle school")
- Remaining 3 should vary: visual, practice, explained, tutorial, step-by-step, etc.
- Topics to randomize: ratios, fractions, negative numbers, algebra, coordinate plane, statistics, percentages, decimals
- Examples: "easy 6th grade ratio word problems", "visual fraction division tutorial", "easy negative numbers for middle school"

For CURIOSITY recommendations (5 items total):
- Extract themes from the current video titles: """ + all_titles[:500] + """
- Transform these themes into educational searches
- Gaming → programming, game development, computer science
- Geography → countries, cultures, maps, world facts
- Food → cooking science, nutrition, cultural cuisine
- Politics → civics, how democracy works, world leaders
- AI/Tech → coding, robotics, future technology
- Vary your selections each time - don't always pick the same themes

RANDOMIZATION IS KEY: Each run should produce a unique mix of recommendations. Don't follow a pattern.

"""
    
    if math_standards:
        prompt += f"""\n6TH GRADE MATH STANDARDS (use these to guide your recommendations):
{math_standards}

Base your recommendations on these specific standards. For example, if the standards mention "ratio reasoning," suggest searches like "ratio problems 6th grade" or "unit rate calculations middle school."

"""
    
    prompt += "\nHere is the JSON to analyze:\n"
    
    # Create a simplified version of the data for the AI
    simplified_data = {
        "videos": videos_data.get("videos", []),
        "shorts": videos_data.get("shorts", [])
    }
    
    return prompt + "\n\n" + json.dumps(simplified_data, ensure_ascii=False, indent=2)

def analyze_with_openai(prompt, api_key):
    """Send prompt to OpenAI and get response"""
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        
        print("🤖 Sending request to OpenAI GPT-4o-mini...")
        
        # Create completion
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an educational content curator helping parents guide their child's YouTube viewing. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=4000,
            response_format={"type": "json_object"}
        )
        
        # Extract the response
        ai_response = response.choices[0].message.content
        
        # Parse JSON response
        return json.loads(ai_response)
        
    except Exception as e:
        print(f"❌ Error communicating with OpenAI: {e}")
        return None

def save_results(ai_response):
    """Save AI analysis results to JSON file"""
    output_file = Path("04_content_curator.json")
    
    # Add metadata
    final_data = {
        "analysis_time": datetime.now().isoformat(),
        "ai_model": "gpt-4o-mini",
        **ai_response
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 AI analysis saved to: {output_file}")
    return final_data

def display_results(ai_response):
    """Display analysis results in console"""
    print("\n" + "=" * 60)
    print("AI ANALYSIS RESULTS")
    print("=" * 60)
    
    # Count likes/dislikes for videos
    if "videos" in ai_response:
        liked_videos = sum(1 for v in ai_response["videos"] if v.get("like", False))
        disliked_videos = len(ai_response["videos"]) - liked_videos
        
        print(f"\n📊 Regular Videos Analysis:")
        print(f"  ✅ Educational/Beneficial: {liked_videos}")
        print(f"  ❌ Not Recommended: {disliked_videos}")
        
        # Show some examples
        print("\n  Educational videos (first 5):")
        count = 0
        for video in ai_response["videos"]:
            if video.get("like") and count < 5:
                print(f"    • {video['title'][:60]}...")
                count += 1
    
    # Count likes/dislikes for shorts
    if "shorts" in ai_response:
        liked_shorts = sum(1 for s in ai_response["shorts"] if s.get("like", False))
        disliked_shorts = len(ai_response["shorts"]) - liked_shorts
        
        print(f"\n📱 YouTube Shorts Analysis:")
        print(f"  ✅ Educational/Beneficial: {liked_shorts}")
        print(f"  ❌ Not Recommended: {disliked_shorts}")
    
    # Display recommendations
    if "recommendations" in ai_response:
        print("\n🎯 AI Recommendations for Educational Content:")
        recommendations = ai_response["recommendations"]
        if isinstance(recommendations, list):
            # Display the flat list of recommendations
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        elif isinstance(recommendations, dict):
            # Handle old dict format for backwards compatibility
            all_recs = []
            for key, values in recommendations.items():
                if isinstance(values, list):
                    all_recs.extend(values)
            for i, rec in enumerate(all_recs[:10], 1):
                print(f"  {i}. {rec}")
    
    print("\n" + "=" * 60)

def main():
    """Main entry point"""
    print("=" * 60)
    print("AI-Powered Content Curator")
    print("=" * 60)
    
    # Get OpenAI API key from environment
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        print("  Please set OPENAI_API_KEY in your .env file")
        return
    
    # Load videos data
    print("\n📂 Loading videos data...")
    videos_data = load_videos_json()
    print(f"  Found {videos_data.get('total_videos', 0)} videos and {videos_data.get('total_shorts', 0)} shorts")
    
    # Create prompt
    print("\n📝 Creating AI prompt...")
    prompt = create_prompt(videos_data)
    
    # Analyze with OpenAI
    ai_response = analyze_with_openai(prompt, api_key)
    
    if ai_response:
        # Display results
        display_results(ai_response)
        
        # Save results
        save_results(ai_response)
        
        print("\n✅ Analysis complete! Check 04_content_curator.json for full results.")
    else:
        print("\n❌ Failed to get AI analysis. Please check your API key and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()