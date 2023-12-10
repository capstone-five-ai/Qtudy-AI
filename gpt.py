from flask import Flask, request, jsonify
import openai
from PIL import Image
import io
import matplotlib.pyplot as plt

app = Flask(__name__)

# OpenAI API Key 환경변수 설정해야함 (github에 key 올라가면 key 막힘)
#openai.api_key


class AiProblemDto: #문제 input
    def __init__(self, text, type, amount, difficulty):
        self.text = text
        self.type = type
        self.amount = amount
        self.difficulty = difficulty

class AiResponseDto: #문제 output
    def __init__(self, problemName, problemCommentary,problemAnswer=None,problemChoices = None):
        self.problemName = problemName
        self.problemChoices = problemChoices #객관식은 있어야하고, 주관식은 없어도 됨
        self.problemAnswer = problemAnswer
        self.problemCommentary = problemCommentary

class AiProblemByJpgDto: #문제 input
    def __init__(self, text, type, amount, difficulty):
        self.text = text
        self.type = type
        self.amount = amount
        self.difficulty = difficulty
        
         

@app.route('/create/problem/mcq', methods=['POST']) #객관식
def prompt1():
    try:
        data = request.json

        # Assuming your JSON format is similar to the AiProblemDto structure
        ai_problem_dto = AiProblemDto(
            text=data.get('text'),
            type=data.get('type'),
            amount=data.get('amount'),
            difficulty=data.get('difficulty')
        )

        # Now you can use ai_problem_dto to create your prompt
        prompt = ai_problem_dto.text + "라는 내용을 기반으로 객관식 문제를 만들어줘"
        messages_p = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ]
        print(prompt)

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages_p,
        )
        
        # Create a list of AiResponseDto instances
        ai_response_list = [
            AiResponseDto(
                problemName="문제 제목1",
                problemChoices=["보기 1", "보기 2", "보기 3"],
                problemAnswer="2",
                problemCommentary="문제 해설 1"
            ),
            AiResponseDto(
                problemName="문제 제목2",
                problemChoices=["보기 1", "보기 2", "보기 3"],
                problemAnswer="3",
                problemCommentary="문제 해설 2"
            ),
            # Add more items to the list if needed
        ]

        # Convert the list to a JSON response
        json_response = [
            {
                "problemName": item.problemName,
                "problemChoices": item.problemChoices,
                "problemAnswer": item.problemAnswer,
                "problemCommentary": item.problemCommentary
            }
            for item in ai_response_list
        ]
        print(json_response)

        return jsonify(json_response)

    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
    
    
    
        
    
    
    
@app.route('/create/problem/saq', methods=['POST']) #주관식
def prompt3():
        data = request.json

        # Assuming your JSON format is similar to the AiProblemDto structure
        ai_problem_dto = AiProblemDto(
            text=data.get('text'),
            type=data.get('type'),
            amount=data.get('amount'),
            difficulty=data.get('difficulty')
        )

        # Now you can use ai_problem_dto to create your prompt
        prompt = ai_problem_dto.text + "라는 내용을 기반으로 주관식 문제를 만들어줘"
        messages_p = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ]
        print(prompt)

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages_p,
        )
        
        # Create a list of AiResponseDto instances
        ai_response_list = [
            AiResponseDto(
                problemName="문제 제목1",
                problemCommentary="문제 해설1"
            ),
            AiResponseDto(
                problemName="문제 제목2",
                problemCommentary="문제 해설2"
            ),
            AiResponseDto(
                problemName="문제 제목3",
                problemCommentary="문제 해설3"
            ),
            AiResponseDto(
                problemName="문제 제목4",
                problemCommentary="문제 해설4"
            ),
            AiResponseDto(
                problemName="문제 제목5",
                problemCommentary="문제 해설5"
            ),
            AiResponseDto(
                problemName="문제 제목6",
                problemCommentary="문제 해설6"
            ),
            # Add more items to the list if needed
        ]

        # Convert the list to a JSON response
        json_response = [
            {
                "problemName": item.problemName,
                "problemChoices": item.problemChoices,
                "problemCommentary": item.problemCommentary
            }
            for item in ai_response_list
        ]
        print(json_response)

        return jsonify(json_response)

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
class AiSummaryDto: #요점정리 input
     def __init__(self, text, amount, fileName):
         self.text = text
         self.amount = amount
         self.fileName = fileName
         
    
class AiSummaryResponseDto: #요점정리 output
     def __init__(self, summaryTitle, summaryContent,fileName):
         self.summaryTitle= summaryTitle
         self.summaryContent = summaryContent    
         self.fileName = fileName


