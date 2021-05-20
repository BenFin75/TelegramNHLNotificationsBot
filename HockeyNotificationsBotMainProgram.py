from telegram import *
from telegram.ext import *
import logging
import requests
import json
import os
from datetime import datetime, timedelta, date
from threading import Timer
import pandas as pd
from pathlib import Path, PureWindowsPath
from dateutil.relativedelta import relativedelta

bot_token_df = pd.read_csv((os.path.join(os.path.dirname(os.getcwd()),"TelegramBotTokens.csv")))
bot_index = int(bot_token_df.index[bot_token_df['Bot Name'] == 'Hockey Bot'].values)
bot_token = str(bot_token_df.loc[[bot_index], ['Bot Token']].values).strip("'[]")

bot = Bot(bot_token)
updater=Updater(bot_token, use_context=True)

chatdb_win = PureWindowsPath('.\Database\ChatDatabase.csv')
teamsdb_win = PureWindowsPath('.\Database\TeamNames.csv')
chatdb = Path(chatdb_win)
teamsdb = Path(teamsdb_win)

dispatcher=updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

team_ids = []
todays_date = date.today()
slashgame = 0
a_month_from_now = todays_date + relativedelta(months=1)
seasoncheck_url = f'https://statsapi.web.nhl.com/api/v1/schedule?startDate={todays_date}&endDate={a_month_from_now}'
seasoncheck_r = requests.get(seasoncheck_url)
seasoncheck_json = seasoncheck_r.json() 
seasoncheck = json.dumps(seasoncheck_json['totalItems'])



def start(update, context):
    welcome_msg = (
        "Hello!  Welcome to the NHL game notifications bot!" + "\n" + "\n" + 
        "Type /setup to get started, or /help for a list of commands." + "\n" + "\n" + 
        "Made by Ben Finley" + "\n" + 
        "The code for this bot is avalible at: https://github.com/Hiben75/TelegramNHLNotifcationBot"
        )
    context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_msg, disable_web_page_preview=1);

def setup(update: Update, context: CallbackContext):
    team_ids.clear()
    global chatsdf
    global slashgame
    global userid
    global chatname
    global exists
    chatsdf = pd.read_csv(chatdb)
    userid = update.message.chat.id
    if userid > 0:
        chatname = update.message.chat.username;
    if userid < 0:
        chatname = update.message.chat.title;
    exists = userid in chatsdf.ChatID.values
    reply_buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Penguins", callback_data=5)
        ],
        [
            InlineKeyboardButton("Devils", callback_data=1),
            InlineKeyboardButton("Islanders", callback_data=2),
            InlineKeyboardButton("Rangers", callback_data=3),
            InlineKeyboardButton("Flyers", callback_data=4),
            InlineKeyboardButton("Bruins", callback_data=6)
        ],
        [
            InlineKeyboardButton("Sabres", callback_data=7),
            InlineKeyboardButton("Habs", callback_data=8),
            InlineKeyboardButton("Senators", callback_data=9),
            InlineKeyboardButton("Leafs", callback_data=10),
            InlineKeyboardButton("Canes", callback_data=12)
        ],
        [
            InlineKeyboardButton("Panthers", callback_data=13),
            InlineKeyboardButton("Bolts", callback_data=14),
            InlineKeyboardButton("Capitals", callback_data=15),
            InlineKeyboardButton("Hawks", callback_data=16),
            InlineKeyboardButton("Wings", callback_data=17)],
        [
            InlineKeyboardButton("Predators", callback_data=18),
            InlineKeyboardButton("Blues", callback_data=19),
            InlineKeyboardButton("Flames", callback_data=20),
            InlineKeyboardButton("Colorado", callback_data=21),
            InlineKeyboardButton("Oilers", callback_data=22)
        ],
        [
            InlineKeyboardButton("Canucks", callback_data=23),
            InlineKeyboardButton("Ducks", callback_data=24),
            InlineKeyboardButton("Stars", callback_data=25),
            InlineKeyboardButton("Kings", callback_data=26),
            InlineKeyboardButton("Sharks", callback_data=28)
        ],
        [
            InlineKeyboardButton("Jackets", callback_data=29),
            InlineKeyboardButton("Wild", callback_data=30),
            InlineKeyboardButton("Jets", callback_data=52),
            InlineKeyboardButton("Coyotes", callback_data=53),
            InlineKeyboardButton("Knights", callback_data=54)
        ],
        [
            InlineKeyboardButton("Done", callback_data='✔️'),
        ]
    ])
    update.message.reply_text(
        f'Hello {update.effective_user.first_name}, What teams would you like notifications for?' + "\n" + "When all teams have been added, click Done",
        reply_markup=reply_buttons
    )

