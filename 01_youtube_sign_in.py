#!/usr/bin/env python3
"""
YouTube Sign-In Script - Run this first to authenticate with YouTube
Always runs with visible browser and persistent profile
"""

import asyncio
import os
import random
from pathlib import Path
from patchright.async_api import async_playwright
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def human_like_mouse_movement(page):
    """Simulate human-like mouse movements"""
    x = random.randint(100, 500)
    y = random.randint(100, 400)
    
    for _ in range(random.randint(2, 4)):
        new_x = x + random.randint(-200, 200)
        new_y = y + random.randint(-150, 150)
        new_x = max(50, min(new_x, 800))
        new_y = max(50, min(new_y, 600))
        
        steps = random.randint(10, 20)
        await page.mouse.move(new_x, new_y, steps=steps)
        await page.wait_for_timeout(random.randint(100, 500))
        
        x, y = new_x, new_y


async def sign_in_youtube():
    """Sign into YouTube with persistent profile - run this once to authenticate"""
    
    # Get credentials from environment variables
    email = os.getenv('GOOGLE_EMAIL', 'the.poop.professor@gmail.com')
    password = os.getenv('GOOGLE_PASSWORD', '')
    
    # Create screenshots directory
    screenshots_dir = Path("screenshots")
    screenshots_dir.mkdir(exist_ok=True)
    
    # Clean up old screenshots
    for file in screenshots_dir.glob("*.png"):
        file.unlink()
    
    print("=" * 60)
    print("YouTube Sign-In Script")
    print("=" * 60)
    print("This script will:")
    print("1. Open a visible browser window")
    print("2. Navigate to YouTube")
    print("3. Help you sign in to your Google account")
    print("4. Save your session for future automation")
    print("=" * 60)
    print(f"Email configured: {email if email else 'Not set'}")
    print(f"Password configured: {'Yes' if password else 'No'}")
    print("=" * 60)
    
    async with async_playwright() as p:
        # ALWAYS use persistent context with visible browser
        print("\nLaunching browser with persistent profile...")
        context = await p.chromium.launch_persistent_context(
            user_data_dir="./chrome_profile",  # Persistent profile
            headless=False,  # ALWAYS visible for sign-in
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
            
            # Check if already signed in
            print("\nChecking if already signed in...")
            try:
                avatar_btn = await page.wait_for_selector('#avatar-btn', timeout=3000)
                if avatar_btn:
                    print("\n✅ Already signed into YouTube!")
                    
                    # Click avatar to show account info
                    await avatar_btn.click()
                    await page.wait_for_timeout(2000)
                    
                    # Look for Switch Account
                    print("\nLooking for account switcher...")
                    switch_btn = await page.wait_for_selector(
                        'yt-formatted-string:has-text("Switch account")',
                        timeout=2000
                    )
                    
                    if switch_btn:
                        await switch_btn.click()
                        await page.wait_for_timeout(2000)
                        
                        # Extract channels
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
                            print(f"\nFound {len(channels)} channel(s):")
                            print("-" * 50)
                            for ch in channels:
                                selected_mark = " ✓ (Currently selected)" if ch.get('selected') else ""
                                print(f"{ch['index']}. {ch['title']} ({ch['handle']}) - {ch['subscribers']}{selected_mark}")
                            print("-" * 50)
                            
                            if len(channels) > 1:
                                try:
                                    choice = input(f"\nSelect channel (1-{len(channels)}) or press Enter to keep current: ").strip()
                                    if choice and choice.isdigit():
                                        channel_index = int(choice) - 1
                                        if 0 <= channel_index < len(channels):
                                            selected_channel = channels[channel_index]
                                            print(f"\nSwitching to: {selected_channel['title']}")
                                            
                                            channel_elements = await page.query_selector_all('ytd-account-item-renderer')
                                            if channel_index < len(channel_elements):
                                                await channel_elements[channel_index].click()
                                                await page.wait_for_timeout(2000)
                                                print(f"✅ Switched to {selected_channel['title']}")
                                except Exception as e:
                                    print(f"Error during channel selection: {e}")
                    
                    print("\nYou're all set! Session saved.")
                    print("You can now run: python 02_youtube_automation.py")
                    
            except:
                # Not signed in, proceed with sign-in flow
                print("Not signed in. Starting sign-in process...")
                
                # Simulate human behavior
                await human_like_mouse_movement(page)
                await page.wait_for_timeout(2000)
                
                # Look for Sign In button
                print("\nLooking for Sign In button...")
                sign_in_button = await page.wait_for_selector('a[aria-label*="Sign in"]', timeout=5000)
                
                if sign_in_button:
                    await sign_in_button.hover()
                    await page.wait_for_timeout(500)
                    await sign_in_button.click()
                    print("Clicked Sign In button")
                    await page.wait_for_timeout(3000)
                    
                    # Check if on Google sign-in page
                    if "accounts.google.com" in page.url:
                        print("\n📝 Google Sign-In Page")
                        
                        # Try to enter email if available
                        if email:
                            print(f"Entering email: {email}")
                            email_input = await page.wait_for_selector('input[type="email"]', timeout=5000)
                            if email_input:
                                await email_input.click()
                                await page.wait_for_timeout(500)
                                
                                for char in email:
                                    await page.keyboard.type(char)
                                    await page.wait_for_timeout(random.randint(50, 150))
                                
                                # Click Next
                                next_button = await page.wait_for_selector('button span:has-text("Next")', timeout=3000)
                                if next_button:
                                    await next_button.click()
                                    await page.wait_for_timeout(3000)
                                    
                                    # Enter password if available
                                    if password:
                                        print("Entering password...")
                                        password_input = await page.wait_for_selector('input[type="password"]', timeout=3000)
                                        if password_input:
                                            await password_input.click()
                                            await page.wait_for_timeout(500)
                                            
                                            for char in password:
                                                await page.keyboard.type(char)
                                                await page.wait_for_timeout(random.randint(50, 150))
                                            
                                            # Click Next/Sign In
                                            next_button = await page.wait_for_selector(
                                                'button span:has-text("Next"), button:has-text("Sign in")',
                                                timeout=3000
                                            )
                                            if next_button:
                                                await next_button.click()
                                                print("Attempting sign in...")
                                                await page.wait_for_timeout(5000)
                        
                        print("\n⚠️  If you see 'Browser or app may not be secure' error:")
                        print("   Complete the login manually in the browser window")
                        print("\n✅ Once signed in, your session will be saved automatically")
                
                else:
                    print("Sign In button not found")
            
            print("\n" + "=" * 60)
            input("Press Enter to close the browser...")
            print("Closing browser...")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("\n" + "=" * 60)
            input("Error occurred. Press Enter to close the browser...")
            
        finally:
            await context.close()


def main():
    print("Starting YouTube Sign-In process...")
    asyncio.run(sign_in_youtube())


if __name__ == "__main__":
    main()