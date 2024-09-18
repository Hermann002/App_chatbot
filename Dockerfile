# step 1

FROM python:3.10-slim AS builder

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --prefix=/install -r requirements.txt

# step 2

FROM python:3.10-alpine

WORKDIR /app

COPY --from=builder /install /usr/local
COPY . .

EXPOSE 5000

CMD ["flask","--app", "App_chatbot", "run", "--host=0.0.0.0"]