def button(update: Update, context: CallbackContext):
    global formatted_team_ids
    global chat_id_set
    global slashgame
    if update.callback_query.data == '✔️':
        chat_id_set = update.effective_chat.id
        print(update)
        update.callback_query.answer()
        update.callback_query.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup([])
            )
        context.bot.deleteMessage(update.callback_query.message.chat.id, update.callback_query.message.message_id)
        setup_msg = 'Your team preferences have been updated!'
        context.bot.send_message(chat_id=update.effective_chat.id, text=setup_msg)
        databasemanagementteams(formatted_team_ids, team_ids)
        slashgame = 1
        gamecheck(update, context, formatted_team_ids, team_ids);
        slashgame = 0
    if update.callback_query.data == 'yes':
        notification_pref = 1
        update.callback_query.answer()
        update.callback_query.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup([])
            )
        context.bot.deleteMessage(update.callback_query.message.chat.id, update.callback_query.message.message_id)
        updater.bot.sendMessage(chat_id=update.effective_chat.id, text = "You will receive Notifications!")
        databasemanagementnotifications(chat_id_noti, notification_pref);

    if update.callback_query.data == 'no':
        notification_pref = 0
        update.callback_query.answer()
        update.callback_query.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup([])
            )
        context.bot.deleteMessage(update.callback_query.message.chat.id, update.callback_query.message.message_id)
        updater.bot.sendMessage(chat_id=update.effective_chat.id, text = "You will not receive Notifications!")
        databasemanagementnotifications(chat_id_noti, notification_pref);


    update.callback_query.answer()
    val = update.callback_query.data
    team_ids.append(val)
    formatted_team_ids = ','.join(team_ids);

def databasemanagementteams(formatted_team_ids, team_ids):
    if exists == True:
        chat_index = chatsdf.index[chatsdf['ChatID'] == userid]
        chatsdf.loc[chat_index,'TeamIDs'] = formatted_team_ids;
        chatsdf.to_csv(chatdb, index = False, header=True)
    if exists == False:
        newchatdf = pd.DataFrame({"ChatName": [chatname], "ChatID": [userid], "TeamIDs": [formatted_team_ids]})
        updateddf = chatsdf.append(newchatdf, ignore_index=True)
        updateddf.to_csv(chatdb, index = False, header=True)

def databasemanagementnotifications(chat_id_noti, notification_pref):

        chatsdf = pd.read_csv(chatdb)
        chat_index = chatsdf.index[chatsdf['ChatID'] == chat_id_noti]
        chatsdf.loc[chat_index,'Notifications'] = notification_pref;
        chatsdf.to_csv(chatdb, index = False, header=True)

