#!/bin/bash

if [[ "$1" == "azure" ]]; then
    echo "Using Azure version..."
    # Execute the Azure version
    python src/generator_azure.py
elif [[ "$1" == "one_file" ]]; then
    echo "Using one file version..."
    # Execute the one file
    python src/generator_one_file.py
else
    echo "Using default version..."
    # Execute the default version
    python src/generator.py
fi