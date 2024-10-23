#!/bin/bash

#Check if the output file was provided
if [ -z "$1" ]; then
    echo "Usage: $0 <output_file>"
    exit 1
fi

# Get the directory of the output file (new_directory)
new_directory=$(dirname "$1")

# Change to the new directory
cd "$new_directory" || { echo "Failed to change directory"; exit 1; }

# Run the talys executable with the output file
~/Documents/talys/bin/talys <$1> out