def gamecheck(update, context, formatted_team_ids, team_ids):
    global chatsdf
    chatsdf = pd.read_csv(chatdb)
    chat_index = int(chatsdf.index[chatsdf['ChatID'] == userid].values)
    chat_team_ids = chatsdf.loc[[chat_index], ['TeamIDs']].values
    formatted_chat_team_ids = str(chat_team_ids)[3:-3]

    api_url = f'https://statsapi.web.nhl.com/api/v1/schedule?teamId={formatted_chat_team_ids}&date={todays_date}'
    r = requests.get(api_url)
    team_data = r.json() 
    is_there_a_game = json.dumps(team_data['totalGames'])
    game_check = int(is_there_a_game)

    if seasoncheck == 0:
        game_check_msg = ("The NHL season has ended, come back next year!")

        context.bot.send_message(chat_id=chat_id_set, text=game_check_msg);
        return

    if game_check > 0:

        number_of_teams = game_check

        while number_of_teams > 0:

             number_of_teams = number_of_teams - 1

             playoff_check = json.dumps(team_data['dates'][0]['games'][0]['gameType']).strip('\"')

             if playoff_check == 'P':
                away_team =  json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['away']['team']['name'], ensure_ascii=False).encode('utf8')
                away_team_fin = away_team[1:-1]
                away_team_dec = str(away_team_fin.decode("utf8"))

                away_wins =  json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['away']['leagueRecord']['wins'])

                away_losses =  json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['away']['leagueRecord']['losses'])

                home_team =  json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['home']['team']['name'], ensure_ascii=False).encode('utf8')
                home_team_fin = home_team[1:-1]
                home_team_dec = str(home_team_fin.decode("utf8"))

                home_wins =  json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['home']['leagueRecord']['wins'])

                home_losses =  json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['home']['leagueRecord']['losses'])

                game_fulltime = json.dumps(team_data['dates'][0]['games'][number_of_teams]['gameDate'])
                game_time = game_fulltime[12:-2]
                game_time_obj = datetime.strptime(game_time, '%H:%M:%S') - timedelta(hours=4)
                game_time_est = datetime.strftime(game_time_obj, '%I:%M%p')

                away_wins_int = int(away_wins)
                home_wins_int = int(home_wins)
                away_games_won = away_wins_int % 4 
                home_games_won = home_wins_int % 4

                if  away_games_won > home_games_won:
                   leading_team = away_team_dec
                   leading_games = str(away_games_won)
                   trailing_games = str(home_games_won)
                if  away_games_won < home_games_won:
                   leading_team = home_team_dec
                   leading_games = str(home_games_won)
                   trailing_games = str(away_games_won)

                tie_check = away_games_won - home_games_won
                if tie_check != 0:
                   game_check_msg = ("The " + home_team_dec + "\n" + "Host" + "\n" + "The " + away_team_dec + "\n" + "At " + game_time_est + " est!" + "\n"
                      + "The " + leading_team + " Lead " + leading_games + " games to " + trailing_games + "!")

                   updater.bot.sendMessage(chat_id=chat_id_set, text = game_check_msg);

                if tie_check == 0:
                    if home_games_won ==1:
                        home_games_won_str = str(home_games_won)
                        game_check_msg = ("The " + home_team_dec + "\n" + "Host" + "\n" + "The " + away_team_dec + "\n" + game_day_of_week + " the " + game_day_str + " at " + game_time_est + " est!" + "\n"
                         + "The series is tied at "+ home_games_won_str + " game!")
                    else:
                        home_games_won_str = str(home_games_won)
                        game_check_msg = ("The " + home_team_dec + "\n" + "Host" + "\n" + "The " + away_team_dec + "\n" + game_day_of_week + " the " + game_day_str + " at " + game_time_est + " est!" + "\n"
                         + "The series is tied at "+ home_games_won_str + " games!")
                    updater.bot.sendMessage(chat_id=update.effective_chat.id, text = game_check_msg);

             if playoff_check == 'R':
                away_team =  json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['away']['team']['name'], ensure_ascii=False).encode('utf8')
                away_team_fin = away_team[1:-1]
                away_team_dec = str(away_team_fin.decode("utf8"))

                away_wins =  json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['away']['leagueRecord']['wins'])

                away_losses =  json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['away']['leagueRecord']['losses'])

                away_ot =  json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['away']['leagueRecord']['ot'])

                home_team =  json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['home']['team']['name'], ensure_ascii=False).encode('utf8')
                home_team_fin = home_team[1:-1]
                home_team_dec = str(home_team_fin.decode("utf8"))

                home_wins =  json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['home']['leagueRecord']['wins'])

                home_losses =  json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['home']['leagueRecord']['losses'])

                home_ot =  json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['home']['leagueRecord']['ot'])

                game_fulltime = json.dumps(team_data['dates'][0]['games'][number_of_teams]['gameDate'])
                game_time = game_fulltime[12:-2]
                game_time_obj = datetime.strptime(game_time, '%H:%M:%S') - timedelta(hours=4)
                game_time_est = datetime.strftime(game_time_obj, '%I:%M%p')

                game_check_msg = ("The " + home_team_dec + " (" + home_wins + "," + home_losses + "," + home_ot + ")" + "\n" + "Host" + "\n" + "The " + away_team_dec + " (" + away_wins + "," + away_losses + 
                                   "," + away_ot + ")" + "\n" + " at " + game_time_est + " est!")

                context.bot.send_message(chat_id=chat_id_set, text=game_check_msg);


    if game_check == 0 and slashgame == 1:
        game_check_msg = 'There is not a game today'

        context.bot.send_message(chat_id=chat_id_set, text=game_check_msg);

