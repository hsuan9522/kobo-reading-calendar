#! /bin/sh

arg1="$1"
cd /mnt/onboard/.adds/utils/analytics

# Keep user data and settings across installs. The package only replaces the
# defaults; working copies are created on first use.
mkdir -p ./data ./image
if [ ! -f ../HsKobo.sqlite ]; then
    cp ../HsKobo.sqlite.template ../HsKobo.sqlite
fi
if [ ! -f ./config.ini ]; then
    cp ./config.ini.default ./config.ini
fi

# python_version=$(python --version 2>&1)
# echo "Python version: $python_version"
fbink -qpm -y -2 "Start Drawing..." &
python readingCalendar.py $arg1 > ./log 2>&1

# if [ $? -ne 0 ]; then
#     fbink -qpm -y -2 "Run Python failed."
#     echo "Error: Python script failed."
#     exit 1
# fi

file_name=$(grep 'file_name:' "./log" | awk -F': ' '{print $2}')

if [ -n "$file_name" ]; then
    fbink -g file=$file_name
else
    echo "No file_name found in the log."
fi
