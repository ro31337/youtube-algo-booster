# YouTube Educational Content Automation Suite

A comprehensive automation toolkit for YouTube that uses AI to identify educational content, perform searches, and automatically like/dislike videos based on their educational value. Built with Patchright (undetected browser automation) and OpenAI GPT-4.

## Inspiration

Шёл 2025 год. Корпорации захватили мир. И не только мир. Сознание. И не только сознание. Они захватили сознание наших детей. Отныне каждый ребенок смотрит в экран и скроллит, скроллит, скроллит. Они используют наших детей для своей собственной выгоды. Что им выгоднее, спросите вы? Показать образовательное видео и заработать 99 центов или показать дьявольски-отупляющее видео и заработать 1 доллар? Да, они действуют исключительно ради наживы. Они наживаются на нас. На наших детях. Они списывают это на алгоритмы. Но пришла пора повернуть эту дьявольскую машину вспять и повлиять на алгоритм. Эти скрипты говорят алгоритму что нравится нам, а не им. Нам нравится образовательный контент. Мы дизлайкаем всё отупляющее, весь интернет-мусор, всю самую мерзкую помойку, которую они выливают на нас и наших детей. Мы делаем алгоритм умнее. И он служит нам. Они не догадываются, что мы их используем. Нас немного, но мы есть.

## Features

- **AI-Powered Content Curation**: Uses OpenAI to evaluate educational value of videos
- **Automated Actions**: Likes educational content and dislikes non-educational content
- **Smart Search**: Generates and searches for grade-appropriate educational content
- **Stealth Browser Automation**: Bypass bot detection using Patchright
- **Persistent Sessions**: Save and reuse login sessions across runs
- **Daily Automation**: Complete pipeline that can run daily with a single command
- **6th Grade Focus**: Specifically tuned for 6th grade math and educational standards

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

## Installation

1. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Install Patchright browser:
```bash
patchright install chromium
```

4. Set up environment variables (optional):
```bash
# Copy the example file
cp .env.example .env

# Edit .env with your credentials
# GOOGLE_EMAIL=your.email@gmail.com
# GOOGLE_PASSWORD=your_password_here
```

## Project Structure

```
.
├── README.md                              # This documentation file
├── requirements.txt                       # Python dependencies
├── run-daily.sh                          # Daily automation script (runs 03-09)
├── .env                                   # Environment variables for credentials
├── .env.example                           # Template for environment variables
├── .gitignore                            # Git ignore rules
│
├── Setup & Authentication Scripts:
│   ├── 00_cleanup_persistence.py         # Clear saved browser sessions and start fresh
│   ├── 01_youtube_sign_in.py            # Authenticate with Google/YouTube (visible browser)
│   └── 02_youtube_optional_switch_channel.py  # Switch between YouTube channels (headless)
│
├── Daily Pipeline Scripts (03-09):
│   ├── 03_youtube_get_index_page_videos.py  # Extract videos from YouTube homepage
│   ├── 04_content_curator.py                # AI evaluates homepage videos, generates search terms
│   ├── 05_youtube_search_recommendations.py # Search YouTube for educational content
│   ├── 06_search_recommendations_reducer.py # Reduce results to prevent AI timeout
│   ├── 07_content_curator.py                # AI evaluates search results
│   ├── 08_youtube_action_list.py           # Generate list of videos to like/dislike
│   └── 09_youtube_take_action.py           # Perform like/dislike actions on YouTube
│
├── Supporting Files:
│   ├── shared_auth.py                    # Shared authentication checking functions
│   └── 04_current_grade_math_standards.txt # 6th grade math standards for AI reference
│
├── Generated Directories:
│   ├── chrome_profile/                   # Persistent browser profile (auto-created)
│   ├── screenshots/                      # Screenshot output directory (auto-created)
│   └── venv/                            # Python virtual environment
│
└── Generated JSON Files (overwritten daily):
    ├── 03_youtube_get_index_page_videos.json  # Homepage videos and shorts
    ├── 04_content_curator.json                # Homepage analysis + recommendations
    ├── 05_youtube_search_recommendations.json # Search results (all)
    ├── 06_search_recommendations_reduced.json # Search results (3 per search)
    ├── 07_content_curator.json                # Search results analysis
    └── 08_youtube_action_list.json           # Final list of actions to perform
```