def nextgame(update, context):
    next_game_check_msg = "what?"
    next_game_request = update.message.text
    team_check = next_game_request [10:].lower()
    nextdf = pd.read_csv(teamsdb, index_col=None) 
    realteam = team_check in nextdf.TeamName.values
    if realteam == False:
        next_game_check_msg = "Sorry I don't know that team"
        context.bot.send_message(chat_id=update.effective_chat.id, text=next_game_check_msg);
        return;

    teamid__next_raw = nextdf.loc[nextdf.TeamName == team_check, 'TeamID']
    teamid__next = int(teamid__next_raw.values)

    api_url = f'https://statsapi.web.nhl.com/api/v1/teams/{teamid__next}?expand=team.schedule.next'
    r = requests.get(api_url)
    next_game = r.json()

    if seasoncheck == 0:
        next_game_check_msg = ("The NHL season has ended, come back next year!")

        context.bot.send_message(chat_id=update.effective_chat.id, text=next_game_check_msg);
        return;

    elimcheck = json.dumps(next_game['teams'][0])
    if 'nextGameSchedule' not in elimcheck:
        team_name = json.dumps(next_game['teams'][0]['name']).strip('"')
        next_game_check_msg = ("Ha, The " + team_name + " has been eliminated from Stanley Cup Contention. Sucks to suck")

        context.bot.send_message(chat_id=update.effective_chat.id, text=next_game_check_msg);
        return;

    playoff_check = json.dumps(next_game['teams'][0]['nextGameSchedule']['dates'][0]['games'][0]['gameType']).strip('\"')

    if playoff_check == 'P':

        away_team =  json.dumps(next_game['teams'][0]['nextGameSchedule']['dates'][0]['games'][0]['teams']['away']['team']['name'], ensure_ascii=False).encode('utf8')
        away_team_fin = away_team[1:-1]
        away_team_dec = str(away_team_fin.decode("utf8"))

        away_wins =  json.dumps(next_game['teams'][0]['nextGameSchedule']['dates'][0]['games'][0]['teams']['away']['leagueRecord']['wins'])

        away_losses =  json.dumps(next_game['teams'][0]['nextGameSchedule']['dates'][0]['games'][0]['teams']['away']['leagueRecord']['losses'])

        home_team =  json.dumps(next_game['teams'][0]['nextGameSchedule']['dates'][0]['games'][0]['teams']['home']['team']['name'], ensure_ascii=False).encode('utf8')
        home_team_fin = home_team[1:-1]
        home_team_dec = str(home_team_fin.decode("utf8"))

        home_wins =  json.dumps(next_game['teams'][0]['nextGameSchedule']['dates'][0]['games'][0]['teams']['home']['leagueRecord']['wins'])

        home_losses =  json.dumps(next_game['teams'][0]['nextGameSchedule']['dates'][0]['games'][0]['teams']['home']['leagueRecord']['losses'])

        game_fulltime = json.dumps(next_game['teams'][0]['nextGameSchedule']['dates'][0]['games'][0]['gameDate'])
        game_day = game_fulltime[1:-11]
        game_day_obj = datetime.strptime(game_day, '%Y-%m-%d')
        game_day_str = datetime.strftime(game_day_obj, '%d')
        game_day_int = int(game_day_str)
        game_day_of_week = datetime.strftime(game_day_obj, '%A')
        game_time = game_fulltime[12:-2]
        game_time_obj = datetime.strptime(game_time, '%H:%M:%S') - timedelta(hours=4)
        game_time_est = datetime.strftime(game_time_obj, '%I:%M%p')
        th_list = [4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,29,20,24,25,26,27,28,29,30]
        if game_day_int == 1 or game_day_int == 21 or game_day_int == 31:
            game_day_str += 'st'
        if game_day_int == 2 or game_day_int == 22:
            game_day_str += 'nd'
        if game_day_int == 3 or game_day_int == 23:
            game_day_str += 'rd'
        if game_day_int in th_list:
            game_day_str += 'th'

        away_wins_int = int(away_wins)
        home_wins_int = int(home_wins)
        away_games_won = away_wins_int % 4 
        home_games_won = home_wins_int % 4

        if  away_games_won > home_games_won:
           leading_team = away_team_dec
           leading_games = str(away_games_won)
           trailing_games = str(home_games_won)
        if  away_games_won < home_games_won:
           leading_team = home_team_dec
           leading_games = str(home_games_won)
           trailing_games = str(away_games_won)

        tie_check = away_games_won - home_games_won
        if tie_check != 0:
           next_game_check_msg = ("The " + home_team_dec + "\n" + "Host" + "\n" + "The " + away_team_dec + "\n" + game_day_of_week + " the " + game_day_str + " at " + game_time_est + " est!" + "\n"
              + "The " + leading_team + " Lead " + leading_games + " games to " + trailing_games + "!")

           updater.bot.sendMessage(chat_id=update.effective_chat.id, text = next_game_check_msg);

        if tie_check == 0:
            if home_games_won ==1:
                home_games_won_str = str(home_games_won)
                next_game_check_msg = ("The " + home_team_dec + "\n" + "Host" + "\n" + "The " + away_team_dec + "\n" + game_day_of_week + " the " + game_day_str + " at " + game_time_est + " est!" + "\n"
                 + "The series is tied at "+ home_games_won_str + " game!")
            else:
                home_games_won_str = str(home_games_won)
                next_game_check_msg = ("The " + home_team_dec + "\n" + "Host" + "\n" + "The " + away_team_dec + "\n" + game_day_of_week + " the " + game_day_str + " at " + game_time_est + " est!" + "\n"
                 + "The series is tied at "+ home_games_won_str + " games!")
            updater.bot.sendMessage(chat_id=update.effective_chat.id, text = next_game_check_msg);


    if playoff_check == 'R':
        away_team =  json.dumps(next_game['teams'][0]['nextGameSchedule']['dates'][0]['games'][0]['teams']['away']['team']['name'], ensure_ascii=False).encode('utf8')
        away_team_fin = away_team[1:-1]
        away_team_dec = str(away_team_fin.decode("utf8"))

        away_wins =  json.dumps(next_game['teams'][0]['nextGameSchedule']['dates'][0]['games'][0]['teams']['away']['leagueRecord']['wins'])

        away_losses =  json.dumps(next_game['teams'][0]['nextGameSchedule']['dates'][0]['games'][0]['teams']['away']['leagueRecord']['losses'])

        away_ot =  json.dumps(next_game['teams'][0]['nextGameSchedule']['dates'][0]['games'][0]['teams']['away']['leagueRecord']['ot'])

        home_team =  json.dumps(next_game['teams'][0]['nextGameSchedule']['dates'][0]['games'][0]['teams']['home']['team']['name'], ensure_ascii=False).encode('utf8')
        home_team_fin = home_team[1:-1]
        home_team_dec = str(home_team_fin.decode("utf8"))

        home_wins =  json.dumps(next_game['teams'][0]['nextGameSchedule']['dates'][0]['games'][0]['teams']['home']['leagueRecord']['wins'])

        home_losses =  json.dumps(next_game['teams'][0]['nextGameSchedule']['dates'][0]['games'][0]['teams']['home']['leagueRecord']['losses'])

        home_ot =  json.dumps(next_game['teams'][0]['nextGameSchedule']['dates'][0]['games'][0]['teams']['home']['leagueRecord']['ot'])

        game_fulltime = json.dumps(next_game['teams'][0]['nextGameSchedule']['dates'][0]['games'][0]['gameDate'])
        game_day = game_fulltime[1:-11]
        game_day_obj = datetime.strptime(game_day, '%Y-%m-%d')
        game_day_str =datetime.strftime(game_day_obj, '%m / %d / %Y')
        game_day_of_week = datetime.strftime(game_day_obj, '%A')
        game_time = game_fulltime[12:-2]
        game_time_obj = datetime.strptime(game_time, '%H:%M:%S') - timedelta(hours=4)
        game_time_est = datetime.strftime(game_time_obj, '%I:%M%p')
        th_list = [4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,29,20,24,25,26,27,28,29,30]
        if game_day_int == 1 or game_day_int == 21 or game_day_int == 31:
            game_day_str += 'st'
        if game_day_int == 2 or game_day_int == 22:
            game_day_str += 'nd'
        if game_day_int == 3 or game_day_int == 23:
            game_day_str += 'rd'
        if game_day_int in th_list:
            game_day_str += 'th'

        next_game_check_msg = ("The " + home_team_dec + " (" + home_wins + "," + home_losses + "," + home_ot + ")" + "\n" + "Host" + "\n" + "The " + away_team_dec + " (" + away_wins + 
                            "," + away_losses + "," + away_ot + ")" + "\n" + game_day_of_week + " the " + game_day_str + " at " + game_time_est + " est!")

        context.bot.send_message(chat_id=update.effective_chat.id, text=next_game_check_msg);
    context.bot.send_message(chat_id=update.effective_chat.id, text=next_game_check_msg);



