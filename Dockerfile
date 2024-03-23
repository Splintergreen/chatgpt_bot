FROM python:3.10-slim
RUN mkdir /gpt_bot
COPY requirements.txt /gpt_bot
RUN pip3 install -r /gpt_bot/requirements.txt --no-cache-dir
COPY ./ /gpt_bot
WORKDIR /gpt_bot
CMD ["python3", "./bot.py"]