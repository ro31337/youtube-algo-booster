#!/bin/bash

# YouTube Automation Daily Run Script
# This script now delegates to the Python script with retry logic

# Run the new Python script with retry logic
./venv/bin/python 00_run_daily.py "$@"

# Exit with the same code as the Python script
exit $?