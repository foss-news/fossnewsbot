import datetime
import logging
import requests
import sys


def date():
    return datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S%z')


class FNGS(object):
    def __init__(self, endpoint, api_pass):
        access_token = ''
        self.ENDPOINT = endpoint
        api_auth = {
            'username': 'tbot',
            'password': api_pass
        }
        try:
            access_token = requests.post(self.ENDPOINT + 'token/', data=api_auth).json()['access']
        except Exception as e:
            logging.debug(e)
            sys.exit('No access token!')
        logging.info('Access token ' + access_token)
        self.auth = {
            'Authorization': 'Bearer ' + access_token
        }

    def new_user(self, tid, username):
        data = {
            'tid': tid,
            'username': username
        }
        r = requests.post(f'{self.ENDPOINT}telegram-bot-user/',
                          data=data,
                          headers=self.auth)
        logging.info(f'Register new user id:{tid} username:{username} status:{r.status_code}')

    def get_user_id(self, tid):
        r = requests.get(f'{self.ENDPOINT}telegram-bot-user-by-tid/?tid={tid}',
                         headers=self.auth)
        logging.debug(r.text)
        return r.json()['id']

    def get_news_by_id(self, tid):
        r = requests.get(
            f'{self.ENDPOINT}telegram-bot-one-random-not-categorized-foss-news-digest-record/?tbot-user-id={self.get_user_id(tid)}',
            headers=self.auth)
        logging.debug(r.text)
        try:
            return r.json()[0]
        except Exception as e:
            logging.debug(e)
            return 'empty'

    def digest_send_data(self, tid, news_id, state='null'):
        data = {
            'telegram_bot_user': self.get_user_id(tid),
            'estimated_state': state,
            'digest_record': news_id,
            'dt': date()
        }
        r = requests.post(f'{self.ENDPOINT}telegram-bot-digest-record-categorization-attempt/',
                          headers=self.auth,
                          data=data)
        logging.info(f'Send Digest data by id:{tid} news_id:{news_id} status:{r.status_code}')
