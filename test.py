import os
import ast
import json
import boto3
from botocore.config import Config
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

AWS_REGION_NAME = os.environ.get("AWS_REGION_NAME", "us-west-2")
DEFAULT_CLAUDE = os.environ.get(
    "DEFAULT_CLAUDE", "anthropic.claude-3-5-sonnet-20241022-v2:0")

# 建立 Bedrock Runtime client
def create_bedrock_runtime():
    config = Config(read_timeout=1000)
    return boto3.client(
        service_name="bedrock-runtime",
        region_name=AWS_REGION_NAME,
        config=config
    )

client = create_bedrock_runtime()

# 遍歷所有 .py 檔案，排除不需要的
def find_py_files(base_path):
    py_files = []
    for root, dirs, files in os.walk(base_path):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                py_files.append(os.path.join(root, file))
    return py_files

# 建立發送到 Claude 的 payload
def create_body(file_code):
    parameter = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "temperature": 0.0,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""
你是一位資深的軟體測試工程師。以下是一個 Python 檔案的完整內容，請你找出其中所有的函數，並針對每個函數，判斷是否需要撰寫 unit test，並說明原因。

請以 JSON 格式回覆，格式如下：

[
  {{
    "function_name": "函數名稱",
    "require": true 或 false,
    "reason": "為什麼需要或不需要寫 unit test"
  }},
  ...
]

Python 檔案內容如下：
{file_code}
"""
                    }
                ]
            }
        ]
    }
    return json.dumps(parameter)

# 呼叫 Claude
def ask_claude_should_test(file_code):
    try:
        payload = create_body(file_code)
        response = client.invoke_model(
            body=payload,
            modelId=DEFAULT_CLAUDE,
            accept="application/json",
            contentType="application/json"
        )
        output = json.loads(response.get("body").read())
        return output.get("content")[0].get("text")
    except Exception as e:
        return json.dumps({"error": str(e)})

# 處理單一檔案
def analyze_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            file_code = f.read()
        raw_response = ask_claude_should_test(file_code)

        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError:
            parsed = [{"error": "JSON 解析錯誤", "raw": raw_response}]

        return {
            "file": filepath,
            "results": parsed
        }
    except Exception as e:
        return {
            "file": filepath,
            "results": [{"error": str(e)}]
        }

# 主程式：統整所有檔案結果並寫入一個檔案
def analyze_project(base_path):
    py_files = find_py_files(base_path)
    print(f"\n🔍 開始分析 {len(py_files)} 個 Python 檔案...\n")

    all_results = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(analyze_file, path): path for path in py_files}
        for future in tqdm(as_completed(futures), total=len(py_files), desc="分析進度"):
            filepath = futures[future]
            try:
                result = future.result()
                all_results.append(result)
                print(f"已處理：{filepath}")
            except Exception as e:
                print(f"錯誤：{filepath} - {e}")

    output_path = os.path.join(base_path, "unit_test_analysis.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\n所有分析完成，結果已寫入：{output_path}")

# 執行分析
if __name__ == "__main__":
    analyze_project(".")