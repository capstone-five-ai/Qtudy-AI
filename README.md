# Qtudy-AI 환경설정

sudo apt install python3-pip3
pip install flask
pip install openai
pip install tiktoken
pip install Pillow
pip install easyocr 
pip install opencv-python




# 파이썬 플라스크 실행
일반 실행 : python3 nocr_gpt.py
백그라운드실행 : nohup python3 nocr_gpt.py &
+(gpt api키 수동으로 추가해줘야함)






# SWAP 파일 생성  (disk 공간 부족으로 생략)
sudo fallocate -l 4G /swapfile