@app.route('/create/summary', methods=['POST']) #요점정리
def prompt4():
    try:
        data = request.json

        # Assuming your JSON format is similar to the AiProblemDto structure
        ai_summary_dto = AiSummaryDto(
            text=data.get('text'),
            amount=data.get('amount'),
            fileName=data.get('fileName')
        )

        # Now you can use ai_problem_dto to create your prompt
        prompt = ai_summary_dto.text + "라는 내용을 기반으로 요점정리를 만들어줘"
        messages_p = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ]
        print(prompt)

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages_p,
        )
        
        # Create a list of AiResponseDto instances
        ai_response = AiSummaryResponseDto(
            summaryTitle="요점정리 제목",
            summaryContent="요점정리",
            fileName="파일이름"
        )

        # Convert the list to a JSON response
        json_response = {
            "summaryTitle": ai_response.summaryTitle,
            "summaryContent": ai_response.summaryContent,
            "fileName": ai_response.fileName
        }

        print(json_response)

        return jsonify(json_response)

    except Exception as e:
        return jsonify({"error": str(e)}), 400
    

class AiGenerateProblemByFileDto:
    def __init__(self, type, amount, difficulty, files):
        self.type = type
        self.amount = amount
        self.difficulty = difficulty
        self.files = files    
        
@app.route('/create/problem/mcq/jpg', methods=['POST']) #객관식
def prompt2():

        # Assuming your JSON format is similar to the AiProblemDto structure
        ai_problem_dto = AiGenerateProblemByFileDto(
            files=request.files.get('files'),
            type=request.values.get('type'),
            amount=request.values.get('amount'),
            difficulty=request.values.get('difficulty')
        )
        
        #for uploaded_file in ai_problem_dto.files:
        # 파일의 이름을 출력하고 저장하거나 원하는 작업을 수행할 수 있습니다.
            #print(uploaded_file.filename)
            #uploaded_file.save(f"uploads/{uploaded_file.filename}")
        #print(ai_problem_dto.type)
        
        print(ai_problem_dto.files)
        print(AiGenerateProblemByFileDto)
        
        file_bytes = ai_problem_dto.files.read()

        # 바이트를 PIL Image로 변환
        image = Image.open(io.BytesIO(file_bytes))
        plt.imshow(image)
        plt.axis('on')  # 축을 표시할지 여부
        plt.show()
    



        # Now you can use ai_problem_dto to create your prompt
        prompt = "라는 내용을 기반으로 객관식 문제를 만들어줘"
        messages_p = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ]
        print(prompt)

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages_p,
        )
        
        # Create a list of AiResponseDto instances
        ai_response_list = [
            AiResponseDto(
                problemName="문제 제목1",
                problemChoices=["보기 1", "보기 2", "보기 3"],
                problemAnswer="2",
                problemCommentary="문제 해설 1"
            ),
            AiResponseDto(
                problemName="문제 제목2",
                problemChoices=["보기 1", "보기 2", "보기 3"],
                problemAnswer="3",
                problemCommentary="문제 해설 2"
            ),
            # Add more items to the list if needed
        ]

        # Convert the list to a JSON response
        json_response = [
            {
                "problemName": item.problemName,
                "problemChoices": item.problemChoices,
                "problemAnswer": item.problemAnswer,
                "problemCommentary": item.problemCommentary
            }
            for item in ai_response_list
        ]
        print(json_response)

        return jsonify(json_response)



class AiSummaryJPGDto: #요점정리 input
     def __init__(self, files, amount, fileName):
         self.files = files
         self.amount = amount
         self.fileName = fileName
         
    


@app.route('/create/summary/jpg', methods=['POST']) #요점정리
def prompt5():
    try:
        data = request.form.to_dict()

        # Assuming your JSON format is similar to the AiProblemDto structure
        ai_summary_dto = AiSummaryJPGDto(
            files=data.get('files'),
            amount=data.get('amount'),
            fileName=data.get('fileName')
        )

        # Now you can use ai_problem_dto to create your prompt
        prompt = "라는 내용을 기반으로 요점정리를 만들어줘"
        messages_p = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ]
        print(prompt)

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages_p,
        )
        
        # Create a list of AiResponseDto instances
        ai_response = AiSummaryResponseDto(
            summaryTitle="요점정리 제목",
            summaryContent="요점정리",
            fileName="파일이름"
        )

        # Convert the list to a JSON response
        json_response = {
            "summaryTitle": ai_response.summaryTitle,
            "summaryContent": ai_response.summaryContent,
            "fileName": ai_response.fileName
        }

        print(json_response)

        return jsonify(json_response)

    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
    

if __name__ == '__main__':
    app.run(port=5000)
