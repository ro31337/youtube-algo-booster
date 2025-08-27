#!/usr/bin/env python3
"""
YouTube Channel Switcher - Run this to switch between YouTube channels
Runs in headless mode by default, uses persistent profile
"""

import asyncio
from patchright.async_api import async_playwright
from shared_auth import check_browser_profile, check_youtube_auth, print_header, print_section


async def switch_youtube_channel():
    """Switch between YouTube channels on the same Google account"""
    
    print_header("YouTube Channel Switcher")
    print("This script helps you switch between YouTube channels")
    print("Requirement: You must be signed in first (run 01_youtube_sign_in.py)")
    print("=" * 60)
    
    # Check if profile exists
    check_browser_profile()
    
    async with async_playwright() as p:
        print("\nLaunching headless browser with saved profile...")
        
        # Use persistent context in headless mode
        context = await p.chromium.launch_persistent_context(
            user_data_dir="./chrome_profile",  # Persistent profile
            headless=True,  # Run in headless mode (no visible window)
            no_viewport=True,  # Use native screen resolution
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
            auth_result = await check_youtube_auth(page, "python 02_youtube_optional_switch_channel.py")
            avatar_btn = auth_result['avatar_btn']
            
            # Click on avatar to open account menu
            print("\nClicking on avatar button...")
            await avatar_btn.click()
            await page.wait_for_timeout(2000)
            
            # Look for Switch Account option
            print("Looking for Switch Account option...")
            switch_account_selectors = [
                'yt-formatted-string:has-text("Switch account")',
                'a:has-text("Switch account")',
                'tp-yt-paper-item:has-text("Switch account")',
                '#label:has-text("Switch account")'
            ]
            
            switch_btn = None
            for selector in switch_account_selectors:
                try:
                    switch_btn = await page.wait_for_selector(selector, timeout=2000)
                    if switch_btn:
                        print(f"Found Switch Account option")
                        await switch_btn.click()
                        print("Opening channel selection...")
                        await page.wait_for_timeout(2000)
                        break
                except:
                    continue
            
            if switch_btn:
                # Extract all channel accounts
                print_section("AVAILABLE CHANNELS")
                
                # Get all channel items
                channels = await page.evaluate("""
                    () => {
                        const items = document.querySelectorAll('ytd-account-item-renderer');
                        return Array.from(items).map((item, index) => {
                            const titleEl = item.querySelector('#channel-title');
                            const handleEl = item.querySelector('yt-formatted-string[secondary]');
                            const subsEl = item.querySelectorAll('yt-formatted-string[secondary]')[1];
                            const isSelected = !item.querySelector('#selected')?.hasAttribute('hidden');
                            
                            return {
                                index: index + 1,
                                title: titleEl?.textContent?.trim() || 'Unknown',
                                handle: handleEl?.textContent?.trim() || '',
                                subscribers: subsEl?.textContent?.trim() || 'No subscribers',
                                selected: isSelected
                            };
                        });
                    }
                """)
                
                if channels:
                    print(f"\nFound {len(channels)} channel(s):\n")
                    for ch in channels:
                        selected_mark = " ✓ (Currently selected)" if ch.get('selected') else ""
                        print(f"  {ch['index']}. {ch['title']}")
                        print(f"     {ch['handle']}")
                        print(f"     {ch['subscribers']}{selected_mark}")
                        print()
                    
                    print("-" * 60)
                    
                    if len(channels) > 1:
                        try:
                            choice = input(f"\nSelect channel (1-{len(channels)}) or press Enter to cancel: ").strip()
                            if choice and choice.isdigit():
                                channel_index = int(choice) - 1
                                if 0 <= channel_index < len(channels):
                                    selected_channel = channels[channel_index]
                                    print(f"\n🔄 Switching to: {selected_channel['title']}")
                                    
                                    # Click on the selected channel
                                    channel_elements = await page.query_selector_all('ytd-account-item-renderer')
                                    if channel_index < len(channel_elements):
                                        await channel_elements[channel_index].click()
                                        print("Switching channel...")
                                        await page.wait_for_timeout(3000)
                                        
                                        print(f"\n✅ Successfully switched to {selected_channel['title']}!")
                                        print("\nThe channel selection has been saved.")
                                        print("You can now run: python 03_youtube_automation.py")
                                        print("\nWaiting for channel switch to complete...")
                                        await page.wait_for_timeout(2000)
                                else:
                                    print("\n❌ Invalid selection. No changes made.")
                            else:
                                print("\n❌ Cancelled. No changes made.")
                        except Exception as e:
                            print(f"\nError during channel selection: {e}")
                    else:
                        print("\nℹ️ Only one channel available. No switch needed.")
                else:
                    print("❌ No channels found in the account menu.")
            else:
                print("\n❌ Could not find Switch Account option.")
                print("This may happen if you only have one channel.")
            
            print("\n" + "=" * 60)
            print("Channel switcher complete.")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("\n" + "=" * 60)
            
        finally:
            await context.close()


def main():
    """Main entry point"""
    print("Starting YouTube Channel Switcher...")
    asyncio.run(switch_youtube_channel())


if __name__ == "__main__":
    main()