#runs gamecheck for the chat that /game was sent in
def game(update, context):
    global slashgame
    global userid
    global formatted_team_ids
    global chat_id_set
    slashgame = 1
    chat_id_set = update.effective_chat.id
    formatted_team_ids = []
    userid = update.message.chat.id
    gamecheck(update, context, formatted_team_ids, team_ids);
    slashgame = 0

#sends a help message when /help is received
def helpcmd(update, context):
    help_msg = (
        "Here is a list of my commands:" + "\n" + "\n" + 
        "/setup" + "\n" + "select which teams you would like notifications for" + "\n" + "\n" + 
        "/game" + "\n" + "manually check if a team you selected has a game today" + "\n" + "\n" + 
        "/nextgame <team name>" + "\n" + "find the time of the next game for a team. e.g. /nextgame Penguins" + "\n" + "\n" + 
        "/lastgame <team name>" + "\n" + "find the score of the last game for a team. e.g /lastgame Penguins" + "\n" + "\n" +
        "/notifications" + "\n" + "enable and disable daily game notifications" + "\n" + "\n" + 
        "/status" + "\n" + "get a list of the teams you are following" + "\n" + "and your notification preferences" + "\n" + "\n" + 
        "/cupcheck" + "\n" + "Important stats" + "\n" + "\n" + 
        "/help" + "\n" + "opens this list of commands" + "\n" + "\n" + 
        "Thank you for using my bot!" + "\n" + "\n" + 
        "Made by Ben Finley" + "\n" + 
        "The code for this bot is avalible at: https://github.com/Hiben75/TelegramNHLNotifcationBot"
        )
    context.bot.send_message(chat_id=update.effective_chat.id, text=help_msg, disable_web_page_preview=1);

