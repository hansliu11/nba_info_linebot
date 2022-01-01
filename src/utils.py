import os
from linebot.models.messages import StickerMessage
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import nba_api as nba
from nba_api.stats.endpoints import leaguegamefinder, boxscoretraditionalv2, teamdetails
from nba_api.stats.static import teams



from dotenv import load_dotenv
from linebot import LineBotApi
from linebot.models import MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, CarouselTemplate, MessageTemplateAction, ButtonsTemplate
from linebot.models.template import CarouselColumn, ImageCarouselColumn, ImageCarouselTemplate

load_dotenv()
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
print(channel_access_token)
line_bot_api = LineBotApi(channel_access_token)
headers  = {
        'Connection': 'keep-alive',
        'Accept': 'application/json, text/plain, */*',
        'x-nba-stats-token': 'true',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
        'x-nba-stats-origin': 'stats',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Referer': 'https://stats.nba.com/',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
}

def count_words_at_url(url):
    resp = requests.get(url)
    return resp.json()

def send_text_message(reply_token, text):
    line_bot_api.reply_message(reply_token, TextSendMessage(text=text))

    return "OK"

def push_text_message(uid, message):
    line_bot_api.push_message(uid, TextSendMessage(text=message))
    
    return "OK"

def send_sticker(uid, pid, sid):
    line_bot_api.push_message(uid, StickerMessage(package_id=pid, sticker_id=sid))
    
    return "OK"

def send_img_carousel(uid, urls, labels, texts):
    cols = []
    for i , url in enumerate(urls):
        col = ImageCarouselColumn(
            image_url=url,
            action=MessageTemplateAction(
                label= labels[i],
                text = texts[i]
            )      
        )
        cols.append(col)
        
    message = TemplateSendMessage(
        alt_text='Carousel template',
        template=ImageCarouselTemplate(
            columns=cols
        )
    )
    line_bot_api.push_message(uid, message)  # bot 主動送訊息

def send_menu_carousel(uid):
    message = TemplateSendMessage(
        alt_text='Carousel template',
        template=CarouselTemplate(
            columns=[
                CarouselColumn(
                    thumbnail_image_url='https://cdn.udn.com/img/480/photo/web/video/321526_78296dec11f7e28b_o.jpg',
                    title='NBA Menu1',
                    text='which would you like to watch?',
                    actions=[
                        MessageTemplateAction(
                            label='Game Scores',
                            text='game scores',
                        ),
                        MessageTemplateAction(
                            label='Game BoxScores',
                            text='game box scores',
                        ),
                        MessageTemplateAction(
                            label='Game Schedule',
                            text='show game schedule',
                        )
                    ]
                ),
                CarouselColumn(
                    thumbnail_image_url='https://cdn.udn.com/img/480/photo/web/video/321526_78296dec11f7e28b_o.jpg',
                    title='NBA Menu2',
                    text='which would you like to watch?',
                    actions=[
                        MessageTemplateAction(
                            label='Standing',
                            text='show standing',
                        ),
                        MessageTemplateAction(
                            label='Stats Leader',
                            text='show season leader',
                        ),
                        MessageTemplateAction(
                            label='Search Team',
                            text='search team',
                        )
                    ]
                ),
            ]
        )
    )
    line_bot_api.push_message(uid, message)  # bot 主動送訊息

def send_button(uid, imgurl, title, discrip, texts, labels):
    acts = []
    for i, lab in enumerate(labels):
        acts.append(
            MessageTemplateAction(
                label=lab,
                text=texts[i]
            )
        )
    
    message = TemplateSendMessage(
        alt_text='Buttons Template',
        template=ButtonsTemplate(
            title=title,
            text=discrip,
            thumbnail_image_url=imgurl,
            actions=acts
        )
    )
    line_bot_api.push_message(uid, message)
     
     
