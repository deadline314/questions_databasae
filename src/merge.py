import os
import json

def merge_json_files(root_folder, filename, output_filename):
    merged_data = []

    # Iterate each subfolder
    for subdir in os.listdir(root_folder):
        subdir_path = os.path.join(root_folder, subdir)
        
        # Check if it is a folder
        if os.path.isdir(subdir_path):
            file_path = os.path.join(subdir_path, filename)

            # If the file exists, read the content
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # add new key 'filename' to each data
                    for item in data:
                        item['filename'] = subdir
                        item['data_type'] = filename.split('.')[0]
                    merged_data.extend(data)
    print(f'{filename} has been merged to {output_filename}')
    # print the data length
    print(f'The length of {filename} is {len(merged_data)}')
    # Save the merged data
    return merged_data
# main
if __name__ == "__main__":
    root_folder = './output'  # The root folder
    file_names = ['general_questions.json', 'easy_questions.json', 'true_false_questions.json']
    merged_data = []
    # Merge each type of file
    for fname in file_names:
        output_file = f'./merged_output/{fname}'  # The merged file name
        if not os.path.exists('./merged_output'):
            os.makedirs('./merged_output')
        merged_data.extend(merge_json_files(root_folder, fname, output_file))
        
        print(f'{fname} has been merged to {output_file}')
        
    # make json structure data with question, answer, data_type, filename to data_type, filename, question, answer
    merged_data = [{'data_type': item['data_type'], 'filename': item['filename'], 'question': item['question'], 'answer': item['answer']} for item in merged_data]
    with open('./merged_output/all_questions.json', 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)