## Script Descriptions

### Setup Scripts (Run Once)

**`00_cleanup_persistence.py`**
- Removes saved browser profile and sessions
- Shows profile size before deletion
- Prompts for confirmation before deleting
- Use when: switching accounts, troubleshooting login issues, or starting fresh

**`01_youtube_sign_in.py`**
- Always runs with visible browser window
- Navigates to YouTube and initiates sign-in
- Supports automated email/password entry from .env file
- Allows manual sign-in for security-conscious users
- Shows available channels if multiple exist
- Saves session in persistent browser profile for reuse

**`02_youtube_optional_switch_channel.py`**
- Runs in headless mode (no visible browser)
- Lists all YouTube channels on the account
- Allows selection of a different channel
- Only needed if you have multiple YouTube channels
- Saves channel selection for future automation

### Daily Pipeline Scripts (Run via `./run-daily.sh`)

**`03_youtube_get_index_page_videos.py`**
- Extracts videos and YouTube Shorts from homepage
- Runs in headless mode (1920x1080 viewport)
- `--debug` flag: Shows visible browser for inspection
- Output: `03_youtube_get_index_page_videos.json` (overwritten each run)
- Displays summary of extracted content

**`04_content_curator.py`**
- Uses OpenAI GPT-4o-mini to analyze homepage videos
- Evaluates educational value for an 11-year-old 6th grader
- Generates 10 randomized search recommendations:
  - 5 math-focused (2 must include "easy")
  - 5 curiosity-sparking world knowledge
- Output: `04_content_curator.json` (overwritten each run)
- Marks videos with "like": true/false

**`05_youtube_search_recommendations.py`**
- Searches YouTube for each recommendation from step 04
- Extracts videos and shorts from search results
- Filters out sponsored content
- Output: `05_youtube_search_recommendations.json` (overwritten each run)
- `--debug` flag: Shows visible browser

**`06_search_recommendations_reducer.py`**
- Randomly selects 3 videos and 3 shorts per search term
- Prevents AI timeout by reducing data size
- Output: `06_search_recommendations_reduced.json` (overwritten each run)
- Shows reduction statistics

**`07_content_curator.py`**
- Analyzes reduced search results for educational value
- More selective than homepage analysis
- Verifies content is genuinely educational
- Output: `07_content_curator.json` (overwritten each run)
- Typically approves ~75% of videos, ~10% of shorts

**`08_youtube_action_list.py`**
- Compiles final action list:
  - ALL videos to dislike from homepage (unlimited)
  - Up to 10 videos to like from searches (random selection)
  - Up to 10 shorts to like from searches (random selection)
- Output: `08_youtube_action_list.json` (overwritten each run)
- Creates flat structure with URLs and actions

**`09_youtube_take_action.py`**
- Performs like/dislike actions on YouTube
- Navigates to each video/short
- Clicks appropriate like/dislike button
- Takes screenshot after each action
- `--debug` flag: Stops after first video for inspection
- Checks if already liked/disliked to avoid duplicates

### Shared Modules

**`shared_auth.py`**
- `check_browser_profile()`: Verifies browser profile exists
- `check_youtube_auth()`: Confirms YouTube authentication
- `print_header()`: Formatted header output
- `print_section()`: Formatted section output
- Used by scripts 02 and 03 for consistent auth checking

### Configuration Files

**`.env`**
- Stores Google account credentials securely
- Never commit this file to version control
- Variables: GOOGLE_EMAIL, GOOGLE_PASSWORD

**`.env.example`**
- Template showing required environment variables
- Copy to `.env` and fill in your credentials

**`requirements.txt`**
- Lists Python package dependencies
- Main packages: patchright (Playwright fork), python-dotenv, openai

## Usage

### Quick Start - Daily Automation

After initial setup, run the complete pipeline daily with one command:

```bash
./run-daily.sh
```

This script runs steps 03-09 automatically, performing:
1. Homepage video extraction
2. AI analysis and search term generation
3. Educational content search
4. Search results reduction
5. Search results AI analysis
6. Action list generation
7. Like/dislike actions on YouTube

### Initial Setup (Run Once)

```bash
# 1. Authenticate with YouTube and select your channel
python 01_youtube_sign_in.py

# 2. (Optional) Switch to a different YouTube channel
python 02_youtube_optional_switch_channel.py
```

