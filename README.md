# Quick Start

If already have environment on your machine, just need to run the following command to install requirements and start the project.
```
make init
```

If don't have environment, you can create a new environment by running the following command.
```
make env
```

Run above command will generate the three kind of dataset from [pdf](https://github.com/deadline314/questions_databasae/tree/main/pdf) files.
If can put the pdf files which you want to generate the dataset in [pdf folder](https://github.com/deadline314/questions_databasae/tree/main/pdf).
You will see the result in [output](https://github.com/deadline314/questions_databasae/tree/main/output) folder.
```
make generate
```

## Notice
Please use the following command to set the OPENAI_API_KEY in your environment.
If you don't have one, you can get one form [OpenAI API Keys](https://platform.openai.com/api-keys)
```
export OPENAI_API_KEY='sk-xxxxxx'
```



# Question Answering Model

This repository was created to compare the text generation quality and semantic understanding capabilities of different models.

## Motivation

It is challenging to directly measure the semantic understanding abilities of various models. Therefore, I used GPT-4o to generate a set of questions based on different PDF documents.

## Types of Questions Included:

1. **Semantic Understanding Questions**  
   These questions assess the model’s ability to comprehend and interpret content at a deeper level. Since evaluating the accuracy of semantic understanding can be subjective, these questions are included primarily for qualitative analysis.

2. **Short Answer Questions**  
   These questions require concise and direct responses, making it easier to compare the models’ precision and response accuracy.

3. **True/False Questions**  
   True/False questions are included to facilitate quick evaluation, as the correctness of the responses can be directly assessed.

## Purpose of This Repository

By incorporating a variety of question types, I aim to:

- Gain a more comprehensive understanding of how different models perform in different scenarios.
- Evaluate their strengths and weaknesses in semantic understanding, concise response generation, and factual accuracy.

## Future Enhancements

- [x] **Automated Dataset Generator** Can automatly generate the three kinds of dataset from pdf file.
- [ ] **Automated Evaluation Metrics:** Explore the use of automated scoring systems to assess the accuracy and relevance of generated responses.
- [ ] **Expanded Dataset:** Incorporate a wider range of document types to test the models across more diverse contexts.
