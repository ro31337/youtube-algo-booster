#!/usr/bin/env python3
"""
YouTube Take Action - Performs like/dislike actions on videos from the action list
Navigates to each video and performs the specified action
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path
from patchright.async_api import async_playwright
from datetime import datetime
from shared_auth import check_browser_profile, check_youtube_auth, print_header, print_section

def load_action_list():
    """Load the action list from the previous script"""
    json_file = Path("08_youtube_action_list.json")
    
    if not json_file.exists():
        print("❌ ERROR: File '08_youtube_action_list.json' not found!")
        print("\nYou need to run the action list generator first:")
        print("1. Run: python 08_youtube_action_list.py")
        print("2. Then run this script again")
        sys.exit(1)
    
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

async def perform_youtube_actions(debug_mode=False):
    """Navigate to YouTube videos and perform like/dislike actions"""
    
    print_header("YouTube Take Action")
    if debug_mode:
        print("🔍 Running in DEBUG mode with visible browser...")
    else:
        print("Running in headless mode with saved session...")
    print("=" * 60)
    
    # Load action list
    print("\n📂 Loading action list...")
    action_data = load_action_list()
    
    summary = action_data.get("summary", {})
    actions = action_data.get("actions", [])
    
    # Sort actions: likes first, then dislikes
    # This helps avoid YouTube thinking we're just mass-disliking
    actions_sorted = sorted(actions, key=lambda x: (x.get("action") != "like", x.get("type")))
    
    print(f"  Total actions to perform: {len(actions_sorted)}")
    print(f"  Videos to like: {summary.get('videos_to_like', 0)}")
    print(f"  Shorts to like: {summary.get('shorts_to_like', 0)}")
    print(f"  Videos to dislike: {summary.get('videos_to_dislike', 0)}")
    print(f"  Shorts to dislike: {summary.get('shorts_to_dislike', 0)}")
    print("\n📌 Strategy: Performing likes first, then dislikes...")
    
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
            
            # Navigate to YouTube with retries
            print("Navigating to YouTube...")
            max_retries = 3
            for retry in range(max_retries):
                try:
                    await page.goto("https://www.youtube.com", wait_until="domcontentloaded", timeout=30000)
                    await page.wait_for_timeout(2000)
                    break
                except Exception as e:
                    if retry < max_retries - 1:
                        print(f"  ⚠️ Navigation timeout, retrying ({retry + 1}/{max_retries})...")
                        await page.wait_for_timeout(3000)
                    else:
                        raise e
            
            # Check authentication using shared function
            auth_result = await check_youtube_auth(page, "python 09_youtube_take_action.py")
            
            print_section("PERFORMING ACTIONS")
            
            # Track progress
            completed_actions = 0
            failed_actions = 0
            
            # Process each action (now sorted with likes first)
            for idx, action_item in enumerate(actions_sorted, 1):
                url = action_item.get("url")
                video_type = action_item.get("type")
                action = action_item.get("action")
                
                print(f"\n📹 Action {idx}/{len(actions)}:")
                print(f"   Type: {video_type}")
                print(f"   Action: {action}")
                print(f"   URL: {url[:60]}...")
                
                try:
                    # Navigate to the video with retries
                    print(f"   Navigating to {video_type}...")
                    nav_success = False
                    for nav_retry in range(2):
                        try:
                            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                            await page.wait_for_timeout(2000)  # Wait for page to fully load
                            nav_success = True
                            break
                        except Exception as nav_e:
                            if nav_retry == 0:
                                print(f"   ⚠️ Navigation timeout, retrying...")
                                await page.wait_for_timeout(2000)
                            else:
                                raise nav_e
                    
                    if not nav_success:
                        raise Exception("Failed to navigate after retries")
                    
                    # ============================================
                    # PERFORM LIKE/DISLIKE ACTION
                    # ============================================
                    
                    # Different selectors for videos vs shorts
                    if video_type == "video":
                        if action == "like":
                            # Video like button selector
                            button_selector = 'like-button-view-model button[aria-label*="like this video"]'
                        else:  # dislike
                            # Video dislike button selector
                            button_selector = 'dislike-button-view-model button[aria-label*="Dislike"]'
                    else:  # short
                        if action == "like":
                            # Short like button selector - use the button with like icon
                            button_selector = 'button[aria-label*="like this video"]'
                        else:  # dislike
                            # Short dislike button selector
                            button_selector = 'button[aria-label="Dislike this video"]'
                    
                    print(f"   Performing {action}...")
                    
                    # Try multiple times to find and click the button
                    action_success = False
                    for attempt in range(3):
                        try:
                            # Wait for the button to be available
                            button = await page.wait_for_selector(button_selector, timeout=5000)
                            
                            # Scroll button into view
                            await button.scroll_into_view_if_needed()
                            await page.wait_for_timeout(500)
                            
                            # Check if already pressed (aria-pressed="true")
                            is_pressed = await button.get_attribute("aria-pressed")
                            
                            if is_pressed == "true":
                                print(f"   ✓ Already {action}d")
                                action_success = True
                                break
                            else:
                                # Click the button with force option
                                await button.click(force=True)
                                print(f"   ✅ {action.capitalize()} action performed")
                                action_success = True
                                break
                            
                        except Exception as btn_e:
                            if attempt < 2:
                                print(f"   ⚠️ Button not ready, retrying ({attempt + 1}/3)...")
                                await page.wait_for_timeout(2000)
                                # Try scrolling down a bit in case button is below fold
                                await page.evaluate("window.scrollBy(0, 200)")
                            else:
                                print(f"   ⚠️ Could not find or click {action} button after 3 attempts")
                    
                    # Wait after action
                    if action_success:
                        await page.wait_for_timeout(1000)
                        
                        # Take screenshot after action
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        screenshot_path = screenshots_dir / f"action_{idx}_{action}_{timestamp}.png"
                        await page.screenshot(path=str(screenshot_path))
                        print(f"   📸 Screenshot saved: {screenshot_path}")
                    
                    completed_actions += 1
                    
                    # In debug mode, only do the first action then wait
                    if debug_mode and idx == 1:
                        print("\n" + "=" * 60)
                        print("DEBUG MODE: Stopped after first video")
                        print("=" * 60)
                        print("\n🔍 Browser is now on the first video/short")
                        print("   Inspect the page to find like/dislike button selectors")
                        print("   The page will remain open for inspection")
                        input("\nPress Enter to close the browser and exit...")
                        break
                    
                except Exception as e:
                    print(f"   ❌ Error performing action: {e}")
                    failed_actions += 1
                    
                # Variable delay between actions to avoid rate limiting
                if idx < len(actions_sorted) and not debug_mode:
                    # Longer delay every 5 actions
                    if idx % 5 == 0:
                        print("   ⏳ Taking a longer break to avoid rate limiting...")
                        await page.wait_for_timeout(5000)
                    else:
                        await page.wait_for_timeout(2000)
            
            # Display summary (only in non-debug mode)
            if not debug_mode:
                print_section("ACTION SUMMARY")
                print(f"📊 Results:")
                print(f"  Completed actions: {completed_actions}")
                print(f"  Failed actions: {failed_actions}")
                print(f"  Total processed: {completed_actions + failed_actions}/{len(actions_sorted)}")
                
                if failed_actions > 0:
                    print(f"\n⚠️ Some actions failed. This is normal - videos may be removed or unavailable.")
                    print(f"   Consider running the script again later for failed items.")
                
                print("\n" + "=" * 60)
                print("Actions complete!")
                print("=" * 60)
                
        except Exception as e:
            print(f"\n❌ Error during action execution: {e}")
            if debug_mode:
                input("\nPress Enter to close the browser and exit...")
            
        finally:
            if not debug_mode:
                await context.close()

def main():
    """Main entry point"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='YouTube action execution script')
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Run in debug mode with visible browser and stop after first video'
    )
    args = parser.parse_args()
    
    print("Starting YouTube action execution...")
    asyncio.run(perform_youtube_actions(debug_mode=args.debug))

if __name__ == "__main__":
    main()