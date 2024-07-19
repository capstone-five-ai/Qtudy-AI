# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
import openai
import tiktoken
import json
from PIL import Image
import numpy as np
import ast
from io import BytesIO
import re
import pytesseract
import random
app = Flask(__name__)



def cleansing_token(input):
    input = re.sub(r'\n', ' ', input)
    input = re.sub(r'\s{2,}', ' ', input)
    input = re.sub(r'[^ㄱ-ㅎ가-힣a-zA-Z0-9\s!$%^&*+-=/?\,()[\]{}:]', '', input)
    return input

def count_tokenizer(text):
    tokenizer = tiktoken.get_encoding("cl100k_base")
    tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo") 
    return len(tokenizer.encode(text))

def get_token_limit(token_count, level):
    limits = [
        (0, 50,      {'MANY': 10, 'MEDIUM': 15, 'FEW': 20}),
        (50, 100,    {'MANY': 20, 'MEDIUM': 30, 'FEW': 40}),
        (100, 200,   {'MANY': 20, 'MEDIUM': 30, 'FEW': 40}),
        (200, 300,   {'MANY': 30, 'MEDIUM': 40, 'FEW': 50}),
        (300, 400,   {'MANY': 40, 'MEDIUM': 50, 'FEW': 60}),
        (400, 500,   {'MANY': 50, 'MEDIUM': 65, 'FEW': 80}),
        (500, 600,   {'MANY': 60, 'MEDIUM': 75, 'FEW': 90}),
        (600, 700,   {'MANY': 70, 'MEDIUM': 85, 'FEW': 100}),
        (700, 800,   {'MANY': 90, 'MEDIUM': 110, 'FEW': 130}),
        (800, 900,   {'MANY': 100, 'MEDIUM': 130, 'FEW': 160}),
        (900, 1000,  {'MANY': 100, 'MEDIUM': 130, 'FEW': 160}),
        (1000, 1500, {'MANY': 150, 'MEDIUM': 170, 'FEW': 200}),
        (1500, 2000, {'MANY': 200, 'MEDIUM': 250, 'FEW': 300}),
        (2000, 2500, {'MANY': 200, 'MEDIUM': 250, 'FEW': 300}),
        (2500, 3000, {'MANY': 240, 'MEDIUM': 280, 'FEW': 350}),
        (3000, 4000, {'MANY': 300, 'MEDIUM': 350, 'FEW': 400}),
        (4000, 5000, {'MANY': 350, 'MEDIUM': 380, 'FEW': 430}),
        (5000, 6000, {'MANY': 400, 'MEDIUM': 450, 'FEW': 500}),
        (6000, 7000, {'MANY': 450, 'MEDIUM': 500, 'FEW': 600}),
        (7000, 10000,{'MANY': 500, 'MEDIUM': 600, 'FEW': 700})
    ]

    for limit in limits:
        if limit[0] <= token_count < limit[1]:
            return limit[2][level]

    return None


def word_split(text, token_limit):
    words = text.split(' ')
    current_text = ""
    texts = []

    for word in words:
        if count_tokenizer(current_text + ' ' + word) > token_limit:
            if current_text:
                texts.append(current_text)
            current_text = word
        else:
            if current_text:
                current_text += ' '
            current_text += word

    if current_text:
        texts.append(current_text)

    return texts
    
def split_tokenizer(text, level):
    token_count = count_tokenizer(text)
    if token_count <= 10000:
        token_limit = get_token_limit(token_count, level)
        split_text = word_split(text, token_limit)
    else:
        token_limit = 500
        split_text = word_split(text, token_limit)
        if level == "MANY":
            selected_indexes = sorted(random.sample(range(len(split_text)), 20))
            split_text = [split_text[i] for i in selected_indexes]
            
        elif level == "MEDIUM":
            selected_indexes = sorted(random.sample(range(len(split_text)), 15))
            split_text = [split_text[i] for i in selected_indexes]
            
        elif level == "FEW":
            selected_indexes = sorted(random.sample(range(len(split_text)), 12))
            split_text = [split_text[i] for i in selected_indexes]
             
    return split_text


