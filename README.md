# Nutrition Tracker Bot

This is a Telegram bot for tracking nutrition information using Python, SQLAlchemy, PostgreSQL and OpenAI's GPT-4.

## Table of Contents

- [About](#about)
- [Getting Started](#getting-started)
- [Usage](#usage)

## About

The bot helps users track their daily nutrition by recording food intake and calculating fat, protein, carbohydrates, and calories. It uses OpenAI's GPT-4 model to understand and interpret food descriptions. The information is then stored in a PostgreSQL database.

## Getting Started

### Prerequisites

The following environment variables need to be set in your system:

- `OPENAI_API_KEY`: Your OpenAI API Key.
- `TELEGRAM_BOT_TOKEN`: The token for your Telegram Bot.
- `DATABASE`: The name of your PostgreSQL database.
- `DB_USER`: Your PostgreSQL user name.
- `DB_PASSWORD`: Your PostgreSQL password.

### Installation

1. Clone this repository:

    ```
    git clone https://github.com/yourusername/nutrition-tracker-bot.git
    ```

2. Go to the project directory:

    ```
    cd nutrition-tracker-bot
    ```

3. Install required Python libraries:

    ```
    pip install -r requirements.txt
    ```

4. Build Docker image:

    ```
    docker build -t nutrition-tracker-bot .
    ```

5. Run the Docker container:

    ```
    docker run -d -p 80:80 nutrition-tracker-bot
    ```

## Usage

To use this bot, send a message to the bot with the description of the food intake. The bot will then respond with the nutrition information (fat, protein, carbohydrates, and calories).

You can also send a date in the format `DD.MM.YY` to get the total nutrition information for that date.