def automation():
    global userid
    global chat_id_set
    global todays_date
    todays_date = date.today()
    chatsdf = pd.read_csv(chatdb)
    chats_with_notifications = list(chatsdf.loc[chatsdf['Notifications'] == 1, 'ChatID'])

    while len(chats_with_notifications) != 0:
        chat = chats_with_notifications[0]
        userid = chat
        autimaticgamenotification()
        chats_with_notifications.remove(chats_with_notifications[0])
    timer ()

def autimaticgamenotification():

    global chatsdf
    chatsdf = pd.read_csv(chatdb)
    chat_index = int(chatsdf.index[chatsdf['ChatID'] == userid].values)
    chat_team_ids = chatsdf.loc[[chat_index], ['TeamIDs']].values
    formatted_chat_team_ids = str(chat_team_ids)[3:-3]

    api_url = f'https://statsapi.web.nhl.com/api/v1/schedule?teamId={formatted_chat_team_ids}&date={todays_date}'
    r = requests.get(api_url)
    team_data = r.json() 
    is_there_a_game = json.dumps(team_data['totalGames'])
    game_check = int(is_there_a_game)

    if seasoncheck == 0:
        return

    if game_check > 0:

        number_of_teams = game_check

        while number_of_teams > 0:

             number_of_teams = number_of_teams - 1

             playoff_check = json.dumps(team_data['dates'][0]['games'][0]['gameType']).strip('\"')

             if playoff_check == 'P':
                away_team =  json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['away']['team']['name'], ensure_ascii=False).encode('utf8')
                away_team_fin = away_team[1:-1]
                away_team_dec = str(away_team_fin.decode("utf8"))

                away_wins =  json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['away']['leagueRecord']['wins'])

                away_losses =  json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['away']['leagueRecord']['losses'])


                home_team =  json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['home']['team']['name'], ensure_ascii=False).encode('utf8')
                home_team_fin = home_team[1:-1]
                home_team_dec = str(home_team_fin.decode("utf8"))

                home_wins =  json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['home']['leagueRecord']['wins'])

                home_losses =  json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['home']['leagueRecord']['losses'])


                game_fulltime = json.dumps(team_data['dates'][0]['games'][number_of_teams]['gameDate'])
                game_time = game_fulltime[12:-2]
                game_time_obj = datetime.strptime(game_time, '%H:%M:%S') - timedelta(hours=4)
                game_time_est = datetime.strftime(game_time_obj, '%I:%M%p')

                away_wins_int = int(away_wins)
                home_wins_int = int(home_wins)
                away_games_won = away_wins_int % 4 
                home_games_won = home_wins_int % 4

                if  away_games_won > home_games_won:
                   leading_team = away_team_dec
                   leading_games = str(away_games_won)
                   trailing_games = str(home_games_won)
                if  away_games_won < home_games_won:
                   leading_team = home_team_dec
                   leading_games = str(home_games_won)
                   trailing_games = str(away_games_won)

                tie_check = away_games_won - home_games_won
                if tie_check != 0:
                   game_check_msg = ("The " + home_team_dec + "\n" + "Host" + "\n" + "The " + away_team_dec + "\n" + "At " + game_time_est + " est!" + "\n"
                      + "The " + leading_team + " Lead " + leading_games + " games to " + trailing_games + "!")

                   updater.bot.sendMessage(chat_id=userid, text = game_check_msg);

                if tie_check == 0:
                    home_games_won_str = str(home_games_won)
                    game_check_msg = ("The " + home_team_dec + "\n" + "Host" + "\n" + "The " + away_team_dec + "\n" + "At " + game_time_est + " est!" + "\n"
                     + "The series is tied at "+ home_games_won_str + " games!")

                    updater.bot.sendMessage(chat_id=userid, text = game_check_msg);


                if playoff_check == 'R':
                   away_team =  json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['away']['team']['name'], ensure_ascii=False).encode('utf8')
                   away_team_fin = away_team[1:-1]
                   away_team_dec = str(away_team_fin.decode("utf8"))

                   away_wins =  json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['away']['leagueRecord']['wins'])

                   away_losses =  json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['away']['leagueRecord']['losses'])

                   away_ot =  json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['away']['leagueRecord']['ot'])

                   home_team =  json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['home']['team']['name'], ensure_ascii=False).encode('utf8')
                   home_team_fin = home_team[1:-1]
                   home_team_dec = str(home_team_fin.decode("utf8"))

                   home_wins =  json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['home']['leagueRecord']['wins'])

                   home_losses =  json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['home']['leagueRecord']['losses'])

                   home_ot =  json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['home']['leagueRecord']['ot'])

                   game_fulltime = json.dumps(team_data['dates'][0]['games'][number_of_teams]['gameDate'])
                   game_time = game_fulltime[12:-2]
                   game_time_obj = datetime.strptime(game_time, '%H:%M:%S') - timedelta(hours=4)
                   game_time_est = datetime.strftime(game_time_obj, '%I:%M%p')

                   game_check_msg = ("The " + home_team_dec + "\n" + "Host" + "\n" + "The " + away_team_dec + "\n" + " at " + game_time_est + " est!" + "\n"
                      + "The " + leading_team + " Lead " + leading_games + " games to" + trailing_games + "!")

                   updater.bot.sendMessage(chat_id=userid, text = game_check_msg);

