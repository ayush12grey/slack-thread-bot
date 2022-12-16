import slack
import os
from pathlib import Path
import requests
from dotenv import load_dotenv
from flask import Flask, request, Response,make_response
from slackeventsapi import SlackEventAdapter
import json


load_dotenv()

CLIENT_SIGNING_KEY =  os.getenv("SIGNING_SECRET_")
BOT_AUTH_TOKEN = os.getenv('SLACK_TOKEN_')
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


@app.route("/shortcut", methods=['GET', 'POST'])
def shortcuts():
    if request.method == 'POST':
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
        return make_response("", 200)

    return ""

@app.route("/command/thread-reminder", methods=['GET', 'POST'])
def commands():
    if request.method == 'POST':
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
        return make_response("", 200)

    return "True"


if __name__ == "__main__":
    # schedule_messages(SCHEDULED_MESSAGES)
    # ids = list_scheduled_messages('C01BXQNT598')
    # delete_scheduled_messages(ids, 'C01BXQNT598')
    app.run(debug=True)
