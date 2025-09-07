#!/usr/bin/env python3
"""
YouTube Homepage Video Extractor - Extracts videos and shorts from YouTube homepage
Runs in headless mode using saved session
"""

import asyncio
import argparse
import json
from pathlib import Path
from patchright.async_api import async_playwright
from datetime import datetime
from shared_auth import check_browser_profile, check_youtube_auth, print_header, print_section


async def extract_youtube_videos(debug_mode=False):
    """Extract videos and shorts from YouTube homepage"""
    
    print_header("YouTube Homepage Video Extractor")
    if debug_mode:
        print("🔍 Running in DEBUG mode with visible browser...")
    else:
        print("Running in headless mode with saved session...")
    print("=" * 60)
    
    # Create screenshots directory if it doesn't exist
    screenshots_dir = Path("./screenshots")
    screenshots_dir.mkdir(exist_ok=True)
    
    # Check if profile exists
    check_browser_profile()
    
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
                "--disable-infobars"
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
            auth_result = await check_youtube_auth(page, "python 03_youtube_automation.py")
            
            # Take a screenshot to verify authentication
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = screenshots_dir / f"authenticated_{timestamp}.png"
            await page.screenshot(path=str(screenshot_path))
            print(f"📸 Screenshot saved: {screenshot_path}")
            
            # ============================================
            # EXTRACT VIDEOS AND SHORTS
            # ============================================
            
            print_section("EXTRACTING VIDEOS AND SHORTS")
            
            # Wait for content to load
            print("Waiting for content to load...")
            await page.wait_for_timeout(3000)
            
            # Scroll down to load more content
            print("Scrolling to load more content...")
            for _ in range(3):
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await page.wait_for_timeout(1000)
            
            # Extract regular videos
            print("\nExtracting regular videos...")
            videos = await page.evaluate("""
                () => {
                    const videoElements = document.querySelectorAll('a[href^="/watch?v="]');
                    const videos = [];
                    
                    videoElements.forEach(element => {
                        const titleElement = element.querySelector('span.yt-core-attributed-string');
                        const href = element.getAttribute('href');
                        
                        // Only take links that have a title span inside them
                        if (titleElement && href) {
                            videos.push({
                                title: titleElement.textContent.trim(),
                                url: 'https://www.youtube.com' + href,
                                type: 'video'
                            });
                        }
                    });
                    
                    return videos;
                }
            """)
            
            # Extract YouTube Shorts
            print("Extracting YouTube Shorts...")
            shorts = await page.evaluate("""
                () => {
                    const shortsElements = document.querySelectorAll('a.shortsLockupViewModelHostEndpoint');
                    const shorts = [];
                    
                    shortsElements.forEach(element => {
                        const titleElement = element.querySelector('span.yt-core-attributed-string');
                        const href = element.getAttribute('href');
                        
                        if (titleElement && href && href.startsWith('/shorts')) {
                            shorts.push({
                                title: titleElement.textContent.trim(),
                                url: 'https://www.youtube.com' + href,
                                type: 'short'
                            });
                        }
                    });
                    
                    return shorts;
                }
            """)
            
            # Combine all results
            all_content = {
                'extraction_time': datetime.now().isoformat(),
                'videos': videos,
                'shorts': shorts,
                'total_videos': len(videos),
                'total_shorts': len(shorts),
                'total_content': len(videos) + len(shorts)
            }
            
            # Print results to console
            print(f"\n📊 Found {len(videos)} regular videos:")
            for i, video in enumerate(videos[:10], 1):  # Show first 10
                print(f"  {i}. {video['title'][:80]}...")
                print(f"     URL: {video['url']}")
            if len(videos) > 10:
                print(f"  ... and {len(videos) - 10} more videos")
            
            print(f"\n📱 Found {len(shorts)} YouTube Shorts:")
            for i, short in enumerate(shorts[:10], 1):  # Show first 10
                print(f"  {i}. {short['title'][:80]}...")
                print(f"     URL: {short['url']}")
            if len(shorts) > 10:
                print(f"  ... and {len(shorts) - 10} more shorts")
            
            # Save to JSON file
            output_file = Path("03_youtube_get_index_page_videos.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_content, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 Data saved to: {output_file}")
            print(f"   Total items extracted: {all_content['total_content']}")
            
            print("\n" + "=" * 60)
            print("Extraction complete!")
            print("=" * 60)
            
            # In debug mode, wait for user input before closing
            if debug_mode:
                print("\n🔍 DEBUG MODE: Browser will remain open")
                input("Press Enter to close the browser and exit...")
                
        except Exception as e:
            print(f"\n❌ Error during automation: {e}")
            if debug_mode:
                input("\nPress Enter to close the browser and exit...")
            
        finally:
            await context.close()


def main():
    """Main entry point"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='YouTube homepage video extractor')
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Run in debug mode with visible browser and manual exit'
    )
    args = parser.parse_args()
    
    print("Starting YouTube video extraction...")
    asyncio.run(extract_youtube_videos(debug_mode=args.debug))


if __name__ == "__main__":
    main()