
from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
import os

import urllib.request
import json
from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN
import time


import matplotlib.pyplot as plt

#チュウニズムのプレイ状況を取得するLINE bot

#トークンはherokuの環境変数
ACCESS_TOKEN = os.environ['ACCESS_TOKEN']

#難易度配列
difficulty = ['1','2','3','4','5','6','7','7+','8','8+','9','9+','10','10+','11','11+','12','12+','13','13+','14','14+','15']

#リストを受け取ると中央値を返す
def median(lst):
    if len(lst)%2 == 1:
        return lst[len(lst)//2]
    else:
        return (lst[len(lst)//2-1]+lst[len(lst)//2])/2

def compute(user_name,level):
    chartnum_dict = {
    1:0,
    2:0,
    3:0,
    4:0,
    5:0,
    6:0,
    7:0,
    7.5:0,
    8:0,
    8.5:0,
    9:0,
    9.5:0,
    10:0,
    10.5:0,
    11:0,
    11.5:0,
    12:0,
    12.5:0,
    13:0,
    13.5:0,
    14:0,
    14.5:0,
    15:0
    }

    #chunirecにアクセス
    account_info = urllib.request.urlopen('https://api.chunirec.net/2.0/users/show.json?token={0}&user_name={1}'.format(ACCESS_TOKEN,user_name)).read()
    account_info = json.loads(account_info.decode('utf-8'))
    if "error" in account_info.keys():
        return 0
    music_data = urllib.request.urlopen('https://api.chunirec.net/2.0/music/showall.json?region=jp2&token={0}'.format(ACCESS_TOKEN)).read()
    music_data = json.loads(music_data.decode('utf-8'))

    # まずは曲数を取得し，難易度ごとに集計（平均スコアの計算に活用）
    for music in music_data:
        if music["meta"]["genre"] != "WORLD'S END":
            for dif in music["data"].values():
                chartnum_dict[dif["level"]] += 1

    # プレイデータをchunirecから取得
    record = urllib.request.urlopen('https://api.chunirec.net/2.0/records/showall.json?region=jp2&token={0}&user_name={1}'.format(ACCESS_TOKEN,user_name)).read()
    record = json.loads(record.decode('utf-8'))

    sum_score = 0
    num_isplayed = 0
    lower_score = 1010001
    for music in record['records']:
        level_range = 0.5# このレベル帯における定数の幅
        if level <= 7:
            level_range=1
        #プレイデータから楽曲情報を取得
        #指定レベルの合計スコア
        if level <= music['level'] < level+level_range:
            sum_score += music['score']
            num_isplayed += 1
            if music['score'] < lower_score:
                lower_score = music['score']

    

    #left = list(range(lower_score-(lower_score%500),1010000,500))
    
    music_list = list(filter(lambda x:level<= x['level'] < level+0.5,record['records']))
    music_score_list = list(map(lambda x:x['score'],music_list))

    # グラフで結果を出力したい（現状未完）
    # height = [0 for i in range(len(left))]
    # i=0
    # for score in left:
    #     for music_score in music_score_list:
    #         if score <= music_score < score+500:
    #             height[i] += 1
    #     i+=1
    # plt.bar(left, height,width=300,color='r',linewidth=4,data=None)
    # plt.savefig('graph.png')

    music_score_list.sort()


    
    return (max(music_score_list),min(music_score_list),median(music_score_list),sum_score/num_isplayed,sum_score/chartnum_dict[level])

# 未鳥状況取得用関数
def notreach_sss(user_name,level):
    
    #アカウントのデータをchunirecから取得
    account_info = urllib.request.urlopen('https://api.chunirec.net/2.0/users/show.json?token={0}&user_name={1}'.format(ACCESS_TOKEN,user_name)).read()
    account_info = json.loads(account_info.decode('utf-8'))
    if "error" in account_info.keys():
        return 0
    music_data = urllib.request.urlopen('https://api.chunirec.net/2.0/music/showall.json?region=jp2&token={0}'.format(ACCESS_TOKEN)).read()
    music_data = json.loads(music_data.decode('utf-8'))


    record = urllib.request.urlopen('https://api.chunirec.net/2.0/records/showall.json?region=jp2&token={0}&user_name={1}'.format(ACCESS_TOKEN,user_name)).read()
    record = json.loads(record.decode('utf-8'))

    sss = 1007500 # SSSボーダー
    notreach_sss_dict = {level+(0.1)*i:0 for i in range(5)}
    for music in record['records']:
        if level <= music['level'] < level+0.5:
            #指定レベルのうち，SSSボーダーに達していない曲をカウント
            if music['score'] < sss:
                notreach_sss_dict[music['const']] += 1

    s = ""

    for (const,num) in notreach_sss_dict.items():
        s += "定数" + str(const) + ":未鳥" +str(num) + "譜面\n"

    return s



app = Flask(__name__)

#環境変数取得
YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message_list = event.message.text.split()
    if len(message_list) == 2 and message_list[1] in difficulty:
        #{ユーザー名} {難易度}
        #→そのレベル帯のプレイ状況
        (max_s,min_s,mid,ave1,ave2) = compute(message_list[0],float(message_list[1].replace('+','.5')))
        messeage = []
        '''
        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(graph.png))
        ''' 
        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="平均スコア:{0}\n未プレイ楽曲を含めた平均:{1}\n最大スコア:{2}\n最小スコア:{3}\n中央値:{4}".format(ave1,ave2,max_s,min_s,mid)))
    elif len(message_list) == 3 and message_list[1] == "未鳥" and  message_list[2] in difficulty:
        #{ユーザー名} {未鳥} {難易度}
        #→譜面定数別にそのレベルの未鳥が何曲あるか送信
        text = notreach_sss(message_list[0],float(message_list[2].replace('+','.5')))
        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=text))
    # else:
    #     line_bot_api.reply_message(
    #         event.reply_token,
    #         TextSendMessage(text="my message:"+event.message.text))


if __name__ == "__main__":
#    app.run()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)