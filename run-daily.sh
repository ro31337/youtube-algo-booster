#!/bin/bash

# YouTube Automation Daily Run Script
# Runs the complete pipeline from video extraction to performing actions

echo "============================================================"
echo "YouTube Automation Daily Run"
echo "Date: $(date)"
echo "============================================================"

# Run the complete pipeline
./venv/bin/python 03_youtube_get_index_page_videos.py && \
./venv/bin/python 04_content_curator.py && \
./venv/bin/python 05_youtube_search_recommendations.py && \
./venv/bin/python 06_search_recommendations_reducer.py && \
./venv/bin/python 07_content_curator.py && \
./venv/bin/python 08_youtube_action_list.py && \
./venv/bin/python 09_youtube_take_action.py

# Check if all scripts ran successfully
if [ $? -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo "✅ Daily automation completed successfully!"
    echo "============================================================"
else
    echo ""
    echo "============================================================"
    echo "❌ Daily automation failed. Check the logs above for errors."
    echo "============================================================"
    exit 1
fi