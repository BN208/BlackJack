FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1
ENV PORT=3000

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /data
ENV BLACKJACK_DB=/data/account.db

EXPOSE 3000

CMD ["waitress-serve", "--host=0.0.0.0", "--port=3000", "app:app"]
