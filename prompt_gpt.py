from flask import Flask, request, jsonify
import openai
import tiktoken
import json
from PIL import Image
from flask import Flask, request
import easyocr
import cv2
import numpy as np

from io import BytesIO

app = Flask(__name__)


MAX_TOKEN = 1000




def count_tokens(text):
    tokenizer = tiktoken.get_encoding("cl100k_base")
    tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo") 
    
    return len(tokenizer.encode(text))

def split_token(text, token_limit):
    characters = list(text)

    current_text = ""
    texts = []

    for char in characters:
        current_text += char
        if count_tokens(current_text) >= token_limit:
            texts.append(current_text)
            current_text = ""

    if current_text:
        texts.append(current_text)

    return texts



class AiProblemDto: #문제 input
    def __init__(self, text, amount, difficulty):
        self.text = text
        self.amount = amount
        self.difficulty = difficulty
    

class AiResponseDto: #문제 output
    def __init__(self, problemName, problemCommentary, problemAnswer, problemChoices = None):
        self.problemName = problemName #문제
        self.problemChoices = problemChoices #객관식은 있어야하고, 주관식은 없어도 됨
        self.problemAnswer = problemAnswer
        self.problemCommentary = problemCommentary
        
         

@app.route('/create/problem/mcq', methods=['POST']) #객관식
def prompt1():
    try:
        data = request.json
        problem_mcq = {
        "type": "object",
        "properties": {
            "problemName": {
            "type": "string",
            "description": "의문문 형식의 문제명"
            },
            "problemChoices": {
            "type": "array",
            "items": {
                "type": "object",
                "description": "option의 갯수는 무조건 4개이어야 해",
                "properties": { 
                "1": {
                    "type": "string",
                    "description": "The OPTION A of the question.",
                },
                "2": {
                    "type": "string",
                    "description": "The OPTION B of the question.",
                },
                "3": {
                    "type": "string",
                    "description": "The OPTION C of the question.",
                },
                "4": {
                    "type": "string",
                    "description": "The OPTION D of the question.",
                },
                },
                "required": ["1", "2", "3", "4"]
            }
            },
            "problemAnswer": {
            "type": "string",
            "description": "선지에서 하나의 정답만 골라줘"
            },
            "problemCommentary": {
            "type": "string",
            "description": "문제의 정답에 대한 해설을 알려줘"
            },
        },
        "required": ["problemName", "problemChoices", "problemAnswer", "problemCommentary"]
        }
       
        ai_mcq_problem_dto = AiProblemDto(
        text=data.get('text'),
        amount=data.get('amount'),
        difficulty=data.get('difficulty')
        )
           
        if ai_mcq_problem_dto.amount == "MANY" : MAX_TOKEN= 300
        elif ai_mcq_problem_dto.amount== "MEDIUM" : MAX_TOKEN = 450
        elif  ai_mcq_problem_dto.amount == "FEW" : MAX_TOKEN = 550

        if ai_mcq_problem_dto.difficulty == "HARD" : ai_mcq_problem_dto.difficulty = "어려운"
        elif ai_mcq_problem_dto.difficulty == "MODERATE" : ai_mcq_problem_dto.difficulty = "basic한"
        elif ai_mcq_problem_dto.difficulty == "EASY" : ai_mcq_problem_dto.difficulty = "쉬운"
        ai_mcq_response_list =[]
        
        sys_prompt = """너는 입력 내용을 기반으로 객관식 문제를 만들어야 하는 시스템이야. 
문제를 푸는 사람은 대학교 1학년 학생이야.
너의 임무는 다음과 같아.
임무1 선지는 입력 내용의 중요한 내용을 포함해야 한다. 
임무2 선지마다 질문의 내용이 하나의 사실을 묻도록 해야 한다. 
임무3 문제명과 선지가 간결하고 명확해야 한다.
임무4 명확한 오답 선지를 만들어야 한다.
임무5 각 선지의 내용이 상호 독립적이어야 한다. 
임무6 각 선지의 형태를 유사하게 한다.
임무7 선지에 논리적 순서가 있으면 그 순서에 따라 배열한다. 
임무8 선지의 개수는 반드시 4개이어야한다
임무9 자연스럽고 인간적인 방식으로 문제를 생성해 
임무10 문제명을 생각하고 그에 대한 선지가 주제에 맞는지 생각하고 그에 대한 답과 해설을 만들어줘 
임무11 문제를 영어가 아닌 한글로 문제를 만들어야 돼
임무12 문제명은 동사로 끝나야한다.
너가 지켜야 할 객관식의 유형은 다음과 같아
유형1 단순히 어떤 문장들의 참·거짓을 판단하는 진위형 
유형2 알맞은 것을 고르는 정답형
유형3 틀린 것을 고르는 부정형 문제
유형4 간단히 답을 제시하는 단답형과 완결형
위 임무와 객관식 유형을 반드시 지켜서 문제를 만들어주는게 너의 역할이야.
위 임무를 모두 지키면 200달러 팁을 줄꺼야. 지키지 못할 시 너에게 처벌을 줄꺼야."""
        text_chunks = split_token(ai_mcq_problem_dto.text, MAX_TOKEN)
        for i in range(len(text_chunks)):
            prompt = "' " +text_chunks[i] + f"'의 내용기반으로 {ai_mcq_problem_dto.difficulty} 객관식 문제 만들어줘 "
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-0613",
                messages=[
                    {
                        "role": "system",
                        "content": sys_prompt
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                functions=[{
                    "name": "get_new_quiz",
                    "description": "요청한 내용을 기반으로 객관식 문제 만들어줘 빈칸이 있으면 안돼",
                    "parameters": problem_mcq
                }],
                function_call={
                    "name": "get_new_quiz"
                },
                # temperature= 1.1,
                # top_p= 0.7,
                # frequency_penalty= 1,
                # presence_penalty= 0.8,
                max_tokens= 1024
                )

            gpt_response = json.loads(response["choices"][0]["message"]["function_call"]["arguments"])
            gpt_response['problemChoices'] = list(gpt_response ['problemChoices'].values())
            ai_mcq_response_list.append(AiResponseDto(problemName=gpt_response['problemName'], 
            problemChoices=gpt_response['problemChoices'], problemAnswer= gpt_response['problemAnswer'],  problemCommentary=gpt_response['problemCommentary']))

        mcq_json_response = [
            {
                "problemName": item.problemName,
                "problemChoices": item.problemChoices,
                "problemAnswer": item.problemAnswer,
                "problemCommentary": item.problemCommentary
            }
            for item in ai_mcq_response_list ]
       
        print(mcq_json_response)

        return jsonify(mcq_json_response)
    except Exception as e:
         return jsonify({"error": str(e)}), 400
    
    
    
@app.route('/create/problem/saq', methods=['POST']) #주관식
def prompt2():
    try:
        saq_data = request.json
        ai_saq_response_list = []
        ai_saq_problem_dto = AiProblemDto(
            text=saq_data.get('text'),
            amount=saq_data.get('amount'),
            difficulty=saq_data.get('difficulty')
        )

        if ai_saq_problem_dto.amount == "MANY" : MAX_TOKEN = 300
        elif ai_saq_problem_dto.amount== "MEDIUM" : MAX_TOKEN = 500
        elif  ai_saq_problem_dto.amount == "FEW" : MAX_TOKEN = 600

        if ai_saq_problem_dto.difficulty == "HARD" : ai_saq_problem_dto.difficulty = "어려운"
        elif ai_saq_problem_dto.difficulty == "MODERATE" : ai_saq_problem_dto.difficulty = "basic한"
        elif ai_saq_problem_dto.difficulty == "EASY" : ai_saq_problem_dto.difficulty = "쉬운"

        problem_saq = {
        "type": "object",
        "properties": {
            "problemName": {
            "type": "string",
            "description": "의문문 형식의 문제명"
            },
            "problemAnswer": {
            "type": "string",
            "description": "문제에 대한 정답"
            },
            "problemCommentary": {
            "type": "string",
            "description": "문제의 정답에 대한 해설"
            },
        },
        "required": ["problemName", "problemAnswer", "problemCommentary"]
        }

        ai_saq_response_list =[]

        # 텍스트를 토큰 제한에 맞게 분리
        text_chunks = split_token(ai_saq_problem_dto.text, MAX_TOKEN)


        for i in range(len(text_chunks)):
            prompt = "' " +text_chunks[i] + f"'의 내용기반으로 {ai_saq_problem_dto.difficulty} 주관식 문제 만들어줘 "
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-0613",
                messages=[
                    {
                        "role": "system",
                        "content": "너는 내용을 입력받으면 그 내용을 기반으로 주관식 문제를 만들어주는 시스템이야. 단 문제를 영어로 만들지 않고 한글로 문제를 만들어야 돼"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                functions=[{
                    "name": "get_new_quiz",
                    "description": "요청한 내용을 기반으로 문제 만들어줘 빈칸이 있으면 안돼",
                    "parameters": problem_saq
                }],
                function_call={
                    "name": "get_new_quiz"
                },
                # temperature= 1.1,
                # top_p= 0.7,
                # frequency_penalty= 1,
                # presence_penalty= 0.8,
                max_tokens= 1024
                )
            gpt_response = json.loads(response["choices"][0]["message"]["function_call"]["arguments"])
            ai_saq_response_list.append(AiResponseDto(problemName = gpt_response['problemName'], 
                        problemAnswer = gpt_response['problemAnswer'],  problemCommentary = gpt_response['problemCommentary']))
        
        saq_json_response = [
                    {
                        "problemName": item.problemName,
                        "problemAnswer": item.problemAnswer,
                        "problemCommentary": item.problemCommentary
                    }
                    for item in ai_saq_response_list ]  
        
        return jsonify(saq_json_response)
    except Exception as e:
         return jsonify({"error": str(e)}), 400
    

class AiSummaryDto: #요점정리 input
     def __init__(self, text, amount):
         self.text = text
         self.amount = amount
         
    
class AiSummaryResponseDto: #요점정리 output
     def __init__(self, summaryContent):
         self.summaryContent = summaryContent    

@app.route('/create/summary', methods=['POST']) #요점정리
def prompt3():
    try:
        data = request.json
        ai_response_list = []
        
        summary_schema = {
        "type": "object",
        "properties": {
            "summaryContent": {
            "type": "string",
            "description": "요점정리 내용"
            }
        },
        "required": ["summaryContent"]
        }


        ai_summary_dto = AiSummaryDto(
            text=data.get('text'),
            amount=data.get('amount'),
        )
        if ai_summary_dto.amount == "MANY" : MAX_TOKEN = 300
        elif ai_summary_dto.amount== "MEDIUM" : MAX_TOKEN = 500
        elif  ai_summary_dto.amount == "FEW" : MAX_TOKEN = 600

        text_chunks = split_token(ai_summary_dto.text, MAX_TOKEN)


        for i in range(len(text_chunks)):
            prompt = "' " +text_chunks[i] + f"'의 내용기반으로 요점 정리 해줘 "
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-0613",
                messages=[
                    {
                        "role": "system",
                        "content": "너는 내용을 입력받으면 그 내용을 기반으로 요점정리를 만들어주는 시스템이야. 단 요점정리를 영어로 만들지 않고 한글로 만들어야 돼"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                functions=[{
                    "name": "summary",
                    "description": "요청한 내용을 기반으로 요점 정리해줘",
                    "parameters": summary_schema
                }],
                function_call={
                    "name": "summary"
                },
                # temperature= 1.1,
                # top_p= 0.7,
                # frequency_penalty= 1,
                # presence_penalty= 0.8,
                max_tokens= 1024
                )
            gpt_response = json.loads(response["choices"][0]["message"]["function_call"]["arguments"])
            
            gpt_response['summaryContent'] = ' '.join(gpt_response['summaryContent'].split('\n'))
            ai_response_list.append(AiSummaryResponseDto(summaryContent = gpt_response['summaryContent']))

            # Check the result
            json_response = [
                {
                    "summaryContent": item.summaryContent
                }
                for item in ai_response_list
            ]
            merged_json = " ".join(item["summaryContent"] for item in json_response)
            summary_result = {"summaryContent" : merged_json}
        return jsonify(summary_result)

    except Exception as e:
        return jsonify({"error": str(e)}), 400




# 이미지 
class AiGenerateProblemByFileDto:
    def __init__(self, files, amount, difficulty):
        self.amount = amount
        self.difficulty = difficulty
        self.files = files    
        
@app.route('/create/problem/mcq/jpg', methods=['POST']) #이미지 객관식
def prompt4():
    try:
        amount_rq = request.form.get('amount')
        difficulty_rq = request.form.get('difficulty')
        img_files = request.files.getlist('files')
        problem_mcq = {
        "type": "object",
        "properties": {
            "problemName": {
            "type": "string",
            "description": "의문문 형식의 문제명"
            },
            "problemChoices": {
            "type": "array",
            "items": {
                "type": "object",
                "description": "option의 갯수는 무조건 4개이어야 해",
                "properties": { 
                "1": {
                    "type": "string",
                    "description": "The OPTION A of the question.",
                },
                "2": {
                    "type": "string",
                    "description": "The OPTION B of the question.",
                },
                "3": {
                    "type": "string",
                    "description": "The OPTION C of the question.",
                },
                "4": {
                    "type": "string",
                    "description": "The OPTION D of the question.",
                },
                },
                "required": ["1", "2", "3", "4"]
            }
            },
            "problemAnswer": {
            "type": "string",
            "description": "선지에서 하나의 정답만 골라줘"
            },
            "problemCommentary": {
            "type": "string",
            "description": "문제의 정답에 대한 해설을 알려줘"
            },
        },
        "required": ["problemName", "problemChoices", "problemAnswer", "problemCommentary"]
        }
       
        ai_mcq_img_dto = AiGenerateProblemByFileDto(
        files = img_files,
        amount= amount_rq,
        difficulty=difficulty_rq
        )
           
        if ai_mcq_img_dto.amount == "MANY" : MAX_TOKEN= 400
        elif ai_mcq_img_dto.amount== "MEDIUM" : MAX_TOKEN = 500
        elif  ai_mcq_img_dto.amount == "FEW" : MAX_TOKEN = 600

        if ai_mcq_img_dto.difficulty == "HARD" :ai_mcq_img_dto.difficulty = "어려운"
        elif ai_mcq_img_dto.difficulty == "MODERATE" : ai_mcq_img_dto.difficulty = "basic한"
        elif ai_mcq_img_dto.difficulty == "EASY" : ai_mcq_img_dto.difficulty = "쉬운"
        
        ocr_result_list = []
        reader = easyocr.Reader(['ko','en'], gpu=False)
        print("num of img")
        print(len(ai_mcq_img_dto.files))
        print("ai_mcq_img_dto.amount : "+ai_mcq_img_dto.amount)
        print("ai_mcq_img_dto.difficulty  : "+ ai_mcq_img_dto.difficulty)
        for file in ai_mcq_img_dto.files:
            image = Image.open(BytesIO(file.read()))
            image = np.array(image)
            ocr_result = reader.readtext(image, detail=0)
            result_merge = ' '.join(ocr_result)
            ocr_result_list.append(result_merge)
   
        result_text = ' '.join(ocr_result_list) 
        
        ai_mcq_img_list =[]
        
        sys_prompt = """너는 입력 내용을 기반으로 객관식 문제를 만들어야 하는 시스템이야. 
문제를 푸는 사람은 대학교 1학년 학생이야.
너의 임무는 다음과 같아.
임무1 선지는 입력 내용의 중요한 내용을 포함해야 한다. 
임무2 선지마다 질문의 내용이 하나의 사실을 묻도록 해야 한다. 
임무3 문제명과 선지가 간결하고 명확해야 한다.
임무4 명확한 오답 선지를 만들어야 한다.
임무5 각 선지의 내용이 상호 독립적이어야 한다. 
임무6 각 선지의 형태를 유사하게 한다.
임무7 선지에 논리적 순서가 있으면 그 순서에 따라 배열한다. 
임무8 선지의 개수는 반드시 4개이어야한다
임무9 자연스럽고 인간적인 방식으로 문제를 생성해 
임무10 문제명을 생각하고 그에 대한 선지가 주제에 맞는지 생각하고 그에 대한 답과 해설을 만들어줘 
임무11 문제를 영어가 아닌 한글로 문제를 만들어야 돼
너가 지켜야 할 객관식의 유형은 다음과 같아
유형1 단순히 어떤 문장들의 참·거짓을 판단하는 진위형 
유형2 알맞은 것을 고르는 정답형
유형3 틀린 것을 고르는 부정형 문제
유형4 간단히 답을 제시하는 단답형과 완결형
위 임무와 객관식 유형을 반드시 지켜서 문제를 만들어주는게 너의 역할이야.
위 임무를 모두 지키면 200달러 팁을 줄꺼야. 지키지 못할 시 너에게 처벌을 줄꺼야."""

        text_chunks = split_token(result_text, MAX_TOKEN)
        for i in range(len(text_chunks)):
            prompt = "' " +text_chunks[i] + f"'의 내용기반으로 {ai_mcq_img_dto.difficulty} 객관식 문제 만들어줘 "
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-0613",
                messages=[
                    {
                        "role": "system",
                        "content": sys_prompt
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                functions=[{
                    "name": "get_new_quiz",
                    "description": "요청한 내용을 기반으로 객관식 문제 만들어줘 빈칸이 있으면 안돼",
                    "parameters": problem_mcq
                }],
                function_call={
                    "name": "get_new_quiz"
                },
                # temperature= 1.1,
                # top_p= 0.7,
                # frequency_penalty= 1,
                # presence_penalty= 0.8,
                max_tokens= 1024
                )

            gpt_response = json.loads(response["choices"][0]["message"]["function_call"]["arguments"])
            gpt_response['problemChoices'] = list(gpt_response ['problemChoices'].values())
            ai_mcq_img_list.append(AiResponseDto(problemName=gpt_response['problemName'], 
            problemChoices=gpt_response['problemChoices'], problemAnswer= gpt_response['problemAnswer'],  problemCommentary=gpt_response['problemCommentary']))

        mcq_json_response = [
            {
                "problemName": item.problemName,
                "problemChoices": item.problemChoices,
                "problemAnswer": item.problemAnswer,
                "problemCommentary": item.problemCommentary
            }
            for item in ai_mcq_img_list ]
       
        print(mcq_json_response)

        return jsonify(mcq_json_response)
    except Exception as e:
         return jsonify({"error": str(e)}), 400
    
# 이미지 주관식
@app.route('/create/problem/saq/jpg', methods=['POST']) 
def prompt5():
    try:
        amount_rq = request.form.get('amount')
        difficulty_rq = request.form.get('difficulty')
        img_files = request.files.getlist('files')

        ai_saq_img_dto = AiGenerateProblemByFileDto(
                files = img_files,
                amount= amount_rq,
                difficulty=difficulty_rq
             )

        if ai_saq_img_dto.amount == "MANY" : MAX_TOKEN = 400
        elif ai_saq_img_dto.amount== "MEDIUM" : MAX_TOKEN = 500
        elif  ai_saq_img_dto.amount == "FEW" : MAX_TOKEN = 600


        if ai_saq_img_dto.difficulty == "HARD" : ai_saq_img_dto.difficulty = "어려운"
        elif ai_saq_img_dto.difficulty == "MODERATE" : ai_saq_img_dto.difficulty = "basic한"
        elif ai_saq_img_dto.difficulty == "EASY" : ai_saq_img_dto.difficulty = "쉬운"

        problem_saq = {
        "type": "object",
        "properties": {
            "problemName": {
            "type": "string",
            "description": "의문문 형식의 문제명"
            },
            "problemAnswer": {
            "type": "string",
            "description": "문제에 대한 정답"
            },
            "problemCommentary": {
            "type": "string",
            "description": "문제의 정답에 대한 해설"
            },
        },
        "required": ["problemName", "problemAnswer", "problemCommentary"]
        }

        ai_saq_img_list =[]

       
    

        ocr_result_list = []
        reader = easyocr.Reader(['ko','en'], gpu=False)
        print("num of img")
        print(len(ai_saq_img_dto.files))
        print("ai_saq_img_dto.amount : "+ai_saq_img_dto.amount)
        print("ai_saq_img_dto.difficulty  : "+ ai_saq_img_dto.difficulty)
        for file in ai_saq_img_dto.files:
            image = Image.open(BytesIO(file.read()))
            image = np.array(image)
            ocr_result = reader.readtext(image, detail=0)
            result_merge = ' '.join(ocr_result)
            ocr_result_list.append(result_merge)
   
        result_text = ' '.join(ocr_result_list) 
         # 텍스트를 토큰 제한에 맞게 분리
        text_chunks = split_token(result_text, MAX_TOKEN)

        for i in range(len(text_chunks)):
            prompt = "' " +text_chunks[i] + f"'의 내용기반으로 {ai_saq_img_dto.difficulty} 주관식 문제 만들어줘 "
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-0613",
                messages=[
                    {
                        "role": "system",
                        "content": "너는 내용을 입력받으면 그 내용을 기반으로 주관식 문제를 만들어주는 시스템이야. 단 문제를 영어로 만들지 않고 한글로 문제를 만들어야 돼"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                functions=[{
                    "name": "get_new_quiz",
                    "description": "요청한 내용을 기반으로 문제 만들어줘 빈칸이 있으면 안돼",
                    "parameters": problem_saq
                }],
                function_call={
                    "name": "get_new_quiz"
                },
                # temperature= 1.1,
                # top_p= 0.7,
                # frequency_penalty= 1,
                # presence_penalty= 0.8,
                max_tokens= 1024
                )
            gpt_response = json.loads(response["choices"][0]["message"]["function_call"]["arguments"])
            ai_saq_img_list.append(AiResponseDto(problemName = gpt_response['problemName'], 
                        problemAnswer = gpt_response['problemAnswer'],  problemCommentary = gpt_response['problemCommentary']))
        
        saq_json_response = [
                    {
                        "problemName": item.problemName,
                        "problemAnswer": item.problemAnswer,
                        "problemCommentary": item.problemCommentary
                    }
                    for item in ai_saq_img_list ]  
        
        return jsonify(saq_json_response)
    except Exception as e:
         return jsonify({"error": str(e)}), 400

class AiSummaryJPGDto: #요점정리 input
     def __init__(self, files, amount):
         self.files = files
         self.amount = amount


@app.route('/create/summary/jpg', methods=['POST']) #이미지 요점정리
def prompt6():
    try:
        amount_rq = request.form.get('amount')
        img_files = request.files.getlist('files')
        
        ai_response_list = []
        
        summary_schema = {
        "type": "object",
        "properties": {
            "summaryContent": {
            "type": "string",
            "description": "요점정리 내용"
            }
        },
        "required": ["summaryContent"]
        }


        ai_img_summary_dto = AiSummaryJPGDto(
            files=img_files,
            amount=amount_rq
        )
        if  ai_img_summary_dto.amount == "MANY" : MAX_TOKEN = 400
        elif  ai_img_summary_dto.amount== "MEDIUM" : MAX_TOKEN = 500
        elif   ai_img_summary_dto.amount == "FEW" : MAX_TOKEN = 600

        ocr_result_list = []
        reader = easyocr.Reader(['ko','en'], gpu=False)
        print("num of img")
        print(len( ai_img_summary_dto.files))
        print("ai_img_summary_dto.amount : " + ai_img_summary_dto.amount)

        for file in  ai_img_summary_dto.files:
            image = Image.open(BytesIO(file.read()))
            image = np.array(image)
            ocr_result = reader.readtext(image, detail=0)
            result_merge = ' '.join(ocr_result)
            ocr_result_list.append(result_merge)
   
        result_text = ' '.join(ocr_result_list) 

        text_chunks = split_token(result_text, MAX_TOKEN)


        for i in range(len(text_chunks)):
            prompt = "' " +text_chunks[i] + f"'의 내용기반으로 요점 정리 해줘 "
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-0613",
                messages=[
                    {
                        "role": "system",
                        "content": "너는 내용을 입력받으면 그 내용을 기반으로 요점정리를 만들어주는 시스템이야. 단 요점정리를 영어로 만들지 않고 한글로 만들어야 돼"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                functions=[{
                    "name": "summary",
                    "description": "요청한 내용을 기반으로 요점 정리해줘",
                    "parameters": summary_schema
                }],
                function_call={
                    "name": "summary"
                },
                # temperature= 1.1,
                # top_p= 0.7,
                # frequency_penalty= 1,
                # presence_penalty= 0.8,
                max_tokens= 1024
                )
            gpt_response = json.loads(response["choices"][0]["message"]["function_call"]["arguments"])
            
            gpt_response['summaryContent'] = ' '.join(gpt_response['summaryContent'].split('\n'))
            ai_response_list.append(AiSummaryResponseDto(summaryContent = gpt_response['summaryContent']))

            # Check the result
            json_response = [
                {
                    "summaryContent": item.summaryContent
                }
                for item in ai_response_list
            ]

            merged_json = " ".join(item["summaryContent"] for item in json_response)
            summary_jpg_result = {"summaryContent" : merged_json}
        return jsonify(summary_jpg_result)

    except Exception as e:
        return jsonify({"error": str(e)}), 400



if __name__ == '__main__':
    from waitress import serve
    print("server stating....")
    serve(app, host='0.0.0.0', port=5000)
