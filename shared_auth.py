#!/usr/bin/env python3
"""
Shared authentication utilities for YouTube automation scripts
"""

import sys
from pathlib import Path


def check_browser_profile():
    """
    Check if browser profile exists and provide instructions if not.
    Exits the program if profile is not found.
    """
    profile_dir = Path("./chrome_profile")
    
    if not profile_dir.exists():
        print("\n❌ ERROR: No saved browser profile found!")
        print("\nYou need to sign in first:")
        print("1. Run: python 01_youtube_sign_in.py")
        print("2. Complete the sign-in process")
        print("3. Then run this script again")
        print("=" * 60)
        sys.exit(1)
    
    return profile_dir


async def check_youtube_auth(page, script_name="this script"):
    """
    Check if user is authenticated on YouTube.
    
    Args:
        page: Playwright page object
        script_name: Name of the calling script for error messages
        
    Returns:
        dict: Channel information if authenticated, None otherwise
    """
    print("\nChecking authentication status...")
    
    try:
        # Look for avatar button that indicates user is signed in
        avatar_btn = await page.wait_for_selector('#avatar-btn', timeout=5000)
        
        if avatar_btn:
            print("✅ Successfully authenticated!")
            
            # Get current channel info
            channel_info = await page.evaluate("""
                () => {
                    const channelName = document.querySelector('yt-formatted-string#channel-name')?.textContent;
                    const channelHandle = document.querySelector('#channel-handle')?.textContent;
                    return { name: channelName, handle: channelHandle };
                }
            """)
            
            if channel_info and (channel_info['name'] or channel_info['handle']):
                print(f"Current channel: {channel_info.get('name', 'Unknown')} ({channel_info.get('handle', '')})")
            
            return {
                'authenticated': True,
                'avatar_btn': avatar_btn,
                'channel_info': channel_info
            }
            
    except:
        # Not signed in
        print("\n❌ ERROR: Not signed in to YouTube!")
        
        # Check if sign-in button exists
        try:
            sign_in_btn = await page.wait_for_selector('a[aria-label*="Sign in"]', timeout=3000)
            if sign_in_btn:
                print("\n📝 Sign-in button detected.")
        except:
            print("\nCould not determine authentication status.")
        
        print(f"\nYou need to authenticate first:")
        print("1. Run: python 01_youtube_sign_in.py")
        print("2. Complete the sign-in process")
        print(f"3. Then run {script_name} again")
        print("=" * 60)
        sys.exit(1)


def print_header(title):
    """Print a formatted header for scripts"""
    print("=" * 60)
    print(title)
    print("=" * 60)


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)