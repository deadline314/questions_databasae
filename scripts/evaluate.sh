if [[ "$1" == "claude35" ]]; then
    echo "Using claude3.5 to evaluate the model..."
    # Execute the Azure version
    python src/evaluate.py claude35
elif [[ "$1" == "claude37" ]]; then
    echo "Using claude3.7 to evaluate the model..."
    # Execute the one file
    python src/evaluate.py claude37
else
    echo "Using default version gpt-4o..."
    # Execute the default version
    python src/evaluate.py openai-gpt-4o
fi