def show_todayGame(reply_token):
    url = "https://tw.global.nba.com/stats2/scores/daily.json?countryCode=TW&locale=zh_TW&tz=%2B8"
    
    session = requests.Session()
    response = session.get(url=url, headers=headers).json()
    games = response["payload"]["date"]["games"]
    today = date.today().strftime("%Y/%m/%d")
    result = ""
    result += (f"\U0001f4c6 {today} \n\n")
    if len(games) == 0:
        result += "\U0000274c No games today"
    
    for game in games :
        gstatus = game['boxscore']['statusDesc']
        if gstatus == "結束":
            homeScore = game['boxscore']['homeScore']
            awayScore = game['boxscore']['awayScore']
            if homeScore > awayScore:
                winteam = game['homeTeam']['profile']["nameEn"]
                loseteam = game['awayTeam']['profile']["nameEn"]
                result += ("\U0001f3c6 {} \U0001f3c0 {}\n".format(winteam,homeScore))
                result += ("\U0001f62d {} \U0001f3c0 {}\n\n".format(loseteam,awayScore))
            else:
                loseteam = game['homeTeam']['profile']["nameEn"]
                winteam = game['awayTeam']['profile']["nameEn"]
                result += ("\U0001f3c6 {} \U0001f3c0 {}\n".format(winteam,awayScore))
                result += ("\U0001f62d {} \U0001f3c0 {}\n\n".format(loseteam,homeScore))
        elif "ET" in gstatus:
            tm = game['profile']["dateTimeEt"]
            tm = datetime.strptime(tm, '%Y-%m-%dT%H:%M')
            # convert ET time to Taipei time
            tm1 = tm.replace(tzinfo=timezone.utc)
            gametime = tm1.astimezone(timezone(timedelta(hours=13))).strftime("%I:%M %p")
            hometeam = game['homeTeam']['profile']["nameEn"]
            awayteam = game['awayTeam']['profile']["nameEn"]
            result += (f"\U00002694 {hometeam} vs {awayteam}\n")
            result += (f"\U000023f0 {gametime}\n\n")
            
        else:
            homeScore = game['boxscore']['homeScore']
            awayScore = game['boxscore']['awayScore']
            hometeam = game['homeTeam']['profile']["nameEn"]
            awayteam = game['awayTeam']['profile']["nameEn"]
            retime = game['boxscore']['periodClock']
            result += (f"\U0001f525 {gstatus} {retime}\n")
            result += ("{} \U0001f3c0 {}\n".format(hometeam,homeScore))
            result += ("{} \U0001f3c0 {}\n\n".format(awayteam,awayScore))
            

    result += "Pospond: "         
    for game in games:
        gstatus = game['boxscore']['statusDesc']
        if gstatus == "延期":
            hometeam = game['homeTeam']['profile']["nameEn"]
            awayteam = game['awayTeam']['profile']["nameEn"]
            result += (f"\n\U00002694 {hometeam} V.S. {awayteam}")
            
        
    # gamescore = scoreboard.ScoreBoard().games.get_dict()
    send_text_message(reply_token,result)
    return "OK"

def show_Games(reply_token, date:str):
    # gamedate = datetime.strptime(date,"%Y-%m-%d")
    # gamedate = (gamedate - timedelta(1)).strftime('%Y-%m-%d')
    url = f"https://tw.global.nba.com/stats2/scores/daily.json?countryCode=TW&gameDate={date}&locale=zh_TW&tz=%2B8"
    session = requests.Session()
    response = session.get(url=url, headers=headers).json()
    games = response["payload"]["date"]["games"]
    date = date.replace("-","/")
    result = ""
    result += (f"\U0001f4c6 {date} \n\n")
    if len(games) == 0:
        result += "\U0000274c No scheduled games"
    
    for game in games :
        gstatus = game['boxscore']['statusDesc']
        if gstatus == "結束":
            homeScore = game['boxscore']['homeScore']
            awayScore = game['boxscore']['awayScore']
            if homeScore > awayScore:
                winteam = game['homeTeam']['profile']["nameEn"]
                loseteam = game['awayTeam']['profile']["nameEn"]
                result += ("\U0001f3c6 {} \U0001f3c0 {}\n".format(winteam,homeScore))
                result += ("\U0001f62d {} \U0001f3c0 {}\n\n".format(loseteam,awayScore))
            else:
                loseteam = game['homeTeam']['profile']["nameEn"]
                winteam = game['awayTeam']['profile']["nameEn"]
                result += ("\U0001f3c6 {} \U0001f3c0 {}\n".format(winteam,awayScore))
                result += ("\U0001f62d {} \U0001f3c0 {}\n\n".format(loseteam,homeScore))
    
    result += "Pospond: "         
    for game in games:
        gstatus = game['boxscore']['statusDesc']
        if gstatus == "延期":
            hometeam = game['homeTeam']['profile']["nameEn"]
            awayteam = game['awayTeam']['profile']["nameEn"]
            result += (f"\n\U00002694 {hometeam} V.S. {awayteam}")
    
    send_text_message(reply_token,result)
    return "OK"

