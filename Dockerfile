FROM python:3.9.2
RUN pip install pandas
RUN pip install kafka-python
RUN apt-get update
Run apt-get install redis -y
RUN apt-get install ffmpeg libsm6 libxext6  -y
RUN pip install opencv-python
RUN pip install numpy
RUN pip install matplotlib
RUN pip install pandas
RUN pip install requests
RUN pip install sqlalchemy
#RUN pip3 install torch==1.10.1 torchvision==0.11.2 torchaudio==0.10.1 --extra-index-url https://download.pytorch.org/whl/cpu
RUN pip install imutils
RUN pip install PyYAML
RUN pip install tqdm
RUN pip install seaborn
RUN pip install scipy
Run pip install glob2
RUN pip install imutils
Run pip install pillow
RUN pip install kafka-python==2.0.2
Run pip install redis==4.6.0
Run pip install shared-memory-dict==0.7.2
Run pip install paramiko
Run pip install grpcio-tools
Run pip install redis
Run pip install protobuf==3.20.0
Run pip install "fastapi[all]"
copy postprocessing app/
workdir /app
CMD chmod +x run.sh
CMD ./run.sh