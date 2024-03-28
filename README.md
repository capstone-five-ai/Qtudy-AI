# Qtudy-AI 환경설정


sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install python3.8 # 3.8이상

apt install python-pip
sudo apt install python3-pip3
pip install flask
pip install openai==0.28.0
pip install tiktoken
pip install Pillow
pip install easyocr 
pip install opencv-python
pip install gunicorn
pip install waitress



# 파이썬 플라스크 실행
일반 실행 : gunicorn -w 4 -b 0.0.0.0:5000 --timeout 200 <파일이름>:app
백그라운드실행 : nohup gunicorn -w 4 -b 0.0.0.0:5000 --timeout 200 --access-logfile access.log --error-logfile error.log <파일이름>:app > output.log 2>&1 &
+(gpt api키 수동으로 추가해줘야함)


백그라운드 실행 확인
: ps ax | grep python   (여기서 gunicorn 프로세스 4개 뜰거임)

백그라운드 실행 제거
: kill <프로세스이름>   (백그라운드 실행되는 프로세스 이름 넣으면 됨.)



# SWAP 파일 생성  (disk 공간 부족으로 생략)
sudo fallocate -l 4G /swapfile  # 스왑 파일 생성 (4GB)
sudo chmod 600 /swapfile        # 권한 설정
sudo mkswap /swapfile            # 스왑 파일 형식 지정
sudo swapon /swapfile            # 스왑 파일 활성화