class AiSummaryJPGDto: # 이미지 요점정리
     def __init__(self, files, amount):
         self.files = files
         self.amount = amount

class AiGenerateProblemByFileDto: # 이미지 문제생성
    def __init__(self, files, amount, difficulty):
        self.amount = amount
        self.difficulty = difficulty
        self.files = files    

class AiSummaryDto: #요점정리 input
     def __init__(self, text, amount):
         self.text = text
         self.amount = amount
         
    
class AiSummaryResponseDto: #요점정리 output
     def __init__(self, summaryContent):
         self.summaryContent = summaryContent 

class AiProblemDto: #문제생성 input
    def __init__(self, text, amount, difficulty):
        self.text = text
        self.amount = amount
        self.difficulty = difficulty
    

class AiResponseDto: #문제생성 output
    def __init__(self, problemName, problemCommentary, problemAnswer = None, problemChoices = None):
        self.problemName = problemName 
        self.problemChoices = problemChoices 
        self.problemAnswer = problemAnswer
        self.problemCommentary = problemCommentary


@app.route('/create/problem/mcq', methods=['POST']) #객관식
def prompt1():
    try:
        ai_mcq_response_list =[]

        mcq_data = request.json
        ai_mcq_problem_dto = AiProblemDto(
        text=mcq_data.get('text'),
        amount=mcq_data.get('amount'),
        difficulty=mcq_data.get('difficulty')
        )

        if ai_mcq_problem_dto.difficulty == "HARD" : 
            temperature_num = 0.1
            top_p_num = 0.1
        elif ai_mcq_problem_dto.difficulty == "MODERATE" :
            temperature_num = 0.2
            top_p_num = 0.2
        elif ai_mcq_problem_dto.difficulty == "EASY" : 
            temperature_num = 0.2
            top_p_num = 0.2

        mcq_system_msg = "너는 입력 내용을 기반으로 n개의 객관식 문제를 만들어야 하는 시스템이야. 문제를 푸는 사람은 대학교 1학년 학생이야. 너의 임무는 다음과 같아. 임무1 선지는 중요한 학습 내용을 포함해야 한다. 임무2 선지마다 질문의 내용이 하나의 사실을 묻도록 해야 한다. 임무3 문제명과 선지가 간결하고 명확해야 한다. 임무4 명확한 오답 선지를 만들어야 한다. 임무5 각 선지의 내용이 상호 독립적이어야 한다. 임무6 각 선지의 형태를 유사하게 한다. 임무7 선지에 논리적 순서가 있으면 그 순서에 따라 배열한다. 임무8 선지의 개수는 반드시 4개이어야한다 임무9 자연스럽고 인간적인 방식으로 문제를 생성해 임무10 문제명을 생각하고 그에 대한 선지가 주제에 맞는지 생각하고 그에 대한 답과 해설을 만들어줘 너가 지켜야 할 객관식의 유형은 다음과 같아 유형1 단순히 어떤 문장들의 참·거짓을 판단하는 진위형 유형2 알맞은 것을 고르는 정답형 유형3 틀린 것을 고르는 부정형 문제 유형4 간단히 답을 제시하는 단답형과 완결형 위 임무와 객관식 유형을 반드시 지켜서 문제를 만들어주는게 너의 역할이야. 위 임무를 모두 지키면 200달러 팁을 줄꺼야. 지키지 못할 시 너에게 처벌을 줄꺼야."
        cleansing_text = cleansing_token(ai_mcq_problem_dto.text)
        print(cleansing_text)
        text_chunks = split_tokenizer(cleansing_text, ai_mcq_problem_dto.amount)
        

        count= 0
        break_count = 0
        success = False
        tries=0
        while not success and tries < 4:
            try:
                count = break_count
                for i in range(count, len(text_chunks)):
                    prompt = text_chunks[i]
                    print(prompt)
                    
                    break_count = i
                    mcq_response = openai.ChatCompletion.create(
                        model="ft:gpt-3.5-turbo-0125:daewon-jaehyun:mcq2:9CTW4TU7",
                        messages=[
                            {
                                "role": "system",
                                "content": mcq_system_msg
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        # temperature= temperature_num,
                        # top_p= top_p_num,
                        # frequency_penalty= 1,
                        # presence_penalty= 0.8,
                        max_tokens= 1024
                        )
                    
                    mcq_result = mcq_response.choices[0]['message']['content']
                    print( mcq_result)
                    mcq_problemName = cleansing_token(re.search(r'문제명: (.*?) 선지:', mcq_result).group(1))
                    choices = re.search(r'선지: (.*?) 해설:', mcq_result).group(1)
                    mcq_problemCommentary = cleansing_token(re.search(r'해설: (.*?) 정답:', mcq_result).group(1))
                    mcq_problemAnswer = cleansing_token(re.search(r'정답: (\d+)', mcq_result).group(1))           
                    mcq_problemchoices = ast.literal_eval(choices)
                    ai_mcq_response_list.append(AiResponseDto(problemName = mcq_problemName, problemChoices=mcq_problemchoices,
                                problemAnswer = mcq_problemAnswer,  problemCommentary = mcq_problemCommentary))
                    
                    tries = 0 
                success = True
            except Exception:
                tries += 1
                
                print(tries, "번째 시도")
                if tries > 3 and len(text_chunks) > break_count+1: 
                  break_count+= 1
                  tries = 0 

        mcq_json_response = [
            {
                "problemName": item.problemName,
                "problemChoices": item.problemChoices,
                "problemAnswer": item.problemAnswer,
                "problemCommentary": item.problemCommentary
            }
            for item in ai_mcq_response_list ]

            
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

        if ai_saq_problem_dto.difficulty == "HARD" : 
            temperature_num = 0.1
            top_p_num = 0.1
        elif ai_saq_problem_dto.difficulty == "MODERATE" : 
            temperature_num = 0.1
            top_p_num = 0.1
        elif ai_saq_problem_dto.difficulty == "EASY" : 
            temperature_num = 0.1
            top_p_num = 0.1

        saq_system_msg = "너는 입력 내용을 기반으로 n개의 주관식 문제를 만들어야 하는 시스템이야. 문제를 푸는 사람은 대학교 1학년 학생이야. 너의 임무는 다음과 같아. 임무1 문제는 중요한 학습 내용을 포함해야 한다. 임무2 문제마다 질문의 내용이 하나의 사실을 묻도록 해야 한다. 임무3 문제는 간결하고 명확해야 한다. 임무4 각 문제의 내용이 상호 독립적이어야 한다. 임무5 각 문제의 형태를 유사하게 한다. 임무6 자연스럽고 인간적인 방식으로 문제를 생성해야 한다. 위 임무를 반드시 지켜서 문제를 만드는게 너의 역할이야. 위 임무를 모두 지키면 209달러 팁을 줄꺼야. 지키지 못할 시 너에게 처벌을 줄꺼야."
        cleansing_text = cleansing_token(ai_saq_problem_dto.text)
        text_chunks = split_tokenizer(cleansing_text, ai_saq_problem_dto.amount)
        
        success = False
        count= 0
        break_count = 0
        tries=0
        while not success and tries < 5:
            try:
                count = break_count
                for i in range(count, len(text_chunks)):
                    prompt = text_chunks[i]
                    break_count = i 
                    saq_response = openai.ChatCompletion.create(
                        model="ft:gpt-3.5-turbo-0125:daewon-jaehyun:saq2:9CTB2UsE",
                        messages=[
                            {
                                "role": "system",
                                "content": saq_system_msg
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        temperature= temperature_num,
                        top_p= top_p_num,
                        # frequency_penalty= 1,
                        # presence_penalty= 0.8,
                        max_tokens= 1024
                        )
                    
                    saq_result = saq_response.choices[0]['message']['content']
                    
                    splited_txt = saq_result.split('정답: ')
                    problem_name = splited_txt[0]
                    saq_problemNname = problem_name[5:]
                    saq_problemAnswer = splited_txt[1]
                    ai_saq_response_list.append(AiResponseDto(problemName = cleansing_token(saq_problemNname), problemCommentary = cleansing_token(saq_problemAnswer)))
                   
                    tries = 0 
                success = True
            except Exception:
                tries += 1
                # 똑같은 지문이 똑같은 에러를 계속 발생했을때 그 지문을 pass하는 경우 -> 3번 기회주고 똑같은 에러가 계속 발생하면 pass 
                print(tries, "번째 시도")
                if tries > 3 and len(text_chunks) > break_count+1: 
                  break_count+= 1
                  tries = 0 
                
        
        saq_json_response = [
                    {
                        "problemName": item.problemName,
                        "problemCommentary": item.problemCommentary
                    }
                    for item in ai_saq_response_list ]  

        return jsonify(saq_json_response )
    except Exception as e:
         return jsonify({"error": str(e)}), 400
    

@app.route('/create/summary', methods=['POST']) #요점정리
def prompt3():
    try:
        summary_data = request.json
        ai_summary_response_list = []
        


        ai_summary_dto = AiSummaryDto(
            text=summary_data.get('text'),
            amount=summary_data.get('amount'),
        )

        cleansing_text = cleansing_token(ai_summary_dto.text)
        text_chunks = split_tokenizer(cleansing_text, ai_summary_dto.amount)
        
        
        summary_system_msg = "너는 입력 내용을 기반으로 입력 내용의 요점을 정리하는 시스템이야. 너의 임무는 다음과 같아. 임무 1 입력 내용의 중요한 내용을 포함해야 한다. 임무 2 정리한 내용의 각 문장은 간결하고 명확해야 한다. 임무 3 자연스럽고 인간적인 방식으로 문장을 생성해야 한다. 위 임무를 반드시 지켜서 문제를 만드는게 너의 역할이야. 위 임무를 모두 지키면 200달러 팁을 줄거야. 지키지 못할 시 너에게 처벌을 줄거야."
    
        success = False
        count= 0
        break_count = 0
        tries=0
        while not success and tries < 4:
            try:
                count = break_count
                for i in range(count,len(text_chunks)):
                    prompt = text_chunks[i]
                    break_count = i 
                    summary_response = openai.ChatCompletion.create(
                        model="ft:gpt-3.5-turbo-0125:daewon-jaehyun:summary:9CPeuoZj",
                        messages=[
                            {
                                "role": "system",
                                "content": summary_system_msg
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        temperature= 0.4,
                        top_p= 0.7,
                        # frequency_penalty= 1,
                        # presence_penalty= 0.8,
                        max_tokens= 1024
                        )
                    summary_result = summary_response.choices[0]['message']['content']
                    ai_summary_response_list.append(AiSummaryResponseDto(summaryContent = cleansing_token(summary_result)))
                    
                    tries = 0
                success = True
            except Exception:
                tries += 1
                # 똑같은 지문이 똑같은 에러를 계속 발생했을때 그 지문을 pass하는 경우 -> 3번 기회주고 똑같은 에러가 계속 발생하면 pass 
                print(tries, "번째 시도")
                if tries > 3 and len(text_chunks) > break_count+1: 
                  break_count+= 1
                  tries = 0 
        sum_summary_txt = ''
        for i in range(len(ai_summary_response_list)):
            sum_summary_txt += ai_summary_response_list[i].summaryContent


        summary_json_response = { "summaryContent": sum_summary_txt}
 
        return jsonify(summary_json_response)

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/create/problem/mcq/jpg', methods=['POST']) #객관식
def prompt4():
    try:
        ocr_mcq_response_list =[]
        mcq_ocr_result_list=[]

        amount_rq = request.form.get('amount')
        difficulty_rq = request.form.get('difficulty')
        img_files = request.files.getlist('files')
        
        ai_mcq_img_dto = AiGenerateProblemByFileDto(
        files = img_files,
        amount= amount_rq,
        difficulty=difficulty_rq
        )      

    

        if ai_mcq_img_dto.difficulty == "HARD" : 
            temperature_num = 0.1
            top_p_num = 0.1
        elif ai_mcq_img_dto.difficulty == "MODERATE" :
            temperature_num = 0.2
            top_p_num = 0.2
        elif ai_mcq_img_dto.difficulty == "EASY" : 
            temperature_num = 0.2
            top_p_num = 0.2

        for file in ai_mcq_img_dto.files:
            image = Image.open(BytesIO(file.read()))
            image = np.array(image)
            ocr_result = pytesseract.image_to_string(image, lang='kor+eng')
            result_merge = ' '.join(ocr_result)
            mcq_ocr_result_list.append(result_merge)
        
        result_text = ' '.join(mcq_ocr_result_list) 
        

        
        mcq_system_msg = "너는 입력 내용을 기반으로 n개의 객관식 문제를 만들어야 하는 시스템이야. 문제를 푸는 사람은 대학교 1학년 학생이야. 너의 임무는 다음과 같아. 임무1 선지는 중요한 학습 내용을 포함해야 한다. 임무2 선지마다 질문의 내용이 하나의 사실을 묻도록 해야 한다. 임무3 문제명과 선지가 간결하고 명확해야 한다. 임무4 명확한 오답 선지를 만들어야 한다. 임무5 각 선지의 내용이 상호 독립적이어야 한다. 임무6 각 선지의 형태를 유사하게 한다. 임무7 선지에 논리적 순서가 있으면 그 순서에 따라 배열한다. 임무8 선지의 개수는 반드시 4개이어야한다 임무9 자연스럽고 인간적인 방식으로 문제를 생성해 임무10 문제명을 생각하고 그에 대한 선지가 주제에 맞는지 생각하고 그에 대한 답과 해설을 만들어줘 너가 지켜야 할 객관식의 유형은 다음과 같아 유형1 단순히 어떤 문장들의 참·거짓을 판단하는 진위형 유형2 알맞은 것을 고르는 정답형 유형3 틀린 것을 고르는 부정형 문제 유형4 간단히 답을 제시하는 단답형과 완결형 위 임무와 객관식 유형을 반드시 지켜서 문제를 만들어주는게 너의 역할이야. 위 임무를 모두 지키면 200달러 팁을 줄꺼야. 지키지 못할 시 너에게 처벌을 줄꺼야."
        cleansing_text = cleansing_token(result_text)
        text_chunks = split_tokenizer(cleansing_text, ai_mcq_img_dto.amount)
      
        success = False
        count= 0
        break_count = 0
        tries=0

        while not success and tries < 4:
            try:
                count = break_count
                for i in range(count, len(text_chunks)):
                    prompt = text_chunks[i]
                    break_count = i
                    mcq_response = openai.ChatCompletion.create(
                        model="ft:gpt-3.5-turbo-0125:daewon-jaehyun:mcq2:9CTW4TU7",
                        messages=[
                            {
                                "role": "system",
                                "content": mcq_system_msg
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        temperature= temperature_num,
                        top_p= top_p_num,
                        # frequency_penalty= 1,
                        # presence_penalty= 0.8,
                        max_tokens= 1024
                        )
                    
                    mcq_result = mcq_response.choices[0]['message']['content']
                    mcq_problemName = cleansing_token(re.search(r'문제명: (.*?) 선지:', mcq_result).group(1))                   
                    choices = re.search(r'선지: (.*?) 해설:', mcq_result).group(1)
                    mcq_problemCommentary = cleansing_token(re.search(r'해설: (.*?) 정답:', mcq_result).group(1))
                    mcq_problemAnswer = cleansing_token(re.search(r'정답: (\d+)', mcq_result).group(1))                 
                    mcq_problemchoices = ast.literal_eval(choices)
                    ocr_mcq_response_list.append(AiResponseDto(problemName = mcq_problemName, problemChoices=mcq_problemchoices,
                                problemAnswer = mcq_problemAnswer,  problemCommentary = mcq_problemCommentary))
                    
                    tries = 0
                success = True
            except Exception:
                tries += 1
                # 똑같은 지문이 똑같은 에러를 계속 발생했을때 그 지문을 pass하는 경우 -> 3번 기회주고 똑같은 에러가 계속 발생하면 pass 
                print(tries, "번째 시도")
                if tries > 3 and len(text_chunks) > break_count+1: 
                  break_count+= 1
                  tries = 0 
        mcq_json_response = [
            {
                "problemName": item.problemName,
                "problemChoices": item.problemChoices,
                "problemAnswer": item.problemAnswer,
                "problemCommentary": item.problemCommentary
            }
            for item in ocr_mcq_response_list ]
            

            
        return jsonify(mcq_json_response)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    

@app.route('/create/problem/saq/jpg', methods=['POST']) #주관식
def prompt5():
    try:
        ai_saq_response_list = []
        saq_ocr_result_list =[]

        amount_rq = request.form.get('amount')
        difficulty_rq = request.form.get('difficulty')
        img_files = request.files.getlist('files')

        ai_saq_img_dto = AiGenerateProblemByFileDto(
                files = img_files,
                amount= amount_rq,
                difficulty=difficulty_rq
             )
        
        if ai_saq_img_dto.difficulty == "HARD" : 
            temperature_num = 0.1
            top_p_num = 0.1
        elif ai_saq_img_dto.difficulty == "MODERATE" : 
            temperature_num = 0.1
            top_p_num = 0.1
        elif ai_saq_img_dto.difficulty == "EASY" : 
            temperature_num = 0.1
            top_p_num = 0.1
        
        for file in ai_saq_img_dto.files:
            image = Image.open(BytesIO(file.read()))
            image = np.array(image)
            ocr_result = pytesseract.image_to_string(image, lang='kor+eng')
            result_merge = ' '.join(ocr_result)
            saq_ocr_result_list.append(result_merge)

        saq_ocr_result = ' '.join(saq_ocr_result_list) 
        
        saq_system_msg = "너는 입력 내용을 기반으로 n개의 주관식 문제를 만들어야 하는 시스템이야. 문제를 푸는 사람은 대학교 1학년 학생이야. 너의 임무는 다음과 같아. 임무1 문제는 중요한 학습 내용을 포함해야 한다. 임무2 문제마다 질문의 내용이 하나의 사실을 묻도록 해야 한다. 임무3 문제는 간결하고 명확해야 한다. 임무4 각 문제의 내용이 상호 독립적이어야 한다. 임무5 각 문제의 형태를 유사하게 한다. 임무6 자연스럽고 인간적인 방식으로 문제를 생성해야 한다. 위 임무를 반드시 지켜서 문제를 만드는게 너의 역할이야. 위 임무를 모두 지키면 209달러 팁을 줄꺼야. 지키지 못할 시 너에게 처벌을 줄꺼야."
        cleansing_text = cleansing_token(saq_ocr_result)
        text_chunks = split_tokenizer(cleansing_text, ai_saq_img_dto.amount)

        success = False
        count= 0
        break_count = 0
        tries=0
        while not success and tries < 4:
            try:
                count = break_count
                for i in range(count, len(text_chunks)):
                    prompt = text_chunks[i]
                    break_count = i
                    saq_response = openai.ChatCompletion.create(
                        model="ft:gpt-3.5-turbo-0125:daewon-jaehyun:saq2:9CTB2UsE",
                        messages=[
                            {
                                "role": "system",
                                "content": saq_system_msg
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        temperature= temperature_num,
                        top_p= top_p_num,
                        # frequency_penalty= 1,
                        # presence_penalty= 0.8,
                        max_tokens= 1024
                        )
                    saq_result = saq_response.choices[0]['message']['content']
                    splited_txt = saq_result.split('정답: ')
                    problem_name = splited_txt[0]
                    saq_problemNname = problem_name[5:]
                    saq_problemAnswer = splited_txt[1]
                    ai_saq_response_list.append(AiResponseDto(problemName = cleansing_token(saq_problemNname), problemCommentary = cleansing_token(saq_problemAnswer)))
                    
                    tries = 0
                success = True
            except Exception:
                tries += 1
                # 똑같은 지문이 똑같은 에러를 계속 발생했을때 그 지문을 pass하는 경우 -> 3번 기회주고 똑같은 에러가 계속 발생하면 pass 
                print(tries, "번째 시도")
                if tries > 3 and len(text_chunks) > break_count+1: 
                  break_count+= 1
                  tries = 0 
        saq_json_response = [
                    {
                        "problemName": item.problemName,
                        "problemCommentary": item.problemCommentary
                    }
                    for item in ai_saq_response_list ]  

        return jsonify(saq_json_response )
    except Exception as e:
         return jsonify({"error": str(e)}), 400
    

@app.route('/create/summary/jpg', methods=['POST']) #요점정리
def prompt6():
    try:
        amount_rq = request.form.get('amount')
        img_files = request.files.getlist('files')

        ai_summary_response_list = []
        summary_ocr_result_list = []

        ai_img_summary_dto = AiSummaryJPGDto(
            files=img_files,
            amount=amount_rq
        )
    

        for file in ai_img_summary_dto.files:
            image = Image.open(BytesIO(file.read()))
            image = np.array(image)
            ocr_result = pytesseract.image_to_string(image, lang='kor+eng')
            result_merge = ' '.join(ocr_result)
            summary_ocr_result_list.append(result_merge)

        summary_ocr_result = ' '.join(summary_ocr_result_list) 


        cleansing_text = cleansing_token(summary_ocr_result)
        text_chunks = split_tokenizer(cleansing_text,ai_img_summary_dto.amount)
       
        summary_system_msg = "너는 입력 내용을 기반으로 입력 내용의 요점을 정리하는 시스템이야. 너의 임무는 다음과 같아. 임무 1 입력 내용의 중요한 내용을 포함해야 한다. 임무 2 정리한 내용의 각 문장은 간결하고 명확해야 한다. 임무 3 자연스럽고 인간적인 방식으로 문장을 생성해야 한다. 위 임무를 반드시 지켜서 문제를 만드는게 너의 역할이야. 위 임무를 모두 지키면 200달러 팁을 줄거야. 지키지 못할 시 너에게 처벌을 줄거야."
        success = False
        count= 0
        break_count = 0
        tries=0
        
        while not success and tries < 4:           
            try:
                count = break_count
                for i in range(count,len(text_chunks)):
                    prompt = text_chunks[i]
                    print(prompt)
                    break_count = i
                    summary_response = openai.ChatCompletion.create(
                        model="ft:gpt-3.5-turbo-0125:daewon-jaehyun:summary:9CPeuoZj",
                        messages=[
                            {
                                "role": "system",
                                "content": summary_system_msg
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        temperature= 0.4,
                        top_p= 0.7,
                        # frequency_penalty= 1,
                        # presence_penalty= 0.8,
                        max_tokens= 1024
                        )
                    summary_result = summary_response.choices[0]['message']['content']
                    ai_summary_response_list.append(AiSummaryResponseDto(summaryContent = cleansing_token(summary_result)))
                    
                    tries = 0 
                success = True
            except Exception:
                tries += 1
                # 똑같은 지문이 똑같은 에러를 계속 발생했을때 그 지문을 pass하는 경우 -> 3번 기회주고 똑같은 에러가 계속 발생하면 pass 
                print(tries, "번째 시도")
                if tries > 3 and len(text_chunks) > break_count+1: 
                  break_count+= 1
                  tries = 0 
                
        sum_summary_txt = ''
        for i in range(len(ai_summary_response_list)):
            sum_summary_txt += ai_summary_response_list[i].summaryContent


        summary_json_response = { "summaryContent": sum_summary_txt}

        
        return jsonify(summary_json_response)

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    from waitress import serve
    print("server stating....")
    serve(app, host='0.0.0.0', port=5000)
