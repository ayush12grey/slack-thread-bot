import slack
import os
from pathlib import Path
import requests
from dotenv import load_dotenv
from flask import Flask, request, Response,make_response
from slackeventsapi import SlackEventAdapter
import json

import time

load_dotenv()

CLIENT_SIGNING_KEY = '176eae18545dcb12c6de51a0e6735475'
BOT_AUTH_TOKEN = 'xoxb-4508841973635-4502380461302-4mdXD79X4jeEeCaysueIABVA'
app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(
    CLIENT_SIGNING_KEY, '/slack/events', app)

client = slack.WebClient(token= BOT_AUTH_TOKEN)

BOT_ID = client.api_call("auth.test")['user_id']
last_message_by_users = {}
#
users_allowed =['U04FBHD3D3K']
#users_allowed = []
message_counts = {}
welcome_messages = {}
Question_and_Exclamation = ['?','!','Can','can', 'could','Could','Congrats','Congratulations']
text_user = 'I detected multiple messages in a row in a short time. \nPlease edit them to use a single message instead. 💙 \nThis way, people can easily reply to the right one using threads. \nPlease use  ‘shift+enter/return’ for going to the next line. '


@ slack_event_adapter.on('message')
def message(payload):
    event = payload.get('event', {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')
    timestamp = event.get('ts')
    is_bot = 'bot_id' in event
    isUserAllowed = user_id in users_allowed
    print(isUserAllowed)
    Inquestion = False
    Inthread = False
    if 'thread_ts' in event:
        Inthread = True
    for item in Question_and_Exclamation :
        if item in text:
            client.chat_postMessage(
                channel=channel_id, thread_ts=timestamp, text="[THREAD] ⬇️")
            Inquestion = True
            break

    if isUserAllowed and user_id in last_message_by_users and not is_bot and not Inquestion and not Inthread:
        last_time_count = last_message_by_users[user_id]['timestamp']
        last_channel = last_message_by_users[user_id]['channelid']
        if float(timestamp) - float(last_time_count) <= 8 and last_channel == channel_id:
            if 'lastwarned' in last_message_by_users[user_id]:

                last_warned = last_message_by_users[user_id]['lastwarned']
                if float(timestamp) - float(last_warned) > 30 :

                     client.chat_postMessage(
                         channel=channel_id, thread_ts=last_time_count, text="[THREAD] ⬇️")
                     client.chat_postMessage(
                channel=f'@{user_id}', text=text_user)

                     last_message_by_users[user_id] = {'timestamp': event.get('ts'), 'channelid': channel_id,'lastwarned':timestamp}
                else:
                     last_message_by_users[user_id] = {'timestamp': event.get('ts'), 'channelid': channel_id,
                                                  'lastwarned': last_warned}
            else:
                client.chat_postMessage(
                    channel=channel_id, thread_ts=last_time_count, text="[THREAD] ⬇️")
                client.chat_postMessage(
                    channel=f'@{user_id}', text=text_user)
                last_message_by_users[user_id] = {'timestamp': timestamp, 'channelid': channel_id,
                                                  'lastwarned': timestamp}
        else:
            last_message_by_users[user_id]['timestamp'] = event.get('ts')

    else :
        if not Inthread and not Inquestion and not is_bot and isUserAllowed:
            last_message_by_users[user_id] = {'timestamp':timestamp,'channelid':channel_id }


    # print(last_message_by_users)
    # print(timestamp)

        # if user_id in message_counts:
        #     message_counts[user_id] += 1
        # else:
        #     message_counts[user_id] = 1
        #
        # if text.lower() == 'start':
        #     send_welcome_message(f'@{user_id}', user_id)
        # elif check_if_bad_words(text):
        #     ts = event.get('ts')
        #     client.chat_postMessage(
        #         channel=channel_id, thread_ts=ts, text="THAT IS A BAD WORD!")


@ slack_event_adapter.on('reaction_added')
def reaction(payload):
    event = payload.get('event', {})
    reaction_type = event.get('reaction')
    channel_id = event.get('item', {}).get('channel')
    thread_ts = event.get('item', {}).get('ts')
    type = event.get('item', {}).get('type')
    user_id = event.get('user')
    print(event)
    if type == 'message' and reaction_type == 'speak_no_evil':
        client.chat_postMessage(
            channel=channel_id, thread_ts=thread_ts, text="A Friendly reminder : please consider deleting this message and responding in thread instead 💙")



#
# @ app.route('/message-count', methods=['POST'])
# def message_count():
#     data = request.form
#     user_id = data.get('user_id')
#     channel_id = data.get('channel_id')
#     message_count = message_counts.get(user_id, 0)
#
#     client.chat_postMessage(
#         channel=channel_id, text=f"Message: {message_count}")
#     return Response(), 200
#
#
@app.route("/shortcut", methods=['GET', 'POST'])
def shortcuts():
    if request.method == 'POST':
        # json_string = request.body()
        # if json_string:
        #     x = json.loads(json_string)
        # else:
        #     # Your code/logic here
        #     x = {}

        json_value = json.loads(request.form['payload'])
        response_url = json_value['response_url']
        thread_ts = json_value['message']['ts']
        data_json ={
          'replace_original': 'true',
          'response_type': 'in_channel',
          'text': '[THREAD] ⬇️',
          'thread_ts': thread_ts,
        }
        response = requests.post(response_url, json= data_json)

        if response.status_code != 200:
            print(response.raw)
            print("unsuccessfull")

        print(response_url)
        print(thread_ts)
        return make_response("", 200)

    return "True"

@app.route("/command/thread-reminder", methods=['GET', 'POST'])
def commands():
    if request.method == 'POST':
        # json_string = request.body()
        # if json_string:
        #     x = json.loads(json_string)
        # else:
        #     # Your code/logic here
        #     x = {}
        #print(request.form)
        #json_value = json.loads()
        response_url = request.form['response_url']
        # thread_ts = json_value['message']['ts']
        data_json ={
          'replace_original': 'true',
          'response_type': 'in_channel',
          'text': 'Friendly reminder: Please always use threads when possible 💙',
           }
        response = requests.post(response_url, json= data_json)

        if response.status_code != 200:
            print(response.raw)
            print("unsuccessfull")

        print(response_url)
        #print(thread_ts)
        return make_response("", 200)

    return "True"


if __name__ == "__main__":
    # schedule_messages(SCHEDULED_MESSAGES)
    # ids = list_scheduled_messages('C01BXQNT598')
    # delete_scheduled_messages(ids, 'C01BXQNT598')
    app.run(debug=True)
