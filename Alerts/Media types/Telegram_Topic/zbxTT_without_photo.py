#!/usr/bin/env python3
########################
#  https://t.me/vadikonline1 #
########################
# https://github.com/vadikonline1/Zabbix-Repository
# python3 /usr/lib/zabbix/alertscripts/zbxTT.py "your_telegram_token" "YOUR_CHAT_ID" "subject" "message" "event_tags" "item_id"

import json
import requests
import sys

zabbix_telegram_token = sys.argv[1] if len(sys.argv) > 1 else '{$ZABBIX_TELEGRAM_TOKEN}'
chat_id = sys.argv[2] if len(sys.argv) > 2 else '{ALERT.SENDTO}'
subject = sys.argv[3] if len(sys.argv) > 3 else '{ALERT.SUBJECT}'
message = sys.argv[4] if len(sys.argv) > 4 else '{ALERT.MESSAGE}'
event_tags = sys.argv[5] if len(sys.argv) > 5 else ''
item_id = sys.argv[6] if len(sys.argv) > 6 else '{ITEM.ID}'
message_thread_id_default = sys.argv[7] if len(sys.argv) > 7 else '1'  # Default value for message thread ID

class TelegramNotifier:
    def __init__(self, zabbix_telegram_token, chat_id, parse_mode='markdownv2'):
        self.zabbix_telegram_token = zabbix_telegram_token
        self.chat_id = chat_id
        self.parse_mode = parse_mode
        self.message = ""

    def escape_markup(self, text):
        if self.parse_mode == 'markdown':
            return text.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[')
        elif self.parse_mode == 'markdownv2':
            return (text.replace('_', '\\_')
                        .replace('*', '\\*')
                        .replace('[', '\\[')
                        .replace(']', '\\]')
                        .replace('(', '\\(')
                        .replace(')', '\\)')
                        .replace('~', '\\~')
                        .replace('`', '\\`')
                        .replace('>', '\\>')
                        .replace('#', '\\#')
                        .replace('+', '\\+')
                        .replace('-', '\\-')
                        .replace('=', '\\=')
                        .replace('|', '\\|')
                        .replace('{', '\\{')
                        .replace('}', '\\}')
                        .replace('.', '\\.')
                        .replace('!', '\\!'))
        return text

    def send_message(self, message_thread_id=None):
        params = {
            'chat_id': self.chat_id,
            'text': self.message,
            'disable_web_page_preview': True,
            'disable_notification': False
        }

        if message_thread_id:
            params['message_thread_id'] = message_thread_id

        if self.parse_mode:
            params['parse_mode'] = self.parse_mode

        url = f'https://api.telegram.org/bot{self.zabbix_telegram_token}/sendMessage'
        response = requests.post(url, json=params)

        if response.status_code != 200:
            raise Exception(f"Error sending message: {response.text}")

    def check_chat_is_forum(self):
        url = f'https://api.telegram.org/bot{self.zabbix_telegram_token}/getChat?chat_id={self.chat_id}'
        response = requests.get(url)
        
        if response.status_code != 200:
            raise Exception(f"Error getting chat info: {response.text}")

        chat_info = response.json()
        return chat_info.get('result', {}).get('is_forum', False)

def main():
    try:
        tags = {}
        if event_tags.strip():
            for tag in event_tags.split(','):
                key_value = tag.split(':')
                if len(key_value) == 2:
                    key = key_value[0].strip()
                    value = key_value[1].strip()
                    if key.startswith('MessageThreadId'):
                        tags.setdefault(key, []).append(value)

        notifier = TelegramNotifier(zabbix_telegram_token, chat_id)
        notifier.message = f"{subject}\n{message}"

        message_thread_ids = [val for key in tags for val in tags[key]]
        if not message_thread_ids:
            message_thread_ids.append(message_thread_id_default)

        notifier.message = notifier.escape_markup(notifier.message)

        # Check if the chat is a forum
        is_forum = notifier.check_chat_is_forum()

        for thread_id in message_thread_ids:
            if thread_id:
                if is_forum:
                    notifier.send_message(message_thread_id=thread_id)
                else:
                    # If not a forum, send the original message without thread_id
                    notifier.message = f"{subject}\n{message}"
                    notifier.send_message()

        return 'OK'
    except Exception as error:
        raise Exception(f'Sending failed: {error}')

if __name__ == "__main__":
    print(main())
