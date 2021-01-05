# telegram-notifier

Notify you when something is mentioned in a telegram channel.

1) Create a file called .env like sample.env with your api_id, api_hash and the name
   of your subscribed channels' json file. Every subscribed channel must have this fields
   correct:
   - name: the name of the channel. You can obtain this in the "Channel info" window. 
   - last_id: the id of the last message from which you want to be notified. First time, if
    this isn't filled in, the program will take the last message in the channel.
   - search_keywords:  these are the words that program will try to find in every
    message that is posted in the channel. If there is a match, you will be notified in your "Saved Messages" channel.
   
2) Create your subscribed channels' json file like the example.

3) Install poetry: https://python-poetry.org/docs/

4) poetry install

5) poetry run python notifier.py