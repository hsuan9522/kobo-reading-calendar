#! /bin/sh

arg1="$1"
cd /mnt/onboard/.adds/utils/analytics
# python_version=$(python --version 2>&1)
# echo "Python version: $python_version"

python3 readingCalendar.py $arg1

if [ $? -ne 0 ]; then
    echo "Error: Python script failed."
    exit 1
fi