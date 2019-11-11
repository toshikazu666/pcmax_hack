import os
import re
import datetime
from bs4 import BeautifulSoup
from configparser import ConfigParser
from argparse import ArgumentParser
import matplotlib.pyplot as plt
from web_interface import WebInterface

html_tag_pattern = re.compile(r'<[^>]*?>')

config = ConfigParser()
config.read('settings.ini')

def make_values_of_tweet(web, dt, room, category):
    # 時間(Hour)ごとのつぶやきの数を集計する
    values = {i: 0 for i in range(0, 24)} # ひな型
    page_num = 1
    print('Aggregating values of "%s" tweets'%category)
    while True:
        print('Processing...')
        # 有効な日時のツイートがなくなるまでページを進める
        num_str = str(page_num)
        tweet_url = config.get('web', 'tweet_url').replace('ROOM', room).replace('PAGE_NUM', num_str)
        all_tweet = web.get_tweet(tweet_url, category)
        # 参照渡しでvaluesを更新する
        if aggregate_tweet(all_tweet, dt, values) == 'END':
            break
        page_num += 1
    print('Scceeded')
    return values

def aggregate_tweet(all_tweet, date_t, values):
    # つぶやきから日時のみを抽出
    date_list = all_tweet.find_all(class_='date')
    # 日時の文字列をdatetime.datetimeに変換
    datetime_list = [datetime.datetime.strptime(remove_html_tag(date), '%Y/%m/%d %H:%M') for date in date_list]
    # 抽出した日時の中に引数の日時が含まれているか確認し、含まれている場合にグラフ用のvaluesを更新する
    pattern = check_datetime(date_t, datetime_list)
    if pattern == 'EXECUTE':
        valid_dt = [dt for dt in datetime_list if dt.date() == date_t.date()]
        for dt in valid_dt:
            values[dt.hour] += 1
    return pattern

def check_datetime(date_t, datetime_list):
    # 抽出した日時の中に引数の日時が含まれているか確認してフラグを返す
    date_list = [dt.date() for dt in datetime_list]
    date = date_t.date()
    if date in date_list:
        # 含まれているため処理を実行するフラグ
        return 'EXECUTE'
    elif max(date_list) < date:
        # 含まれておらず、過去のページにも含まれていなので処理終了
        return 'END'
    elif min(date_list) > date:
        # 含まれていないが、過去のページには含まれているので処理はスキップ
        return 'PASS'

def remove_html_tag(html):
    # HTMLのタグを除去して文字列を返す
    return html_tag_pattern.sub('', str(html))

def make_graph(values_pure, values_adult, date):
    # グラフを作成してPNG形式で保存する
    plt.cla()
    plt.figure(figsize=(6, 6))

    # プロットする(x, y)の値
    x = list(values_pure.keys())
    yp = list(values_pure.values()) # ピュア版
    ya = list(values_adult.values()) # アダルト版

    # マーカーと点線でグラフをプロット
    plt.plot(x, yp, color='royalblue', linewidth=2, linestyle=':', marker='x', ms=8, label='pure')
    plt.plot(x, ya, color='hotpink', linewidth=2, linestyle=':', marker='x', ms=8, label='adult')

    # タイトル/軸/ラベル/凡例/レイアウトの設定
    plt.title(str(date))
    plt.xticks(x)
    plt.xlabel('Time(hour)')
    plt.ylabel('Number of tweets')
    plt.xlim(x[0], x[-1])
    plt.ylim(0,100)
    plt.grid()
    plt.legend()
    plt.tight_layout()

    # ファイルを保存
    filename = '%s.png' % str(date)
    plt.savefig(filename)
    print('Saving file -> "%s"'%filename)

def main():
    parser = ArgumentParser()
    parser.add_argument('-d', '--date', help='date for aggregate, YYYYMMDD format is required')
    args = parser.parse_args()

    try:
        dt = datetime.datetime.strptime(args.date, '%Y%m%d')
        date = dt.date()
        today = datetime.date.today()
        if date > today:
            # コマンドライン引数の日付が今日より後日の場合は例外を発生
            raise ValueError('%s is over today'%date)
    except Exception as e:
        # 例外を捕捉したら日付を今日として実行する
        print(e)
        dt = datetime.datetime.now()
        print('Exception was caught. Aggregate as today (%s)'%dt.date())

    print('Make graph of tweets on "%s"'%dt.date())

    login_url = config.get('web', 'login_url')
    # ユーザ/パスワードは環境変数から設定する前提
    login_user = os.environ.get('LOGIN_USER')
    login_password = os.environ.get('LOGIN_PASSWORD')

    # ピシマにログインしてセッションを維持する
    web = WebInterface(login_url, login_user, login_password)

    # つぶやきの数を時間ごとに集計
    pure_tweet_value = make_values_of_tweet(web, dt, '1', 'pure')
    adult_tweet_value = make_values_of_tweet(web, dt, '2', 'adult')
    
    # グラフを出力
    make_graph(pure_tweet_value, adult_tweet_value, dt.date())

if __name__ == '__main__':
    main()