def last(update, context):
    last_game_request = update.message.text
    team_check = last_game_request [10:].lower()
    lastdf = pd.read_csv(teamsdb, index_col=None) 
    realteam = team_check in lastdf.TeamName.values
    if realteam == False:
        next_game_check_msg = "Sorry I don't know that team"
        context.bot.send_message(chat_id=update.effective_chat.id, text=next_game_check_msg);
        return;

    teamid__last_raw = lastdf.loc[lastdf.TeamName == team_check, 'TeamID']
    teamid__last = int(teamid__last_raw.values)

    api_url = f'https://statsapi.web.nhl.com/api/v1/teams/{teamid__last}?expand=team.schedule.previous'
    r = requests.get(api_url)
    next_game = r.json()

    game_pk =  json.dumps(next_game['teams'][0]['previousGameSchedule']['dates'][0]['games'][0]['gamePk'])

    api2_url = f'https://statsapi.web.nhl.com/api/v1/game/{game_pk}/feed/live'
    r2 = requests.get(api2_url)
    last_game_stats = r2.json()

    home_team =  json.dumps(last_game_stats['liveData']['linescore']['teams']['home']['team']['name'], ensure_ascii=False).encode('utf8')
    home_team_fin = home_team[1:-1]
    home_team_dec = str(home_team_fin.decode("utf8"))

    away_team =  json.dumps(last_game_stats['liveData']['linescore']['teams']['away']['team']['name'], ensure_ascii=False).encode('utf8')
    away_team_fin = away_team[1:-1]
    away_team_dec = str(away_team_fin.decode("utf8"))


    away_team_score =  json.dumps(last_game_stats['liveData']['linescore']['teams']['away']['goals'])
    home_team_score =  json.dumps(last_game_stats['liveData']['linescore']['teams']['home']['goals'])


    overtime_check =  int(json.dumps(last_game_stats['liveData']['linescore']['currentPeriod']))

    if overtime_check == 3:
        overtime_msg = ''
    if overtime_check == 4:
        overtime_msg = 'In Overtime!'
    if overtime_check == 5:
        overtime_msg = 'In a Shootout!'

    if away_team_score > home_team_score:
        last_game_msg = ("The " + away_team_dec + ":    " + away_team_score + "\n" + " The " + home_team_dec + ":    " + home_team_score + "\n" + overtime_msg)
    if home_team_score > away_team_score:
        last_game_msg =  ("The " + home_team_dec + ":    " + home_team_score + "\n" + " The " + away_team_dec + ":    " + away_team_score + "\n" + overtime_msg)

    updater.bot.sendMessage(chat_id=update.effective_chat.id, text = last_game_msg);


