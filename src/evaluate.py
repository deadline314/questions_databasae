import os
import json
import base64
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


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

# Evaluate true/false questions using OpenAI API
def evaluate_true_false_questions(question):
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    filename = question['filename']
    with open(f'./pdf/{filename}.pdf', 'rb') as f:
        pdf_base64 = base64.b64encode(f.read()).decode('utf-8')

    
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": f"根據pdf文件，請回應問題的答案，並只要回答'是'或'否'就好。\n問題: {question['question']}"
                },
                {
                    "type": "input_file",
                    "filename": filename,
                    "file_data": f"data:application/pdf;base64,{pdf_base64}",
                }
            ]
        }
    ]

    response = client.responses.create(
                model="gpt-4o",
                input=messages,
                temperature=1,
                max_output_tokens=16,
                top_p=1
                )
    return response.output_text.strip() == question['answer']

# Evaluate general open-ended questions
def evaluate_general_questions(question):
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    filename = question['filename']
    with open(f'./pdf/{filename}.pdf', 'rb') as f:
        pdf_base64 = base64.b64encode(f.read()).decode('utf-8')

    except_answer = question['answer']
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": f"請根據pdf文件，簡短的回答問題\nQuestion: {question['question']}"
                },
                {
                    "type": "input_file",
                    "filename": filename,
                    "file_data": f"data:application/pdf;base64,{pdf_base64}",
                }
            ]
        }
    ]
    response = client.responses.create(
                model="gpt-4o",
                input=messages,
                temperature=1,
                max_output_tokens=50,
                top_p=1
                )
    predict_answer = response.output_text.strip()

    # Second round evaluation for semantic similarity
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": f"請告訴我根據問題實際上的答案與模型預測的答案意思是否正確，不用到一模一樣意思相同即可，請以'是'或'否'回答。\n問題: {question['question']}\n實際上的答案: {except_answer}\n模型預測的答案: {predict_answer}"
                }
            ]
        }
    ]


    response = client.responses.create(
                model="gpt-4o",
                input=messages,
                temperature=1,
                max_output_tokens=16,
                top_p=1
                )
    return response.output_text.strip() == '是'

# Evaluate short easy questions
def evaluate_easy_questions(question):
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    filename = question['filename']
    with open(f'./pdf/{filename}.pdf', 'rb') as f:
        pdf_base64 = base64.b64encode(f.read()).decode('utf-8')

    except_answer = question['answer']
    
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": f"請根據pdf文件，簡短的回答問題\nQuestion: {question['question']}"
                },
                {
                    "type": "input_file",
                    "filename": filename,
                    "file_data": f"data:application/pdf;base64,{pdf_base64}",
                }
            ]
        }
    ]

    response = client.responses.create(
                model="gpt-4o",
                input=messages,
                temperature=1,
                max_output_tokens=50,
                top_p=1
                )
    predict_answer = response.output_text.strip()


    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": f"請告訴我根據問題實際上的答案與模型預測的答案意思是否正確，不用到一模一樣意思相同即可，請以'是'或'否'回答。\n問題: {question['question']}\n實際上的答案: {except_answer}\n模型預測的答案: {predict_answer}"
                }
            ]
        }
    ]

    response = client.responses.create(
                model="gpt-4o",
                input=messages,
                temperature=1,
                max_output_tokens=16,
                top_p=1
                )
    return response.output_text.strip() == '是'

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
def evaluate_datasets(file_path):
    questions, answers, data_types, filenames = extract_questions_and_answers(file_path)
    time0 = time.time()
    # Group all questions by filename
    grouped_data = {}
    for q, a, t, f in zip(questions, answers, data_types, filenames):
        grouped_data.setdefault(f, []).append({'question': q, 'answer': a, 'data_type': t, 'filename': f})

    all_tasks = []
    for filename, items in grouped_data.items():
        tf_questions = [q for q in items if q['data_type'] == 'true_false_questions'][:1]
        easy_questions = [q for q in items if q['data_type'] == 'easy_questions'][:2]
        general_questions = [q for q in items if q['data_type'] == 'general_questions'][:1]

        for q in tf_questions:
            all_tasks.append((filename, evaluate_true_false_questions, q))
        for q in easy_questions:
            all_tasks.append((filename, evaluate_easy_questions, q))
        for q in general_questions:
            all_tasks.append((filename, evaluate_general_questions, q))

    # Dictionary to store results by filename
    result_map = {}

    time1 = time.time()
    print(f"time1: {time1 - time0}")
    # Run all tasks concurrently
    with ThreadPoolExecutor(max_workers=20) as executor:
        future_to_task = {executor.submit(func, q): (filename, func) for filename, func, q in all_tasks}

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
    evaluate_datasets('./merged_output/all_questions.json')