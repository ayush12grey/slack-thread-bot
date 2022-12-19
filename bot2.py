import os
import re
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import requests
load_dotenv()
app = App(token=os.getenv("SLACK_TOKEN_"))

last_message_by_users = {}
users_allowed = os.getenv("USERS_ALLOWED")
Question_and_Exclamation = ['?','!','Can','can', 'could','Could','Congrats','Congratulations']
text_user = 'I detected multiple messages in a row in a short time. \nPlease edit them to use a single message instead. 💙 \nThis way, people can easily reply to the right one using threads. \nPlease use  ‘shift+enter/return’ for going to the next line. '

@app.event("message")
def handle_message_events(body, client, say):
    event =body["event"]
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')
    timestamp = event.get('ts')
    is_bot = 'bot_id' in event
    isUserAllowed = user_id in users_allowed
    Inquestion = False
    Inthread = False
    if 'thread_ts' in event:
        Inthread = True
    for item in Question_and_Exclamation:
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
                if float(timestamp) - float(last_warned) > 30:

                    client.chat_postMessage(
                        channel=channel_id, thread_ts=last_time_count, text="[THREAD] ⬇️")
                    client.chat_postMessage(
                        channel=f'@{user_id}', text=text_user)

                    last_message_by_users[user_id] = {'timestamp': event.get('ts'), 'channelid': channel_id,
                                                      'lastwarned': timestamp}
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

    else:
        if not Inthread and not Inquestion and not is_bot and isUserAllowed:
            last_message_by_users[user_id] = {'timestamp': timestamp, 'channelid': channel_id}

@app.event('reaction_added')
def handle_message_events(body, client, say):
    event = body["event"]
    reaction_type = event.get('reaction')
    channel_id = event.get('item', {}).get('channel')
    thread_ts = event.get('item', {}).get('ts')
    type = event.get('item', {}).get('type')
    user_id = event.get('user')

    if type == 'message' and reaction_type == 'speak_no_evil':
        client.chat_postMessage(
            channel=channel_id, thread_ts=thread_ts,
            text="A Friendly reminder : please consider deleting this message and responding in thread instead 💙")

@app.shortcut("thread-starter")
def open_thread(ack, shortcut, client):
    ack()
    thread_ts = shortcut['message_ts']
    channel_id = shortcut['channel']['id']
    client.chat_postMessage(
        channel=channel_id, thread_ts=thread_ts,
        text="[THREAD] ⬇️")


@app.command("/thread-reminder")
def thread_reminder_command(ack, respond, command):
    ack()
    response_url = command['response_url']
    data_json = {
        'replace_original': 'true',
        'response_type': 'in_channel',
        'text': 'Friendly reminder: Please always use threads when possible 💙',
    }
    response = requests.post(response_url, json=data_json)

    if response.status_code != 200:
        print(response.raw)
        print("unsuccessfull")
    respond('')

if __name__ == "__main__":
    handler = SocketModeHandler(app, os.getenv("APP_TOKEN"))
    handler.start()