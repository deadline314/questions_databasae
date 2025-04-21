import boto3
import json
import os
from openai import OpenAI
from botocore.config import Config

DEFAULT_CLAUDE = os.environ.get(
    "DEFAULT_CLAUDE", "anthropic.claude-3-5-sonnet-20241022-v2:0")

DEFAULT_CLAUDE_37 = os.environ.get(
    "DEFAULT_CLAUDE_37", "anthropic.claude-3-7-sonnet-20250219-v1:0")

def create_bedrock_runtime():
    config = Config(read_timeout=1000)
    bedrock_runtime = boto3.client(
        service_name="bedrock-runtime",
        region_name=os.getenv('AWS_REGION_NAME'),
        config=config
    )
    return bedrock_runtime


def inference_model_claude37(question, file_base64=None):
    client = create_bedrock_runtime()
    if file_base64:
        message = {
            "role": "user",
            "content": [
            {
                "text": question
            },
            {
                "type": "text",
                "text": file_base64
            }
        ]
    }
    else:
        message = {
            "role": "user",
            "content": [
                {
                    "text": question
                }
            ]
        }

    response = client.converse(
        modelId="arn:aws:bedrock:us-east-1:185271018684:inference-profile/us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        messages=[message]
    )

    predict_answer = response['output']['message']['content'][0]['text'].strip()
    return predict_answer

def inference_model_claude35(question, file_base64s=None):
    client = create_bedrock_runtime()
    if file_base64s:
        for file_base64 in file_base64s:
            message = {
                "role": "user",
                "content": [
                {
                    "text": question
                },
      
        ]}
        message["content"].append({
                "document": {
                    "format": "pdf",
                    "name": "pdf",
                    "source": {
                        "bytes": file_base64
                    }
                }
            })
    else:
        message = {
            "role": "user",
            "content": [
                {
                    "text": question
                }
            ]
        }

    response = client.converse(
        modelId="arn:aws:bedrock:us-east-1:185271018684:inference-profile/us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        messages=[message]
    )

    predict_answer = response['output']['message']['content'][0]['text'].strip()
    return predict_answer

def inference_model_chatgpt_4o(question, file_base64=None):
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    if file_base64:
        messages = [
            {
                "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": question
                }
        ]
        }
    ]
    else:
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": question
                    }
                ]
            }
        ]
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    predict_answer = response.choices[0].message.content.strip()
    return predict_answer