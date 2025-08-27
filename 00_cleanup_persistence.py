#!/usr/bin/env python3
"""
Cleanup Script - Removes saved browser profile and sessions
Run this when you want to start fresh or switch accounts
"""

import os
import shutil
from pathlib import Path


def cleanup_persistence():
    """Remove all saved browser data and sessions"""
    
    print("=" * 60)
    print("Browser Profile Cleanup Script")
    print("=" * 60)
    print("This will remove:")
    print("• Saved login sessions")
    print("• Browser cookies")
    print("• Cached data")
    print("• All persistent browser profile data")
    print("=" * 60)
    
    # Profile directory path
    profile_dir = Path("./chrome_profile")
    screenshots_dir = Path("./screenshots")
    
    # Check if profile exists
    if profile_dir.exists():
        print(f"\n📁 Found browser profile at: {profile_dir.absolute()}")
        
        # Get directory size
        total_size = sum(f.stat().st_size for f in profile_dir.rglob('*') if f.is_file())
        size_mb = total_size / (1024 * 1024)
        print(f"   Size: {size_mb:.2f} MB")
        
        # Confirm deletion
        confirm = input("\n⚠️  Are you sure you want to delete all saved data? (yes/no): ").strip().lower()
        
        if confirm in ['yes', 'y']:
            try:
                print("\nRemoving browser profile...")
                shutil.rmtree(profile_dir)
                print("✅ Browser profile removed successfully!")
                
                # Also clean screenshots if they exist
                if screenshots_dir.exists():
                    print("\nCleaning up screenshots...")
                    for file in screenshots_dir.glob("*.png"):
                        file.unlink()
                    print("✅ Screenshots cleaned!")
                
                print("\n" + "=" * 60)
                print("Cleanup complete!")
                print("\nNext steps:")
                print("1. Run: python 01_youtube_sign_in.py")
                print("2. Sign in to your Google account")
                print("3. Select your YouTube channel")
                print("=" * 60)
                
            except Exception as e:
                print(f"\n❌ Error during cleanup: {e}")
                print("You may need to close any running browsers first.")
        else:
            print("\n❌ Cleanup cancelled.")
    else:
        print("\n📁 No browser profile found at:", profile_dir.absolute())
        print("Nothing to clean up!")
        
        # Check for screenshots
        if screenshots_dir.exists() and list(screenshots_dir.glob("*.png")):
            clean_screenshots = input("\nClean up screenshots? (yes/no): ").strip().lower()
            if clean_screenshots in ['yes', 'y']:
                for file in screenshots_dir.glob("*.png"):
                    file.unlink()
                print("✅ Screenshots cleaned!")
    
    print("\nDone!")


def main():
    """Main entry point"""
    cleanup_persistence()


if __name__ == "__main__":
    main()