def notifications(update: Update, context: CallbackContext):
    global chat_id_noti
    chat_id_noti = update.message.chat.id
    chatsdf = pd.read_csv(chatdb)
    notiexists = chatsdf.index[chatsdf['ChatID'] == chat_id_noti].values
    if notiexists.size > 0:            
        reply_buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Yes", callback_data='yes'),
                InlineKeyboardButton("No", callback_data='no')
            ],    
        ])
        update.message.reply_text(
            f'Would you like daily game notifications?' + "\n" + "Notifications are sent at 8am est.", reply_markup=reply_buttons
            )
        return;

    updater.bot.sendMessage(chat_id=update.effective_chat.id, text = "Please run /setup first!");

#Tells the user what teams the are following and if they are getting daily notifications
def status(update, context):
    usersteams = ''
    usersteamslist = ''
    chat_id_status = update.message.chat.id
    chatsdf = pd.read_csv(chatdb)
    teamnamesdf = pd.read_csv(teamsdb, encoding = "ISO-8859-1")
    usersteamsids = list(chatsdf.loc[chatsdf['ChatID'] == chat_id_status, 'TeamIDs'].values)
    usersteamsidsform = str(usersteamsids)[2:-2]
    usersteamsidslist = [int(x) for x in usersteamsidsform.split(',')]
    formattedteamsdf = teamnamesdf.loc[teamnamesdf['Formatted'] == 1]
    while len(usersteamsidslist) > 0:
        team = usersteamsidslist[0]
        usersteams = formattedteamsdf.loc[formattedteamsdf['TeamID'] == team, 'TeamName'].values
        usersteamslist = usersteamslist + usersteams + '?The '
        usersteamsidslist.remove(team)
    isusernotifi = chatsdf.loc[chatsdf['ChatID'] == chat_id_status, 'Notifications'].values
    if isusernotifi == 0:
        notif_status = 'are not'
    if isusernotifi == 1:
        notif_status = 'are'
    finalteamslist = str(usersteamslist)[2:-7]
    status_message = ('You are following:' + '\n' + 'The ' + finalteamslist.replace('?', '\n') + '\n' +'\n' + 'You ' + notif_status + 
                      ' receiving daily notifications.')
    updater.bot.sendMessage(chat_id=update.effective_chat.id, text = status_message);

#Tells the user the days since the Flyers and the Penguins have won the cup
#Lets Go Pens!
def cupcheck(update, context):
    f_Date = date(1975, 5, 27)
    f_sincecup = f_Date - todays_date
    f_dayssincecup = str(f_sincecup.days)[1:]

    p_Date = date(2017, 6, 11)
    p_sincecup = p_Date - todays_date
    p_dayssincecup = str(p_sincecup.days)[1:]

    cup_msg = ('It has been ' + f_dayssincecup + ' days since the Flyers have won the Stanley Cup.' + '\n' + 'It has been ' + p_dayssincecup + ' days since the Penguins have won the Stanley Cup.'+ '\n' + 'Lets Go Pens!')
    updater.bot.sendMessage(chat_id=update.effective_chat.id, text = cup_msg);

#DEBUG sends what the bot thinks today is
def today(update, context):
    today_msg = str(todays_date)
    updater.bot.sendMessage(chat_id=update.effective_chat.id, text = today_msg);

#Send notification at 8am every day
def timer ():
    x=datetime.today()
    y = x.replace(day=x.day, hour=8, minute=0, second=0, microsecond=0) + timedelta(days=1)
    delta_t=y-x

    secs=delta_t.total_seconds()

    t = Timer(secs, automation)
    t.start()

#stop the bot
def stop(update, context):
    if update.message.chat.id == 110799848:
        updater.bot.sendMessage(chat_id=update.effective_chat.id, text = 'Shuting Down');
        updater.stop()
        updater.is_idle = False

def testautonotify(update, context):
    if update.message.chat.id == 110799848:
        updater.bot.sendMessage(chat_id=update.effective_chat.id, text = 'Testing Automatic Notifications');
        automation()

#starts automation
timer()

#dispatcher for each command
dispatcher.add_handler(CommandHandler('setup', setup))
dispatcher.add_handler(CallbackQueryHandler(button))
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('game', game))
dispatcher.add_handler(CommandHandler('nextgame', nextgame))
dispatcher.add_handler(CommandHandler('help', helpcmd))
dispatcher.add_handler(CommandHandler('lastgame', last))
dispatcher.add_handler(CommandHandler('notifications', notifications))
dispatcher.add_handler(CommandHandler('status', status))
dispatcher.add_handler(CommandHandler('cupcheck', cupcheck))
dispatcher.add_handler(CommandHandler('stop', stop))
dispatcher.add_handler(CommandHandler('testautonotify', testautonotify))



updater.start_polling()

updater.idle()
