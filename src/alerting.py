import os
import requests


def send_discord_alert(message):
    webhook_url = os.environ.get('WEBHOOK_URL')
    if webhook_url:
        data = {"content": message}
        requests.post(webhook_url, json=data)