def show_tmw_schedule(reply_token):
    
    url = "https://tw.global.nba.com/stats2/season/schedule.json?countryCode=TW&days=1&locale=zh_TW&tz=%2B8"
    
    session = requests.Session()
    response = session.get(url=url, headers=headers).json()
        
    games = response["payload"]["dates"][0]["games"]
    tomorrow = games[0]['profile']["dateTimeEt"].split("T")[0]
    gamedate = datetime.strptime(tomorrow,"%Y-%m-%d")
    gamedate = (gamedate + timedelta(1)).strftime('%Y-%m-%d')
    # tomorrow = tomorrow.replace("-","/")
    result = ""
    result += (f"\U0001f4c6 {gamedate} \n\n")
    if len(games) == 0:
        result += "\U0000274c No scheduled games"
    else:
        for game in games :
            # if game['gameStatusText'] != "PPD":
            tm = game['profile']["dateTimeEt"]
            tm = datetime.strptime(tm, '%Y-%m-%dT%H:%M')
            # convert ET time to Taipei time
            tm1 = tm.replace(tzinfo=timezone.utc)
            gametime = tm1.astimezone(timezone(timedelta(hours=13))).strftime("%I:%M %p")
            
            hometeam = game['homeTeam']['profile']["nameEn"]
            
            awayteam = game['awayTeam']['profile']["nameEn"]
            
            result += (f"\U000023f0 {gametime}\n")
            result += (f"\U00002694 {hometeam} vs {awayteam}\n\n")
        
        # result += "Pospond: \n"         
        # for game in games:
        #     if game['gameStatusText'] == "PPD":
        #         hometeam = game['homeTeam']['teamName']
        #         awayteam = game['awayTeam']['teamName']
        #         result += (f"\U00002694 {hometeam} V.S. {awayteam}")
    
    send_text_message(reply_token,result)
    return "OK"

def show_standings(uid):
    url = "https://tw.global.nba.com/stats2/season/conferencestanding.json?locale=zh_TW"
    
    session = requests.Session()
    # response = requests.get(url=url, headers=headers).json()
    response = session.get(url=url, headers=headers).json()
    Eteams = response["payload"]["standingGroups"][0]["teams"]
    Wteams = response["payload"]["standingGroups"][1]["teams"]
    Eteams_rank = {}
    Wteams_rank = {}
    resultE = '\U0001F4E2\U0001F4E2\U0001F4E2 Eastern Conference\n\n'
    resultW = '\U0001F4E2\U0001F4E2\U0001F4E2 Western Conference\n\n'
    for team in Eteams:
        conf = response["payload"]["standingGroups"][0]["displayConference"]
        tname = team["profile"]["cityEn"] + " " + team["profile"]["nameEn"]
        wins = team["standings"]["wins"]
        losses = team["standings"]["losses"]
        winp = team["standings"]["winPct"]
        rank = team["standings"]["confRank"]
        gb = team["standings"]["confGamesBehind"]

        Eteams_rank[rank] = [conf, tname, wins, losses, winp, gb]
        
    for team in Wteams:
        conf = response["payload"]["standingGroups"][0]["displayConference"]
        tname = team["profile"]["cityEn"] + " " + team["profile"]["nameEn"]
        wins = team["standings"]["wins"]
        losses = team["standings"]["losses"]
        winp = team["standings"]["winPct"]
        rank = team["standings"]["confRank"]
        gb = team["standings"]["confGamesBehind"]

        Wteams_rank[rank] = [conf, tname, wins, losses, winp, gb]
        
    for rank in range(1,len(Eteams_rank)+1):
        team = Eteams_rank[rank]
        if(rank == 1):
            resultE += ("\U0001F947 {}({})\n" .format(team[1],rank))
        elif(rank == 2):
            resultE += ("\U0001F948 {}({})\n" .format(team[1],rank))
        elif(rank == 3):
            resultE += ("\U0001F949 {}({})\n" .format(team[1],rank))
        elif(rank > 3 and rank < 9):
            resultE += ("\U0001f3c5 {}({})\n" .format(team[1],rank))
        else:
            resultE += ("\U00002716 {}({})\n" .format(team[1],rank))

        resultE += (f"{team[2]} W, {team[3]} L, {team[4]} W/L%, {team[5]} GB\n")
    
    for rank in range(1,len(Eteams_rank)+1):
        team = Wteams_rank[rank]
        if(rank == 1):
            resultW += ("\U0001F947 {}({})\n" .format(team[1],rank))
        elif(rank == 2):
            resultW += ("\U0001F948 {}({})\n" .format(team[1],rank))
        elif(rank == 3):
            resultW += ("\U0001F949 {}({})\n" .format(team[1],rank))
        elif(rank > 3 and rank < 9):
            resultW += ("\U0001f3c5 {}({})\n" .format(team[1],rank))
        else:
            resultW += ("\U00002716 {}({})\n" .format(team[1],rank))

        resultW += (f"{team[2]} W, {team[3]} L, {team[4]} W/L%, {team[5]} GB\n")
            
    push_text_message(uid,resultE)
    push_text_message(uid,resultW)
    
