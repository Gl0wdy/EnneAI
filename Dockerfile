FROM python:3.14.2-slim

WORKDIR /app             

COPY requirements.txt .   
RUN pip install -r requirements.txt  

COPY . .

RUN python setup.py 

CMD ["python", "main.py"]     