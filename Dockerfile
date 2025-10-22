FROM python:3.12-slim

#Work Directory
WORKDIR /app

#Copy requirements
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

#Copy app
COPY . /app

#Create directory for SQLite database
RUN mkdir -p /app/db

#Expose port
EXPOSE 8001

#Run app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
