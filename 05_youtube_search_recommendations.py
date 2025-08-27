#!/usr/bin/env python3
"""
YouTube Search Recommendations - Searches YouTube for educational content recommendations
Uses recommendations from AI content curator to find appropriate videos
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path
from patchright.async_api import async_playwright
from datetime import datetime
from shared_auth import check_browser_profile, check_youtube_auth, print_header, print_section


def load_recommendations():
    """Load recommendations from content curator JSON file"""
    json_file = Path("04_content_curator.json")
    
    if not json_file.exists():
        print("❌ ERROR: File '04_content_curator.json' not found!")
        print("\nYou need to run the content curator first:")
        print("1. Run: python 03_youtube_get_index_page_videos.py")
        print("2. Run: python 04_content_curator.py")
        print("3. Then run this script again")
        sys.exit(1)
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if 'recommendations' not in data:
        print("❌ ERROR: No recommendations found in content curator JSON!")
        print("Please run 04_content_curator.py to generate recommendations.")
        sys.exit(1)
    
    recommendations = data['recommendations']
    
    # Handle both flat list and dict formats
    if isinstance(recommendations, dict):
        # Convert dict format to flat list
        flat_list = []
        for key, values in recommendations.items():
            if isinstance(values, list):
                flat_list.extend(values)
        return flat_list
    
    return recommendations


async def search_youtube_recommendations(debug_mode=False):
    """Search YouTube for educational content based on AI recommendations"""
    
    print_header("YouTube Search Recommendations")
    if debug_mode:
        print("🔍 Running in DEBUG mode with visible browser...")
    else:
        print("Running in headless mode with saved session...")
    print("=" * 60)
    
    # Load recommendations
    print("\n📂 Loading recommendations from content curator...")
    recommendations = load_recommendations()
    print(f"  Found {len(recommendations)} recommendations to search for:")
    for i, rec in enumerate(recommendations, 1):
        print(f"    {i}. {rec}")
    
    # Create screenshots directory if it doesn't exist
    screenshots_dir = Path("./screenshots")
    screenshots_dir.mkdir(exist_ok=True)
    
    # Check if profile exists
    check_browser_profile()
    
    # Initialize results storage
    all_results = {
        "search_time": datetime.now().isoformat(),
        "searches": []
    }
    
    async with async_playwright() as p:
        if debug_mode:
            print("\nLaunching visible browser for debugging...")
        else:
            print("\nLaunching headless browser with saved profile...")
        
        # Launch with persistent context
        context = await p.chromium.launch_persistent_context(
            user_data_dir="./chrome_profile",  # Use saved profile
            headless=not debug_mode,  # Visible in debug mode, headless otherwise
            no_viewport=False,  # Use specific viewport for consistent rendering
            viewport={'width': 1920, 'height': 1080},  # Full HD resolution
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-infobars",
                "--start-maximized"
            ]
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        try:
            # Remove webdriver property
            await page.evaluate("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            
            # Navigate to YouTube
            print("Navigating to YouTube...")
            await page.goto("https://www.youtube.com", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)
            
            # Check authentication using shared function
            auth_result = await check_youtube_auth(page, "python 05_youtube_search_recommendations.py")
            
            print_section("SEARCHING RECOMMENDATIONS")
            
            # Search each recommendation
            for idx, search_term in enumerate(recommendations, 1):
                print(f"\n🔍 Searching {idx}/{len(recommendations)}: {search_term}")
                
                search_result = {
                    "search_term": search_term,
                    "videos": [],
                    "shorts": []
                }
                
                try:
                    # Wait for search input to be available
                    search_input = await page.wait_for_selector('input[name="search_query"]', timeout=5000)
                    
                    # Clear and type search term
                    await search_input.click()
                    await search_input.fill("")
                    await search_input.type(search_term, delay=50)
                    
                    # Click search button
                    search_button = await page.wait_for_selector('button[aria-label="Search"]', timeout=5000)
                    await search_button.click()
                    
                    # Wait for search results to load
                    await page.wait_for_timeout(3000)
                    
                    # Extract regular videos
                    videos = await page.evaluate("""
                        () => {
                            const videos = [];
                            // Select all video titles from search results
                            const videoElements = document.querySelectorAll('a#video-title');
                            
                            videoElements.forEach(element => {
                                // Check if parent container has "Sponsored" text
                                const container = element.closest('ytd-video-renderer') || element.closest('ytd-rich-item-renderer');
                                const hasSponsored = container && (
                                    container.textContent.includes('Sponsored') ||
                                    container.querySelector('.badge-shape-wiz__text')?.textContent === 'Sponsored'
                                );
                                
                                if (!hasSponsored && element.href && element.textContent) {
                                    videos.push({
                                        title: element.textContent.trim(),
                                        url: element.href
                                    });
                                }
                            });
                            return videos;
                        }
                    """)
                    
                    # Extract YouTube Shorts
                    shorts = await page.evaluate("""
                        () => {
                            const shorts = [];
                            // Select all shorts from search results
                            const shortElements = document.querySelectorAll('a.shortsLockupViewModelHostEndpoint');
                            
                            shortElements.forEach(element => {
                                if (element.href && element.textContent) {
                                    shorts.push({
                                        title: element.textContent.trim(),
                                        url: element.href
                                    });
                                }
                            });
                            return shorts;
                        }
                    """)
                    
                    search_result["videos"] = videos
                    search_result["shorts"] = shorts
                    
                    print(f"  ✅ Found {len(videos)} videos and {len(shorts)} shorts")
                    
                    # Take screenshot of search results
                    if debug_mode:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        screenshot_path = screenshots_dir / f"search_{idx}_{timestamp}.png"
                        await page.screenshot(path=str(screenshot_path))
                        print(f"  📸 Screenshot saved: {screenshot_path}")
                    
                except Exception as e:
                    print(f"  ❌ Error searching for '{search_term}': {e}")
                    search_result["error"] = str(e)
                
                all_results["searches"].append(search_result)
                
                # Small delay between searches to avoid rate limiting
                if idx < len(recommendations):
                    await page.wait_for_timeout(1500)
            
            # Save results to JSON
            output_file = Path("05_youtube_search_recommendations.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, ensure_ascii=False, indent=2)
            
            # Display summary
            print_section("SEARCH RESULTS SUMMARY")
            total_videos = sum(len(s["videos"]) for s in all_results["searches"])
            total_shorts = sum(len(s["shorts"]) for s in all_results["searches"])
            successful_searches = sum(1 for s in all_results["searches"] if "error" not in s)
            
            print(f"📊 Search Statistics:")
            print(f"  Successful searches: {successful_searches}/{len(recommendations)}")
            print(f"  Total videos found: {total_videos}")
            print(f"  Total shorts found: {total_shorts}")
            print(f"\n💾 Results saved to: {output_file}")
            
            # In debug mode, wait for user input before closing
            if debug_mode:
                print("\n🔍 DEBUG MODE: Browser will remain open")
                input("Press Enter to close the browser and exit...")
                
            print("\n" + "=" * 60)
            print("Search complete!")
            print("=" * 60)
                
        except Exception as e:
            print(f"\n❌ Error during search: {e}")
            if debug_mode:
                input("\nPress Enter to close the browser and exit...")
            
        finally:
            await context.close()


def main():
    """Main entry point"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='YouTube search recommendations script')
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Run in debug mode with visible browser and manual exit'
    )
    args = parser.parse_args()
    
    print("Starting YouTube search recommendations...")
    asyncio.run(search_youtube_recommendations(debug_mode=args.debug))


if __name__ == "__main__":
    main()