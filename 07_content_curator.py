#!/usr/bin/env python3
"""
AI-Powered Search Results Curator - Analyzes reduced search results for educational value
Evaluates each video/short from reduced search results and marks them as appropriate or not
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

def load_search_results_json():
    """Load the reduced search results JSON file from previous script"""
    json_file = Path("06_search_recommendations_reduced.json")
    
    if not json_file.exists():
        print("❌ ERROR: File '06_search_recommendations_reduced.json' not found!")
        print("\nYou need to run the scripts in order:")
        print("1. Run: python 04_content_curator.py")
        print("2. Run: python 05_youtube_search_recommendations.py")
        print("3. Run: python 06_search_recommendations_reducer.py")
        print("4. Then run this script again")
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

def create_prompt(search_data):
    """Create the prompt for OpenAI"""
    
    # Load math standards
    math_standards = load_math_standards()
    
    prompt = """Your task is to review search results from educational YouTube searches and determine whether each video is truly educational and appropriate.

Context: An 11-year-old student (born 2013) in 6th grade in California will be watching these videos. The parents' goal is to ensure the child watches genuinely educational content that helps with learning.

IMPORTANT: This is an 11-year-old 6th grader, NOT a small child. They are capable of understanding sophisticated content.

The searches were based on AI-generated educational recommendations, so most content SHOULD be educational. However, you must verify each video individually.

Your objectives:
1. Verify videos are genuinely educational and age-appropriate
2. Ensure math content aligns with 6th grade standards
3. Filter out clickbait, low-quality, or entertainment-disguised-as-education content
4. Prioritize high-quality educational channels and content creators

For each video/short:
- Mark "like": true if it's genuinely educational and beneficial
- Mark "like": false if it's:
  - Clickbait or misleading
  - Too childish (meant for much younger kids)
  - Entertainment disguised as education
  - Low quality or incorrect information
  - Off-topic despite the search term

Quality indicators to look for:
- Reputable educational channels (Khan Academy, Math Antics, SciShow, TED-Ed, etc.)
- Clear educational value in the title
- Appropriate complexity for 6th grade
- Focused on actual learning, not just entertainment

Remember: Just because a video appeared in an educational search doesn't mean it's truly educational. Be selective and prioritize quality.

CRITICAL JSON STRUCTURE REQUIREMENT:
You MUST return the EXACT structure shown below. DO NOT wrap or nest the response.
DO NOT add any additional wrapper objects around the structure.
The root level MUST have "searches" as a direct array, NOT nested inside another object.

Your response MUST follow this EXACT structure:
{
  "searches": [
    {
      "search_term": "the search term here",
      "videos": [
        {
          "title": "video title",
          "url": "video url",
          "like": true or false
        }
      ],
      "shorts": [
        {
          "title": "short title",
          "url": "short url",
          "like": true or false
        }
      ]
    }
  ]
}

