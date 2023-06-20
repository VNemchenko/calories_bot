docker build -t calories_bot .
docker run --env-file .env -d calories_bot
