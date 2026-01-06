FROM python:3.9-slim
WORKDIR /app

#Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt


#Copy source code
COPY . .

#Command to run the model training script
CMD ["python", "src/train.py"]
