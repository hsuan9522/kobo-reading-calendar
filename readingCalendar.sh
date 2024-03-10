#! /bin/sh

# echo 123
cd /mnt/onboard/.adds/utils/analytics
python_version=$(python --version 2>&1)
echo "Python version: $python_version"

python readingCalendar.py