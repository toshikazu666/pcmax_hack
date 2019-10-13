import requests
from bs4 import BeautifulSoup

class WebInterface:
    def __init__(self, login_url, user, password):
        # ログインしてセッションを作る
        self.session = requests.session()
        login_info = {
            'login_id': user,
            'login_pw': password,
            'save_on': 'false',
            'login': '1'
        }
        res = self.session.post(login_url, data=login_info)
        res.raise_for_status()

    def get_tweet(self, tweet_url, category):
        # つぶやきをパースする
        res = self.session.get(tweet_url)
        soup = BeautifulSoup(res.text, 'html.parser')
        class_name = 'tw_list %s' % category
        return soup.find(class_=class_name)
        