After setup, you're ready to use the daily automation script.

### Manual Step-by-Step Execution

You can also run each script individually:

```bash
# Step 1: Extract homepage videos
python 03_youtube_get_index_page_videos.py

# Step 2: AI analyzes homepage and generates search terms
python 04_content_curator.py

# Step 3: Search YouTube for educational content
python 05_youtube_search_recommendations.py

# Step 4: Reduce search results to prevent AI timeout
python 06_search_recommendations_reducer.py

# Step 5: AI analyzes search results
python 07_content_curator.py

# Step 6: Generate action list
python 08_youtube_action_list.py

# Step 7: Perform like/dislike actions
python 09_youtube_take_action.py
```

### Debug Mode

Most scripts support `--debug` flag for troubleshooting:

```bash
# See browser window during homepage extraction
python 03_youtube_get_index_page_videos.py --debug

# See browser during search
python 05_youtube_search_recommendations.py --debug

# Stop after first video to inspect like/dislike buttons
python 09_youtube_take_action.py --debug
```

### Resetting or Switching Accounts

```bash
# Clear all saved browser data and sessions
python 00_cleanup_persistence.py

# Then re-authenticate
python 01_youtube_sign_in.py
```

## Daily Automation Script

The `run-daily.sh` script executes the complete pipeline (scripts 03-09) with a single command:

```bash
./run-daily.sh
```

### What it does:
1. **Extracts** videos from YouTube homepage
2. **Analyzes** them with AI for educational value
3. **Searches** for educational content based on AI recommendations
4. **Reduces** search results to manageable size
5. **Evaluates** search results for quality
6. **Generates** a list of videos to like (educational) and dislike (non-educational)
7. **Performs** the like/dislike actions on YouTube

### Important Notes:
- All JSON files are **overwritten** each run to ensure fresh data
- The script stops if any step fails (uses `&&` chaining)
- Takes approximately 5-10 minutes to complete
- Screenshots are saved in the `screenshots/` directory for verification

### Scheduling Daily Runs

You can schedule this to run automatically using cron (Linux/Mac):

```bash
# Edit your crontab
crontab -e

# Add this line to run daily at 2 AM
0 2 * * * cd /path/to/youtube_auto_liker2 && ./run-daily.sh >> daily_run.log 2>&1
```

## Configuration

### Environment Variables

Create a `.env` file in the project root (see `.env.example`):

```bash
GOOGLE_EMAIL=your.email@gmail.com
GOOGLE_PASSWORD=your_password_here
```

### Customizing Automation Tasks

Edit `03_youtube_automation.py` to add your automation logic:

```python
# Example: Navigate to a specific video
video_url = "https://www.youtube.com/watch?v=VIDEO_ID"
await page.goto(video_url, wait_until="networkidle")

# Example: Click like button
like_button = await page.wait_for_selector('button[aria-label*="like"]')
await like_button.click()

# Example: Subscribe to a channel
subscribe_button = await page.wait_for_selector('#subscribe-button')
await subscribe_button.click()
```

## Troubleshooting

### Common Issues

1. **"No saved browser profile found!"**
   - Run `python 01_youtube_sign_in.py` first to authenticate
   - Make sure you completed the sign-in process before closing

2. **"Browser or app may not be secure" error**
   - This is Google's bot detection
   - Complete the sign-in manually in the browser window
   - Once signed in successfully, the session will be saved

3. **Patchright not installed**
   - Run `patchright install chromium`
   - Make sure you're in the correct virtual environment

4. **Session expired or invalid**
   - Run `python 00_cleanup_persistence.py` to clear old data
   - Then run `python 01_youtube_sign_in.py` to re-authenticate

## Technologies Used

- **Patchright**: Undetected browser automation (Playwright fork)
- **Python**: Programming language
- **Asyncio**: Asynchronous programming support

## Notes

- This project is for educational purposes
- The authentication script (`01_youtube_sign_in.py`) always runs with a visible browser
- The channel switcher script (`02_youtube_optional_switch_channel.py`) runs in headless mode
- The automation script (`03_youtube_automation.py`) always runs in headless mode
- Browser sessions are persisted in the `chrome_profile/` directory
- Screenshots are saved in the `screenshots/` directory

## License

This project is for educational and demonstration purposes.