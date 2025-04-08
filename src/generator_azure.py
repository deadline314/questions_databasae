import os
import json
import base64
from openai import OpenAI,RateLimitError
import time

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('AZURE_OPENAI_API_KEY'))

# Define the prompts
prompts = [
    {
        "filename": "general_questions.json",
        "prompt": """
請根據文檔的內容，來給我50個題目以及答案。
"""
    },
    {
        "filename": "easy_questions.json",
        "prompt": """
請再給我50題不同的題目，但我希望每個題目的答案都只需要簡短的回應即可回答問題，很簡單也沒關係，例如
Q:壓縮機有幾個階段
A:5
Q:Mode 5 中的速度上限是？
A:2945 rpm
"""
    },
    {
        "filename": "true_false_questions.json",
        "prompt": "除此之外再給我50題是非題，答案只有 \"是\" 跟 \"否\""
    }
]

# Read PDF file and convert to base64
def pdf_to_base64(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    encoded_pdf = base64.b64encode(data).decode("utf-8")
    return encoded_pdf


def get_response(messages, retries=6):
    delay = 1
    for attempt in range(retries):
        try:
            # generate with best model
            response = client.chat.completions.create(
                model="gpt-4.5-preview",
                messages=messages,
            )
            return response.choices[0].message.content
        except RateLimitError as e:
            print(f"Rate limit exceeded, retrying in {delay} seconds...")
            time.sleep(delay)
            delay += 5
    raise Exception("Exceeded maximum retry attempts due to rate limits.")

# Main function

def generate_datasets(pdf_path):
    encoded_pdf = pdf_to_base64(pdf_path)

    output_dir = os.path.splitext(os.path.basename(pdf_path))[0]
    output_dir = f'./output/{output_dir}'
    
    # If the output directory already exists, skip the generation
    if os.path.exists(output_dir):
        print(f"Skipping {pdf_path} because it already exists.")
        return
    
    filename = os.path.basename(pdf_path)
    os.makedirs(output_dir, exist_ok=True)
    messages = [
        {
            "role": "system",
            "content": [
                {
                "type": "text",
                "text": "如果做不到的話請跟我說原因。\n只要給我中文的題目跟答案即可\n請注意題目跟答案只能從文本中生成\n請以json的格式回答我\n不要有任何描述性的文字，只需要給我json的資料即可\n\n格式請用\n[\n  {\"question\": \"\", \"answer\": \"\"}\n]"
                }
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompts[0]['prompt']
                },
                {
                    "type": "file",
                    "filename": filename,
                    "file_data": f"data:application/pdf;base64,{encoded_pdf}",
                }
            ]
        }
    ]

    for idx, item in enumerate(prompts):
        print(f"Generating {item['filename']} from {filename}...")

        if idx > 0:
            messages.append({"role": "user", "content": item['prompt']})

        response = get_response(messages)
        messages.append({"role": "assistant", "content": response})
        # print('--------------All messages:--------------')
        # print(messages[1:]) 
        print('--------------Response:--------------')
        print(response) 
        with open(os.path.join(output_dir, item['filename']), 'w', encoding='utf-8') as f:
            # Remove ```json and ```
            cleaned_response = response.strip().lstrip('```json').rstrip('```').strip()
            try:
                json_data = json.loads(cleaned_response)
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            except json.JSONDecodeError:
                print(f"Failed to parse JSON for {item['filename']}:")
                print(response)

# Main
if __name__ == "__main__":
    for pdf_name in os.listdir("./pdf"):
        pdf_path = os.path.join("./pdf", pdf_name)
        generate_datasets(pdf_path)
