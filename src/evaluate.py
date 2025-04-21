import os
import json
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import sys
from inference_model import inference_model_claude37, inference_model_claude35, inference_model_chatgpt_4o
from file_processing import split_pdf_to_bytes

AWS_REGION_NAME = os.environ.get("AWS_REGION_NAME", "us-west-2")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID_TEST", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY_TEST", "")
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY_TEST", "")
AZURE_API_BASE = os.environ.get("AZURE_API_BASE_TEST", "")
OPENAI_API_VERSION = os.environ.get("OPENAI_API_VERSION", "2024-07-01-preview") 
DEFAULT_CLAUDE = os.environ.get(
    "DEFAULT_CLAUDE", "anthropic.claude-3-5-sonnet-20241022-v2:0")

# Load and parse the dataset from a JSON file
def extract_questions_and_answers(dataset_dir):
    questions, answers, data_types, filenames = [], [], [], []
    with open(dataset_dir, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for item in data:
            questions.append(item['question'])
            answers.append(item['answer'])
            data_types.append(item['data_type'])
            filenames.append(item['filename'])
    return questions, answers, data_types, filenames

def inference_model(model_name, question, file_base64):
    if model_name == 'gpt-4o':
        return inference_model_chatgpt_4o(question, file_base64)
    elif model_name == 'claude35':
        return inference_model_claude35(question, file_base64)
    elif model_name == 'claude37':
        return inference_model_claude37(question, file_base64)

# Evaluate true/false questions using OpenAI API
def evaluate_true_false_questions(question, model_name):
    filename = question['filename']
    if model_name == 'gpt-4o':
        with open(f'./pdf/{filename}.pdf', 'rb') as f:
            pdf_base64 = base64.b64encode(f.read()).decode('utf-8')
    else:
        # Check file size > 4.5mb
        if os.path.getsize(f'./pdf/{filename}.pdf') > 4.5 * 1024 * 1024:
            base64_outputs = split_pdf_to_bytes(f'./pdf/{filename}.pdf')
            pdf_base64 = base64_outputs
        else:
            with open(f'./pdf/{filename}.pdf', 'rb') as f:
                pdf_base64 = [f.read()]

    except_answer = question['answer']
    prompt = f"根據pdf文件，請回應問題的答案，並只要回答'是'或'否'就好。\n問題: {question['question']}"
    predict_answer = inference_model(model_name, prompt, pdf_base64)
    return predict_answer == except_answer

# Evaluate general open-ended questions
def evaluate_general_questions(question, model_name):
    filename = question['filename']
    if model_name == 'gpt-4o':
        with open(f'./pdf/{filename}.pdf', 'rb') as f:
            pdf_base64 = base64.b64encode(f.read()).decode('utf-8')
    else:
        # Check file size > 4.5mb
        if os.path.getsize(f'./pdf/{filename}.pdf') > 4.5 * 1024 * 1024:
            base64_outputs = split_pdf_to_bytes(f'./pdf/{filename}.pdf')
            pdf_base64 = base64_outputs
        else:
            with open(f'./pdf/{filename}.pdf', 'rb') as f:
                pdf_base64 = [f.read()]

    except_answer = question['answer']
    question_prompt = f"請根據pdf文件，簡短的回答問題\nQuestion: {question['question']}"
    predict_answer = inference_model(model_name, question_prompt, pdf_base64)
    
    evaluate_prompt= f"請告訴我根據問題實際上的答案與模型預測的答案意思是否正確，不用到一模一樣意思相同即可，請以'是'或'否'回答。\n問題: {question['question']}\n實際上的答案: {except_answer}\n模型預測的答案: {predict_answer}"
    evaluate_answer = inference_model('claude37', evaluate_prompt, None)
    return evaluate_answer == '是'

# Evaluate short easy questions
def evaluate_easy_questions(question, model_name):
    filename = question['filename']
    if model_name == 'gpt-4o':
        with open(f'./pdf/{filename}.pdf', 'rb') as f:
            pdf_base64 = base64.b64encode(f.read()).decode('utf-8')
    else:
        # Check file size > 4.5mb
        if os.path.getsize(f'./pdf/{filename}.pdf') > 4.5 * 1024 * 1024:
            base64_outputs = split_pdf_to_bytes(f'./pdf/{filename}.pdf')
            pdf_base64 = base64_outputs
        else:
            with open(f'./pdf/{filename}.pdf', 'rb') as f:
                pdf_base64 = [f.read()]

    except_answer = question['answer']
    question_prompt = f"請根據pdf文件，簡短的回答問題\nQuestion: {question['question']}"
    predict_answer = inference_model(model_name, question_prompt, pdf_base64)
    
    evaluate_prompt= f"請告訴我根據問題實際上的答案與模型預測的答案意思是否正確，不用到一模一樣意思相同即可，請以'是'或'否'回答。\n問題: {question['question']}\n實際上的答案: {except_answer}\n模型預測的答案: {predict_answer}"
    evaluate_answer = inference_model('claude37', evaluate_prompt, None)
    return evaluate_answer == '是'

# Format and print evaluation results in a dynamic table
def dynamic_table_output(results):
    headers = ["Filename", "True False Questions", "General Questions", "Easy Questions", "Total", "Accuracy"]
    data_rows = []

    total_tf = total_gq = total_eq = 0
    total_tf_q = total_gq_q = total_eq_q = 0

    for filename, tf_score, gq_score, eq_score, tf_count, gq_count, eq_count in results:
        total_score = tf_score + gq_score + eq_score
        total_count = tf_count + gq_count + eq_count
        accuracy = f"{(total_score / total_count * 100):.2f}%" if total_count > 0 else "N/A"

        data_rows.append([filename, str(tf_score), str(gq_score), str(eq_score), str(total_score), accuracy])

        total_tf += tf_score
        total_gq += gq_score
        total_eq += eq_score
        total_tf_q += tf_count
        total_gq_q += gq_count
        total_eq_q += eq_count

    total_score = total_tf + total_gq + total_eq
    total_count = total_tf_q + total_gq_q + total_eq_q
    total_accuracy = f"{(total_score / total_count * 100):.2f}%" if total_count > 0 else "N/A"
    data_rows.append(["Total", str(total_tf), str(total_gq), str(total_eq), str(total_score), total_accuracy])

    col_widths = [max(len(str(row[i])) for row in ([headers] + data_rows)) + 2 for i in range(len(headers))]
    row_format = "| " + " | ".join("{:<" + str(w) + "}" for w in col_widths) + " |"

    print(row_format.format(*headers))
    print("|" + "|".join("-" * (w + 2) for w in col_widths) + "|")

    for i, row in enumerate(data_rows):
        print(row_format.format(*row))
        if i == len(data_rows) - 2:
            print("|" + "|".join("=" * (w + 2) for w in col_widths) + "|")

# Main evaluation function
def evaluate_datasets(file_path, model_name):
    questions, answers, data_types, filenames = extract_questions_and_answers(file_path)
    time0 = time.time()
    # Group all questions by filename
    grouped_data = {}
    for q, a, t, f in zip(questions, answers, data_types, filenames):
        grouped_data.setdefault(f, []).append({'question': q, 'answer': a, 'data_type': t, 'filename': f})

    all_tasks = []
    for filename, items in grouped_data.items():
        tf_questions = [q for q in items if q['data_type'] == 'true_false_questions'][:1]
        easy_questions = [q for q in items if q['data_type'] == 'easy_questions'][:1]
        general_questions = [q for q in items if q['data_type'] == 'general_questions'][:1]

        for q in tf_questions:
            all_tasks.append((filename, evaluate_true_false_questions, q, model_name))
        for q in easy_questions:
            all_tasks.append((filename, evaluate_easy_questions, q, model_name))
        for q in general_questions:
            all_tasks.append((filename, evaluate_general_questions, q, model_name))

    # Dictionary to store results by filename
    result_map = {}

    time1 = time.time()
    print(f"time1: {time1 - time0}")
    # Run all tasks concurrently
    with ThreadPoolExecutor(max_workers=20) as executor:
        future_to_task = {executor.submit(func, q, model_name): (filename, func) for filename, func, q, model_name in all_tasks}

        for future in as_completed(future_to_task):
            filename, func = future_to_task[future]
            result = future.result()
            if filename not in result_map:
                result_map[filename] = {'tf': [0, 0], 'gq': [0, 0], 'eq': [0, 0]}
            if func == evaluate_true_false_questions:
                result_map[filename]['tf'][1] += 1
                if result: result_map[filename]['tf'][0] += 1
            elif func == evaluate_general_questions:
                result_map[filename]['gq'][1] += 1
                if result: result_map[filename]['gq'][0] += 1
            elif func == evaluate_easy_questions:
                result_map[filename]['eq'][1] += 1
                if result: result_map[filename]['eq'][0] += 1

    time2 = time.time()
    print(f"time2: {time2 - time1}")
    # Prepare final results for output
    results = []
    for filename, scores in result_map.items():
        results.append((
            filename,
            scores['tf'][0], scores['gq'][0], scores['eq'][0],
            scores['tf'][1], scores['gq'][1], scores['eq'][1]
        ))

    dynamic_table_output(results)

# Entry point
if __name__ == '__main__':
    if len(sys.argv) != 2:
        evaluate_datasets('./merged_output/all_questions.json', 'gpt-4o')
    else:
        evaluate_datasets('./merged_output/all_questions.json', sys.argv[1])