DO NOT return {"searches": {"searches": [...]}} - that is WRONG!
DO NOT add any wrapper - return EXACTLY the structure shown above!
Your response must start with {"searches": [ and NOT with {"searches": {"searches":

"""
    
    if math_standards:
        prompt += f"""\n6TH GRADE MATH STANDARDS (for evaluating math content):
{math_standards[:1000]}...

Ensure math videos align with these standards and are at the appropriate level.

"""
    
    prompt += "\nHere are the search results to analyze:\n\n"
    
    # Format the search data for analysis (already reduced by reducer script)
    formatted_data = {
        "searches": []
    }
    
    for search in search_data.get("searches", []):
        formatted_search = {
            "search_term": search["search_term"],
            "videos": search.get("videos", []),  # Already reduced to 3 videos
            "shorts": search.get("shorts", [])   # Already reduced to 3 shorts
        }
        formatted_data["searches"].append(formatted_search)
    
    return prompt + json.dumps(formatted_data, ensure_ascii=False, indent=2)

def analyze_with_openai(prompt, api_key):
    """Send prompt to OpenAI and get response"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Initialize OpenAI client
            client = OpenAI(api_key=api_key, timeout=60.0)  # Add 60 second timeout
            
            if retry_count == 0:
                print("🤖 Sending request to OpenAI GPT-4o-mini...")
                print("   This may take a while due to the large number of videos...")
            else:
                print(f"   Retry {retry_count}/{max_retries}...")
            
            # Create completion
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an educational content curator helping parents ensure their child watches quality educational content. Return ONLY valid JSON following the EXACT structure specified. DO NOT nest or wrap the response. The root must be {\"searches\": [...]} with NO additional wrapping."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=8000,  # Increased for larger response
                response_format={"type": "json_object"},
                timeout=60.0  # 60 second timeout for the API call
            )
            
            # Extract the response
            ai_response = response.choices[0].message.content
            
            # Parse JSON response
            parsed_response = json.loads(ai_response)
            
            # Validate the response structure
            if not isinstance(parsed_response, dict):
                raise ValueError("Response is not a dictionary")
            
            # Ensure we have the expected structure
            if "searches" not in parsed_response and "results" not in parsed_response:
                # Try to create proper structure if AI returned flat list
                if isinstance(parsed_response, list):
                    parsed_response = {"searches": parsed_response}
                else:
                    raise ValueError("Response missing 'searches' or 'results' key")
            
            return parsed_response
            
        except (openai.APITimeoutError, openai.APIConnectionError) as e:
            print(f"⚠️  Connection/timeout error: {e}")
            retry_count += 1
            if retry_count < max_retries:
                import time
                wait_time = retry_count * 5  # Progressive backoff: 5s, 10s, 15s
                print(f"   Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                print(f"❌ Failed after {max_retries} retries")
                return None
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON response: {e}")
            print(f"   Raw response: {ai_response[:500]}...")  # Show first 500 chars
            return None
        except Exception as e:
            print(f"❌ Error communicating with OpenAI: {e}")
            retry_count += 1
            if retry_count >= max_retries:
                return None

def save_results(ai_response, original_data):
    """Save AI analysis results to JSON file"""
    output_file = Path("07_content_curator.json")
    
    # Handle different response formats from AI
    searches_data = ai_response.get("searches") or ai_response.get("results", [])
    
    # Add metadata
    final_data = {
        "analysis_time": datetime.now().isoformat(),
        "ai_model": "gpt-4o-mini",
        "original_search_time": original_data.get("search_time"),
        "searches": searches_data
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 AI analysis saved to: {output_file}")
    return final_data

def display_results(ai_response):
    """Display analysis results in console"""
    print("\n" + "=" * 60)
    print("SEARCH RESULTS ANALYSIS")
    print("=" * 60)
    
    # Handle different response formats from AI
    searches_data = ai_response.get("searches") or ai_response.get("results", [])
    
    if not searches_data:
        print("⚠️  No search results in AI response")
        print(f"   Response keys: {list(ai_response.keys())}")
    
    total_videos_liked = 0
    total_videos_disliked = 0
    total_shorts_liked = 0
    total_shorts_disliked = 0
    
    for search in searches_data:
        # Handle case where search might be a string or malformed
        if isinstance(search, str):
            print(f"⚠️  Skipping malformed search entry: {search[:100]}...")
            continue
        
        if not isinstance(search, dict):
            print(f"⚠️  Skipping non-dict search entry: {type(search)}")
            continue
            
        search_term = search.get("search_term", "Unknown")
        videos = search.get("videos", [])
        shorts = search.get("shorts", [])
        
        # Count likes for this search
        videos_liked = sum(1 for v in videos if v.get("like", False))
        videos_total = len(videos)
        shorts_liked = sum(1 for s in shorts if s.get("like", False))
        shorts_total = len(shorts)
        
        print(f"\n📚 Search: \"{search_term}\"")
        print(f"   Videos: {videos_liked}/{videos_total} approved")
        print(f"   Shorts: {shorts_liked}/{shorts_total} approved")
        
        # Add to totals
        total_videos_liked += videos_liked
        total_videos_disliked += (videos_total - videos_liked)
        total_shorts_liked += shorts_liked
        total_shorts_disliked += (shorts_total - shorts_liked)
        
        # Show some approved videos
        if videos_liked > 0:
            print("   ✅ Approved videos (first 3):")
            count = 0
            for video in videos:
                if video.get("like") and count < 3:
                    title = video.get("title", "")[:60]
                    print(f"      • {title}...")
                    count += 1
    
    # Display overall summary
    print("\n" + "=" * 60)
    print("OVERALL STATISTICS")
    print("=" * 60)
    print(f"\n📊 Total Videos Analysis:")
    print(f"  ✅ Educational/Approved: {total_videos_liked}")
    print(f"  ❌ Not Recommended: {total_videos_disliked}")
    if total_videos_liked + total_videos_disliked > 0:
        print(f"  Approval Rate: {total_videos_liked/(total_videos_liked + total_videos_disliked)*100:.1f}%")
    
    print(f"\n📱 Total Shorts Analysis:")
    print(f"  ✅ Educational/Approved: {total_shorts_liked}")
    print(f"  ❌ Not Recommended: {total_shorts_disliked}")
    if total_shorts_liked + total_shorts_disliked > 0:
        print(f"  Approval Rate: {total_shorts_liked/(total_shorts_liked + total_shorts_disliked)*100:.1f}%")
    
    print("\n" + "=" * 60)

def main():
    """Main entry point"""
    print("=" * 60)
    print("AI-Powered Search Results Curator")
    print("=" * 60)
    
    # Get OpenAI API key from environment
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        print("  Please set OPENAI_API_KEY in your .env file")
        return
    
    # Load search results data
    print("\n📂 Loading search results data...")
    search_data = load_search_results_json()
    
    # Count total items
    total_searches = len(search_data.get("searches", []))
    total_videos = sum(len(s.get("videos", [])) for s in search_data.get("searches", []))
    total_shorts = sum(len(s.get("shorts", [])) for s in search_data.get("searches", []))
    
    print(f"  Found {total_searches} searches")
    print(f"  Total videos to analyze: {total_videos}")
    print(f"  Total shorts to analyze: {total_shorts}")
    
    # Create prompt
    print("\n📝 Creating AI prompt...")
    prompt = create_prompt(search_data)
    
    # Analyze with OpenAI
    ai_response = analyze_with_openai(prompt, api_key)
    
    if ai_response:
        # Display results
        display_results(ai_response)
        
        # Save results
        save_results(ai_response, search_data)
        
        print("\n✅ Analysis complete! Check 07_content_curator.json for full results.")
        print("   Videos marked with \"like\": true are approved for viewing.")
    else:
        print("\n❌ Failed to get AI analysis. Please check your API key and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()