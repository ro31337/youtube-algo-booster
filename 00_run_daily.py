#!/usr/bin/env python3
"""
Daily automation runner with retry logic for YouTube Algorithm Booster pipeline.

This script replaces the bash script run-daily.sh with proper error handling,
retry logic, and detailed status reporting for each step of the pipeline.
"""

import subprocess
import sys
import time
from datetime import datetime
from typing import List, Optional, Tuple


class DailyPipelineRunner:
    """
    Manages the execution of the YouTube automation pipeline with retry logic.
    
    Each command in the pipeline is executed sequentially with up to 10 retries
    per command. The script provides detailed logging of each retry attempt.
    """
    
    def __init__(self, max_retries: int = 10, initial_delay: int = 5):
        """
        Initialize the pipeline runner.
        
        Args:
            max_retries: Maximum number of retry attempts per command
            initial_delay: Initial delay in seconds between retries
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.python_executable = "./venv/bin/python"
        
        # Define the pipeline steps in order
        self.pipeline_steps = [
            ("03_youtube_get_index_page_videos.py", "Extract YouTube homepage videos"),
            ("04_content_curator.py", "Curate homepage content"),
            ("05_youtube_search_recommendations.py", "Generate search recommendations"),
            ("06_search_recommendations_reducer.py", "Reduce search recommendations"),
            ("07_content_curator.py", "Curate search results content"),
            ("08_youtube_action_list.py", "Generate action list"),
            ("09_youtube_take_action.py", "Execute YouTube actions")
        ]
    
    def print_header(self):
        """Print the script header with timestamp."""
        print("=" * 60)
        print("YouTube Automation Daily Run with Retry Logic")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Configuration: Max {self.max_retries} retries per step")
        print("=" * 60)
        print()
    
    def print_step_header(self, step_num: int, script: str, description: str):
        """Print header for each pipeline step."""
        print(f"\n📌 Step {step_num}/{len(self.pipeline_steps)}: {description}")
        print(f"   Script: {script}")
        print("-" * 60)
    
    def calculate_delay(self, retry_count: int) -> int:
        """
        Calculate exponential backoff delay with cap.
        
        Args:
            retry_count: Current retry attempt number
            
        Returns:
            Delay in seconds
        """
        # Exponential backoff: 5, 10, 20, 40, 60, 60, 60...
        delay = min(self.initial_delay * (2 ** retry_count), 60)
        return delay
    
    def run_command_with_retry(self, script: str, description: str) -> Tuple[bool, int]:
        """
        Run a single command with retry logic.
        
        Args:
            script: Python script filename to execute
            description: Human-readable description of the step
            
        Returns:
            Tuple of (success: bool, attempts: int)
        """
        command = [self.python_executable, script]
        
        for attempt in range(1, self.max_retries + 1):
            try:
                if attempt == 1:
                    print(f"🔄 Executing: {' '.join(command)}")
                else:
                    print(f"🔄 Retry {attempt}/{self.max_retries}: {' '.join(command)}")
                
                # Run the command
                result = subprocess.run(
                    command,
                    capture_output=False,  # Show output in real-time
                    text=True,
                    check=False  # Don't raise exception on non-zero exit
                )
                
                if result.returncode == 0:
                    print(f"✅ Success on attempt {attempt}!")
                    return True, attempt
                else:
                    print(f"❌ Failed with exit code {result.returncode}")
                    
                    if attempt < self.max_retries:
                        delay = self.calculate_delay(attempt - 1)
                        print(f"⏳ Waiting {delay} seconds before retry...")
                        time.sleep(delay)
                    else:
                        print(f"❌ Failed after {self.max_retries} attempts")
                        return False, attempt
                        
            except FileNotFoundError:
                print(f"❌ Error: Script '{script}' not found")
                return False, attempt
            except PermissionError:
                print(f"❌ Error: Permission denied for '{script}'")
                return False, attempt
            except KeyboardInterrupt:
                print("\n⚠️  Pipeline interrupted by user")
                return False, attempt
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                if attempt < self.max_retries:
                    delay = self.calculate_delay(attempt - 1)
                    print(f"⏳ Waiting {delay} seconds before retry...")
                    time.sleep(delay)
                else:
                    return False, attempt
        
        return False, self.max_retries
    
    def run_pipeline(self) -> bool:
        """
        Run the complete pipeline with retry logic.
        
        Returns:
            True if all steps completed successfully, False otherwise
        """
        self.print_header()
        
        successful_steps = []
        failed_step = None
        total_attempts = 0
        
        for step_num, (script, description) in enumerate(self.pipeline_steps, 1):
            self.print_step_header(step_num, script, description)
            
            success, attempts = self.run_command_with_retry(script, description)
            total_attempts += attempts
            
            if success:
                successful_steps.append((script, attempts))
            else:
                failed_step = (script, attempts)
                break
        
        # Print summary
        print("\n" + "=" * 60)
        print("PIPELINE EXECUTION SUMMARY")
        print("=" * 60)
        
        if successful_steps:
            print("\n✅ Successful Steps:")
            for script, attempts in successful_steps:
                if attempts == 1:
                    print(f"   - {script} (1 attempt)")
                else:
                    print(f"   - {script} ({attempts} attempts)")
        
        if failed_step:
            script, attempts = failed_step
            print(f"\n❌ Failed Step:")
            print(f"   - {script} (failed after {attempts} attempts)")
            print(f"\n❌ Pipeline stopped at step {len(successful_steps) + 1}/{len(self.pipeline_steps)}")
            print(f"   Total attempts across all steps: {total_attempts}")
            print("\n" + "=" * 60)
            print("❌ Daily automation failed. Please check the logs above.")
            print("=" * 60)
            return False
        else:
            print(f"\n✅ All {len(self.pipeline_steps)} steps completed successfully!")
            print(f"   Total attempts across all steps: {total_attempts}")
            print("\n" + "=" * 60)
            print("✅ Daily automation completed successfully!")
            print("=" * 60)
            return True
    
    def run_specific_steps(self, start_from: Optional[str] = None) -> bool:
        """
        Run pipeline starting from a specific step (useful for recovery).
        
        Args:
            start_from: Script filename to start from (e.g., "07_content_curator.py")
            
        Returns:
            True if all steps completed successfully, False otherwise
        """
        if start_from:
            # Find the starting index
            start_idx = None
            for idx, (script, _) in enumerate(self.pipeline_steps):
                if script == start_from:
                    start_idx = idx
                    break
            
            if start_idx is not None:
                print(f"📍 Starting from step: {start_from}")
                self.pipeline_steps = self.pipeline_steps[start_idx:]
            else:
                print(f"⚠️  Script '{start_from}' not found in pipeline")
                return False
        
        return self.run_pipeline()


def main():
    """Main entry point for the script."""
    runner = DailyPipelineRunner(max_retries=10, initial_delay=5)
    
    # Check for command-line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("YouTube Automation Daily Runner")
            print("\nUsage:")
            print("  python 00_run_daily.py              # Run complete pipeline")
            print("  python 00_run_daily.py --from SCRIPT # Start from specific script")
            print("\nExample:")
            print("  python 00_run_daily.py --from 07_content_curator.py")
            sys.exit(0)
        elif sys.argv[1] == "--from" and len(sys.argv) > 2:
            success = runner.run_specific_steps(start_from=sys.argv[2])
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Use --help for usage information")
            sys.exit(1)
    else:
        success = runner.run_pipeline()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()