def show_boxscore(uid, dateteam):
    info = ['TEAM_ABBREVIATION', 'PLAYER_NAME', 'MIN', 'PTS','REB', 'AST', 'STL', 'BLK', 'TO']
    gamefinder = leaguegamefinder.LeagueGameFinder(season_nullable='2021-22',
                                                    league_id_nullable='00',
                                                    season_type_nullable='Regular Season',
                                                    headers=headers)
    games = gamefinder.get_data_frames()[0]
    list = dateteam.split(" ")
    Date = datetime.strptime(list[0], "%Y-%m-%d")
    gamedate = (Date - timedelta(1)).strftime('%Y-%m-%d')
    searchteam = " ".join(list[1:])
    # print(games.head())
    game = games[(games.GAME_DATE == gamedate) & (games.TEAM_NAME == searchteam)]
    gid = game['GAME_ID'].tolist()[0]
    searchteam_abbr = game['TEAM_ABBREVIATION'].values[0]
    opp_team = games[(games.GAME_ID==gid) & (games.TEAM_NAME != searchteam)]['TEAM_NAME'].values[0]
    print(gid)
    
    # stats = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id = gid)
    # stats_df = stats.player_stats.get_data_frame()
    # stats_df = stats_df[stats_df.MIN.notnull()]
    # player_stats = stats_df.loc[:,info]
    # result = ("\U0001f3c0\U0001f3c0\U0001f3c0 {}\n\n" .format(searchteam))
    # result_opp = ("\U0001f3c0\U0001f3c0\U0001f3c0 {}\n\n" .format(opp_team))
    # for index, player in player_stats.iterrows():
    #     if player['TEAM_ABBREVIATION'] == searchteam_abbr:
    #         result += (f"\U0001F525\U000026f9\U0001F525 {player['PLAYER_NAME']} {player['MIN']}\n")
    #         result += (f"{player['PTS']} PTS, {player['AST']} AST, {player['REB']} REB, {player['STL']} STL, {player['BLK']} BLK, {player['TO']} TOV\n\n")
    #     else:
    #         result_opp += (f"\U0001F525\U000026f9\U0001F525 {player['PLAYER_NAME']} {player['MIN']}\n")
    #         result_opp += (f"{player['PTS']} PTS, {player['AST']} AST, {player['REB']} REB, {player['STL']} STL, {player['BLK']} BLK, {player['TO']} TOV\n\n")
    # push_text_message(uid, result)
    # push_text_message(uid, result_opp)
    
def showStatleader(uid):
    url = "https://stats.nba.com/js/data/widgets/home_season.json"
    response = requests.get(url=url, headers=headers).json()
    seasonLeaders = response["items"][0]["items"]
    result = "Season Leaders\n\n"
    
    pointleaders = seasonLeaders[0]
    title = pointleaders["title"]
    result += f"\U0001f525 {title} \U0001f525\n\U0001f451 "
    for i in range(3):
        player = pointleaders["playerstats"][i]
        result += "{}  {} PTS\n".format(player['PLAYER_NAME'], player['PTS'])
    
    reboundleaders = seasonLeaders[1]
    result += f"\n\U0001f3c0 {reboundleaders['title']} \U0001f3c0\n\U0001f451 "
    for i in range(3):
        player = reboundleaders["playerstats"][i]
        result += "{}  {} REB\n".format(player['PLAYER_NAME'], player['REB'])
      
    assistleaders = seasonLeaders[2]
    result += f"\n\U0001f64c {assistleaders['title']} \U0001f64c\n\U0001f451 "
    for i in range(3):
        player = assistleaders["playerstats"][i]
        result += "{}  {} AST\n".format(player['PLAYER_NAME'], player['AST'])
        
    blockleaders = seasonLeaders[3]    
    result += f"\n\U0001f932 {blockleaders['title']} \U0001f932\n\U0001f451 "
    for i in range(3):
        player = blockleaders["playerstats"][i]
        result += "{}  {} BLK\n".format(player['PLAYER_NAME'], player['BLK']) 
        
    stealleaders = seasonLeaders[4]    
    result += f"\n\U000026f9 {stealleaders['title']} \U000026f9\n\U0001f451 "
    for i in range(3):
        player = stealleaders["playerstats"][i]
        result += "{}  {} STL\n".format(player['PLAYER_NAME'], player['STL'])
        
    threeptsleader = seasonLeaders[6]    
    result += f"\n\U0001f44c {threeptsleader['title']} \U0001f44c\n\U0001f451 "
    for i in range(3):
        player = threeptsleader["playerstats"][i]
        result += "{}  {} 3PM\n".format(player['PLAYER_NAME'], player['FG3M'])
        
    push_text_message(uid, result)
    
def showTeam(uid):
    url = "https://stats.nba.com/js/data/widgets/home_season.json"
    response = requests.get(url=url, headers=headers).json()

"""
def send_image_url(id, img_url):
    pass

def send_button_message(id, text, buttons):
    pass
"""
