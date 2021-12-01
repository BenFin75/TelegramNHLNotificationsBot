# -----------------------------------------------------------
# NHL Game Notifications Bot
# Telegram bot for receiving daily NHL game notifications 
# as well other information about the league and palyers
#
# Created by Benjamin Finley
# Code is availible on GitHub @ https://github.com/Hiben75/TelegramNHLNotifcationBot
# 
# Version 1.5.1
# Status: Active
#
# -----------------------------------------------------------


# !/usr/bin/ env python
# -*- coding: utf-8 -*-
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
import prettytable as pt
import pytz

# configures logging for development
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# gets the bot token from remote database so the code can be made public
bot_token_df = pd.read_csv((os.path.join(
                                        os.path.dirname(os.getcwd()), "TelegramBotTokens.csv")))
bot_index = int(bot_token_df.index[bot_token_df['Bot Name'] == 'Hockey Bot'].values)
bot_token = str(bot_token_df.loc[[bot_index], ['Bot Token']].values).strip("'[]")
bot = Bot(bot_token)  # noqa: F405
updater = Updater(bot_token, use_context=True)

# set the database paths so the bot works on any OS.
chatdb_win = PureWindowsPath('.\Database\ChatDatabase.csv')
teamsdb_win = PureWindowsPath('.\Database\TeamNames.csv')
todaysdb_win = PureWindowsPath('./Database/todaysgames.csv')
todays_db = Path(todaysdb_win)
chatdb = Path(chatdb_win)
teamsdb = Path(teamsdb_win)


team_ids = []
todays_date = date.today()
zone = 'US/Eastern'
dst_check = bool(datetime.now(pytz.timezone(zone)).dst())

def seasoncheck(chat_id_set, autonotify):
    """
        checks if the nhl is currently in season by seening if there are any games this month
    """
    a_month_from_now = todays_date + relativedelta(months=1)
    api_url = f'https://statsapi.web.nhl.com/api/v1/schedule?startDate={todays_date}&endDate={a_month_from_now}'
    r = requests.get(api_url)
    json = r.json() 
    numofgame = json['totalItems']
    if numofgame == 0:
        if autonotify == 1:
            return False
        else:
            game_check_msg = ("The NHL season has ended, come back next year!")
            updater.bot.sendMessage(chat_id=chat_id_set, text=game_check_msg)
            return False
    else:
        return True


def start(update, context):
    """
        Welcome message explaining the bot.
        The /start command is sent automatically whenever a user begins a new converstation with the bot
        it can also be called at anytiem with the /start command
    """
    welcome_msg = (
        "Hello!  Welcome to the NHL game notifications bot!" + "\n" + "\n" + 
        "Type /setup to get started, or /help for a list of commands." + "\n" + "\n" + 
        "Made by Ben Finley" + "\n" + 
        "The code for this bot is avalible at: https://github.com/Hiben75/TelegramNHLNotifcationBot"
        )
    context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_msg, disable_web_page_preview=1)


def helpcmd(update, context):
    """
        Help command giving a list of the bots command, what they do, and how to use them
    """
    help_msg = (
        "Here is a list of my commands:" + "\n" + "\n" + 
        "/setup" + "\n" + "select which teams you would like notifications for" + "\n" + "\n" + 
        "/game" + "\n" + "manually check if a team you selected has a game today" + "\n" + "\n" + 
        "/nextgame <team name>" + "\n" + "find the time of the next game for a team. e.g. /nextgame Penguins" + "\n" + "\n" + 
        "/lastgame <team name>" + "\n" + "find the score of the last game for a team. e.g /lastgame Penguins" + "\n" + "\n" +
        "/notifications" + "\n" + "enable and disable daily game notifications" + "\n" + "\n" + 
        "/status" + "\n" + "get a list of the teams you are following" + "\n" + "and your notification preferences" + "\n" + "\n" + 
        "/roster <team name>" + "\n" + "get the active roster for a given team e.g /roster Penguins" + "\n" + "\n" + 
        "/player <team name> <player>" + "\n" + "get the numer, full name, and position for a player" + "\n" + " e.g /player Penguins 87 or /player Penguins Crosby" + "\n" + "\n" + 
        "/stats <team name>" + "\n" + "/stats <team name> <player>" + "\n" + "get the regular season stats for a given team or player" + "\n" + " e.g /stats Penguins, /stats Penguins 87, or /stats Penguins Crosby" + "\n" + "\n" + 
        "/standings <division name>" + "\n" + "get the standings for a given division e.g /standings Pacific" + "\n" + "If left blank /standings will retrun all division stnadings" "\n" + "\n" + 
        "/cupcheck" + "\n" + "Important stats" + "\n" + "\n" + 
        "/removeMe" + "\n" + "Delete your teams and notification data." + "\n" + "\n" + 
        "/help" + "\n" + "opens this list of commands" + "\n" + "\n" + 
        "Thank you for using my bot!" + "\n" + "\n" + 
        "Made by Ben Finley" + "\n" + 
        "The code for this bot is avalible at: https://github.com/BenFin75/TelegramNHLNotifcationBot"
        )
    context.bot.send_message(chat_id=update.effective_chat.id, text=help_msg, disable_web_page_preview=1)


def setup(update, context: CallbackContext):
    """
        The command to allow the user to select which teams they wish to follow
        these teams are the teams checked for with /game and by the automatic notifications
    """
    team_ids.clear()

    # These are needed becasue the button fuction does not get variables form setup to pass on
    global chatsdf
    global userid
    global chatname
    global exists

    chatsdf = pd.read_csv(chatdb)
    userid = update.effective_chat.id
    if userid > 0:
        chatname = update.message.chat.username
    if userid < 0:
        chatname = update.message.chat.title
    exists = userid in chatsdf.ChatID.values
    reply_buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Penguins", callback_data=5),
            InlineKeyboardButton("Leafs", callback_data=10)
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
            InlineKeyboardButton("Canes", callback_data=12),
            InlineKeyboardButton("Panthers", callback_data=13)
        ],
        [
            InlineKeyboardButton("Bolts", callback_data=14),
            InlineKeyboardButton("Capitals", callback_data=15),
            InlineKeyboardButton("Hawks", callback_data=16),
            InlineKeyboardButton("Wings", callback_data=17),
            InlineKeyboardButton("Predators", callback_data=18)
            ],
        [
            InlineKeyboardButton("Blues", callback_data=19),
            InlineKeyboardButton("Flames", callback_data=20),
            InlineKeyboardButton("Avs", callback_data=21),
            InlineKeyboardButton("Oilers", callback_data=22),
            InlineKeyboardButton("Canucks", callback_data=23)
        ],
        [
            InlineKeyboardButton("Ducks", callback_data=24),
            InlineKeyboardButton("Stars", callback_data=25),
            InlineKeyboardButton("Kings", callback_data=26),
            InlineKeyboardButton("Sharks", callback_data=28),
            InlineKeyboardButton("Jackets", callback_data=29)
        ],
        [
            InlineKeyboardButton("Wild", callback_data=30),
            InlineKeyboardButton("Jets", callback_data=52),
            InlineKeyboardButton("Coyotes", callback_data=53),
            InlineKeyboardButton("Knights", callback_data=54),
            InlineKeyboardButton("Kraken", callback_data=55)
        ],
        [
            InlineKeyboardButton("Done", callback_data='✔️'),
        ]
    ])
    update.message.reply_text(
        f'Hello {update.effective_user.first_name}, What teams would you like notifications for?'
        + "\n" + "When all teams have been added, click Done",
        reply_markup=reply_buttons
    )


def button(update, context: CallbackContext):
    """
        This is the handler for the buttons called in other funtions
        When the buttons are clicked this function receives the output

    """
    global formatted_team_ids
    global chat_id_set

    # The button handler for pressing done when setting up the teams a user wants to follow
    if update.callback_query.data == '✔️':
        chat_id_set = update.effective_chat.id
        update.callback_query.answer()
        # removes the buttons after selection
        update.callback_query.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup([])
            )
        # removes the text sent with the buttons and replaces it with a new message
        context.bot.deleteMessage(update.callback_query.message.chat.id, update.callback_query.message.message_id)
        setup_msg = ('Your team preferences have been updated!')
        context.bot.send_message(chat_id=update.effective_chat.id, text=setup_msg)
        databasemanagementteams(formatted_team_ids, team_ids)
        game(update, context)
        notifications(update, context)

    # The button handler for turning on notifications for a user
    if update.callback_query.data == 'yes':
        notification_pref = 1
        update.callback_query.answer()
        update.callback_query.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup([])
            )
        context.bot.deleteMessage(update.callback_query.message.chat.id, update.callback_query.message.message_id)
        updater.bot.sendMessage(chat_id=update.effective_chat.id, text="You will receive Notifications!")
        databasemanagementnotifications(chat_id_noti, notification_pref)

    #The button handler for turning off notifications for a user
    if update.callback_query.data == 'no':
        notification_pref = 0
        update.callback_query.answer()
        update.callback_query.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup([])
            )
        context.bot.deleteMessage(update.callback_query.message.chat.id, update.callback_query.message.message_id)
        updater.bot.sendMessage(chat_id=update.effective_chat.id, text="You will not receive Notifications!")
        databasemanagementnotifications(chat_id_noti, notification_pref)

    if update.callback_query.data == 'bye':
        chatsdf = pd.read_csv(chatdb)
        chatsdf_removed = chatsdf[chatsdf['ChatID'] != chat_id_noti]
        chatsdf_removed.to_csv(chatdb, index=False, header=True)
        update.callback_query.answer()
        update.callback_query.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup([])
            )
        context.bot.deleteMessage(update.callback_query.message.chat.id, update.callback_query.message.message_id)
        updater.bot.sendMessage(chat_id=update.effective_chat.id, text="Your team and notification data has been deleted." + "\n" + "You can run /setup to start again." + "\n" + "Thanks for using my bot, bye!")

    if update.callback_query.data == 'stay':
        update.callback_query.answer()
        update.callback_query.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup([])
            )
        context.bot.deleteMessage(update.callback_query.message.chat.id, update.callback_query.message.message_id)
        updater.bot.sendMessage(chat_id=update.effective_chat.id, text="Your team and notification data are safe")

    # adds the users team selection to their list of followed teams
    other_buttons = ['✔️', 'yes', 'no', 'bye', 'stay']
    if update.callback_query.data not in other_buttons:
        update.callback_query.answer()
        val = update.callback_query.data
        team_ids.append(val)
        formatted_team_ids = ','.join(team_ids)


def databasemanagementteams(formatted_team_ids, team_ids):
    """
        Modifys the chat database to update what teams the user/chat is following
    """
    if exists is True:
        chat_index = chatsdf.index[chatsdf['ChatID'] == userid]
        chatsdf.loc[chat_index, 'TeamIDs'] = formatted_team_ids
        chatsdf.to_csv(chatdb, index=False, header=True)
    if exists is False:
        newchatdf = pd.DataFrame({"ChatName": [chatname], "ChatID": [userid], "TeamIDs": [formatted_team_ids]})
        updateddf = chatsdf.append(newchatdf, ignore_index=True)
        updateddf.to_csv(chatdb, index=False, header=True)


def databasemanagementnotifications(chat_id_noti, notification_pref):
    """
        Modifys the chat database to update if the user/chat wants daily notifications
    """
    chatsdf = pd.read_csv(chatdb)
    chat_index = chatsdf.index[chatsdf['ChatID'] == chat_id_noti]
    chatsdf.loc[chat_index, 'Notifications'] = notification_pref
    chatsdf.to_csv(chatdb, index=False, header=True)


def teamdatabasecheck(update, context, team_name):
    """
        Sends a message if the user submits an unsupported team name
    """
    teamdf = pd.read_csv(teamsdb, index_col=None) 
    if team_name not in teamdf.TeamName.values:
        unknown_team_msg = "Sorry I don't know that team."
        context.bot.send_message(chat_id=update.effective_chat.id, text=unknown_team_msg)
        return False
    else:
        return True


def nextgame(update, context):
    """
        Returns the date and opponent for the next game 
        for the team submitted by the user
    """
    next_game_request = update.message.text
    if next_game_request.count(' ') == 0:
        context.bot.send_message(chat_id=update.effective_chat.id, text=("Please indicate the team you want the next game for." + '\n' + "e.g. /nextgame Pens"))
        return
    team_name = next_game_request[10:].lower()
    nextdf = pd.read_csv(teamsdb, index_col=None) 
    if not teamdatabasecheck(update, context, team_name):
        return

    teamid_next_raw = nextdf.loc[nextdf.TeamName == team_name, 'TeamID']
    teamid_next = int(teamid_next_raw.values)
    api_url = f'https://statsapi.web.nhl.com/api/v1/teams/{teamid_next}?expand=team.schedule.next'
    r = requests.get(api_url)
    next_game = r.json()
    autonotify = 0
    chat_id_set = update.effective_chat.id
    if not seasoncheck(chat_id_set, autonotify):
        return
    elimcheck = json.dumps(next_game['teams'][0])
    if 'nextGameSchedule' not in elimcheck:
        formatted_teams_df = nextdf.loc[nextdf['Formatted'] == 1]
        teamid_name_form = str(formatted_teams_df.loc[formatted_teams_df.TeamID == teamid_next, 'TeamName'].values).strip("'[]")
        apiL_url = f'https://statsapi.web.nhl.com/api/v1/teams/{teamid_next}?expand=team.schedule.previous'
        rL = requests.get(apiL_url)
        last_game = rL.json()
        playoff_check =       json.dumps(last_game['teams'][0]['previousGameSchedule']['dates'][0]['games'][0]['gameType']).strip('\"')
        away_team_score = int(json.dumps(last_game['teams'][0]['previousGameSchedule']['dates'][0]['games'][0]['teams']['away']['score']))
        home_team_score = int(json.dumps(last_game['teams'][0]['previousGameSchedule']['dates'][0]['games'][0]['teams']['home']['score']))
        away_team_id =    int(json.dumps(last_game['teams'][0]['previousGameSchedule']['dates'][0]['games'][0]['teams']['away']['team']['id']))
        home_team_id =    int(json.dumps(last_game['teams'][0]['previousGameSchedule']['dates'][0]['games'][0]['teams']['home']['team']['id']))
        if away_team_score > home_team_score and away_team_id == teamid_next and playoff_check == 'P' or home_team_score > away_team_score and home_team_id == teamid_next and playoff_check == 'P':
            next_game_check_msg = (
                                    "The " + teamid_name_form + " have won their playoff series." + "\n" + "The next game has yet to be scheduled." + "\n" + "\n" +
                                    "This is probably due to the next opponent still playing their series." + "\n" + 
                                    "Please check back later."
                                    )
            context.bot.send_message(chat_id=update.effective_chat.id, text=next_game_check_msg)
            return
        else:
            next_game_check_msg = ("Ha, The " + teamid_name_form + " have been eliminated from Stanley Cup Contention. Sucks to suck")
            context.bot.send_message(chat_id=update.effective_chat.id, text=next_game_check_msg)
            return

    # the encoding is so that Montréal has its é, can't forget that
    away_team =     json.dumps(next_game['teams'][0]['nextGameSchedule']['dates'][0]['games'][0]['teams']['away']['team']['name'], ensure_ascii=False).encode('utf8')
    away_team_fin = away_team[1:-1]
    away_team_dec = str(away_team_fin.decode("utf8"))
    away_wins =     json.dumps(next_game['teams'][0]['nextGameSchedule']['dates'][0]['games'][0]['teams']['away']['leagueRecord']['wins'])
    away_losses =   json.dumps(next_game['teams'][0]['nextGameSchedule']['dates'][0]['games'][0]['teams']['away']['leagueRecord']['losses'])
    home_team =     json.dumps(next_game['teams'][0]['nextGameSchedule']['dates'][0]['games'][0]['teams']['home']['team']['name'], ensure_ascii=False).encode('utf8')
    home_team_fin = home_team[1:-1]
    home_team_dec = str(home_team_fin.decode("utf8"))
    home_wins =     json.dumps(next_game['teams'][0]['nextGameSchedule']['dates'][0]['games'][0]['teams']['home']['leagueRecord']['wins'])
    home_losses =   json.dumps(next_game['teams'][0]['nextGameSchedule']['dates'][0]['games'][0]['teams']['home']['leagueRecord']['losses'])
    game_fulltime = json.dumps(next_game['teams'][0]['nextGameSchedule']['dates'][0]['games'][0]['gameDate'])
    game_day_full = json.dumps(next_game['teams'][0]['nextGameSchedule']['dates'][0]['date'])
    game_day = game_day_full[1:-1]
    game_day_obj = datetime.strptime(game_day, '%Y-%m-%d')
    game_day_str = datetime.strftime(game_day_obj, '%d')
    game_day_int = int(game_day_str)
    game_day_txt = str(game_day_int)
    print (game_day_txt)
    game_day_of_week = datetime.strftime(game_day_obj, '%A')
    game_time = game_fulltime[12:-2]
    if dst_check == True:
        game_time_obj = datetime.strptime(game_time, '%H:%M:%S') - timedelta(hours=4)
    if dst_check ==False:
        game_time_obj = datetime.strptime(game_time, '%H:%M:%S') - timedelta(hours=5)
    game_time_est = datetime.strftime(game_time_obj, '%-I:%M%p')

    th_list = [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 29, 20, 24, 25, 26, 27, 28, 29, 30]
    if game_day_int == 1 or game_day_int == 21 or game_day_int == 31:
        game_day_txt += 'st'
    if game_day_int == 2 or game_day_int == 22:
        game_day_txt += 'nd'
    if game_day_int == 3 or game_day_int == 23:
        game_day_txt += 'rd'
    if game_day_int in th_list:
        game_day_txt += 'th'

    playoff_check = json.dumps(next_game['teams'][0]['nextGameSchedule']['dates'][0]['games'][0]['gameType']).strip('\"')
    if playoff_check == 'P':
        away_games_won = int(away_wins) % 4 
        home_games_won = int(home_wins) % 4
        if away_games_won > home_games_won:
            leading_team = away_team_dec
            leading_games = str(away_games_won)
            trailing_games = str(home_games_won)
        if away_games_won < home_games_won:
            leading_team = home_team_dec
            leading_games = str(home_games_won)
            trailing_games = str(away_games_won)
        tie_check = away_games_won - home_games_won
        if tie_check != 0:
            if leading_games == 1:
                next_game_check_msg = ("The " + home_team_dec + "\n" + "Host" + "\n" + "The " + away_team_dec + "\n" + game_day_of_week + " the " + game_day_txt + " at " + game_time_est + " est!" + "\n"
                                       + "The " + leading_team + " Lead " + leading_games + " game to " + trailing_games + "!")
            else:
                next_game_check_msg = ("The " + home_team_dec + "\n" + "Host" + "\n" + "The " + away_team_dec + "\n" + game_day_of_week + " the " + game_day_txt + " at " + game_time_est + " est!" + "\n"
                                       + "The " + leading_team + " Lead " + leading_games + " games to " + trailing_games + "!")
            updater.bot.sendMessage(chat_id=update.effective_chat.id, text=next_game_check_msg)
        if tie_check == 0:
            home_games_won_str = str(home_games_won)
            if home_games_won == 1:
                next_game_check_msg = ("The " + home_team_dec + "\n" + "Host" + "\n" + "The " + away_team_dec + "\n" + game_day_of_week + " the " + game_day_txt + " at " + game_time_est + " est!" + "\n"
                                       + "The series is tied at " + home_games_won_str + " game!")
            else:
                next_game_check_msg = ("The " + home_team_dec + "\n" + "Host" + "\n" + "The " + away_team_dec + "\n" + game_day_of_week + " the " + game_day_txt + " at " + game_time_est + " est!" + "\n"
                                       + "The series is tied at " + home_games_won_str + " games!")
            updater.bot.sendMessage(chat_id=update.effective_chat.id, text=next_game_check_msg)

    if playoff_check == 'R':
        away_ot = json.dumps(next_game['teams'][0]['nextGameSchedule']['dates'][0]['games'][0]['teams']['away']['leagueRecord']['ot'])
        home_ot = json.dumps(next_game['teams'][0]['nextGameSchedule']['dates'][0]['games'][0]['teams']['home']['leagueRecord']['ot'])

        next_game_check_msg = ("The " + home_team_dec + " (" + home_wins + "," + home_losses + "," + home_ot + ")" + "\n" + "Host" + "\n" + "The " + away_team_dec + " (" + away_wins + 
                               "," + away_losses + "," + away_ot + ")" + "\n" + game_day_of_week + " the " + game_day_txt + " at " + game_time_est + " est!")
        context.bot.send_message(chat_id=update.effective_chat.id, text=next_game_check_msg)


def gamecheck(chat_id_set, number_of_teams, team_data):
    """
        The core function for returning the game description
        for the teams being followed by the user
        /game and the automatic notifications use this funtion
        for sending messages
    """
    while number_of_teams > 0:
        number_of_teams = number_of_teams - 1

        # the encoding is so that Montréal has its é, can't forget that
        away_team =    json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['away']['team']['name'], ensure_ascii=False).encode('utf8')
        away_team_fin = away_team[1:-1]
        away_team_dec = str(away_team_fin.decode("utf8"))
        away_wins =    json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['away']['leagueRecord']['wins'])
        away_losses =  json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['away']['leagueRecord']['losses'])
        home_team =    json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['home']['team']['name'], ensure_ascii=False).encode('utf8')
        home_team_fin = home_team[1:-1]
        home_team_dec = str(home_team_fin.decode("utf8"))
        home_wins =     json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['home']['leagueRecord']['wins'])
        home_losses =   json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['home']['leagueRecord']['losses'])
        game_fulltime = json.dumps(team_data['dates'][0]['games'][number_of_teams]['gameDate'])
        game_time = game_fulltime[12:-2]
        if dst_check == True:
            game_time_obj = datetime.strptime(game_time, '%H:%M:%S') - timedelta(hours=4)
        if dst_check ==False:
            game_time_obj = datetime.strptime(game_time, '%H:%M:%S') - timedelta(hours=5)
        game_time_est = datetime.strftime(game_time_obj, '%-I:%M%p')
        playoff_check = json.dumps(team_data['dates'][0]['games'][0]['gameType']).strip('\"')
        if playoff_check == 'P':

            away_wins_int = int(away_wins)
            home_wins_int = int(home_wins)
            away_games_won = away_wins_int % 4 
            home_games_won = home_wins_int % 4
            if away_games_won > home_games_won:
                leading_team = away_team_dec
                leading_games = str(away_games_won)
                trailing_games = str(home_games_won)
            if away_games_won < home_games_won:
                leading_team = home_team_dec
                leading_games = str(home_games_won)
                trailing_games = str(away_games_won)

            tie_check = away_games_won - home_games_won
            if tie_check != 0:
                if leading_games == 1:
                    game_check_msg = ("The " + home_team_dec + "\n" + "Host" + "\n" + "The " + away_team_dec + "\n" + "At " + game_time_est + " est!" + "\n" +  
                                      "The " + leading_team + " Lead " + leading_games + " game to " + trailing_games + "!")
                else:
                    game_check_msg = ("The " + home_team_dec + "\n" + "Host" + "\n" + "The " + away_team_dec + "\n" + "At " + game_time_est + " est!" + "\n" + 
                                      "The " + leading_team + " Lead " + leading_games + " games to " + trailing_games + "!")
                updater.bot.sendMessage(chat_id=chat_id_set, text=game_check_msg)

            if tie_check == 0:
                home_games_won_str = str(home_games_won)
                if home_games_won == 1:
                    game_check_msg = ("The " + home_team_dec + "\n" + "Host" + "\n" + "The " + away_team_dec + "\n" + "At " + game_time_est + " est!" + "\n" + 
                                      "The series is tied at " + home_games_won_str + " game!")
                else:
                    game_check_msg = ("The " + home_team_dec + "\n" + "Host" + "\n" + "The " + away_team_dec + "\n" + "At " + game_time_est + " est!" + "\n" + 
                                      "The series is tied at " + home_games_won_str + " games!")
                updater.bot.sendMessage(chat_id=chat_id_set, text=game_check_msg)
        if playoff_check == 'R':
            away_ot = json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['away']['leagueRecord']['ot'])
            home_ot = json.dumps(team_data['dates'][0]['games'][number_of_teams]['teams']['home']['leagueRecord']['ot'])
            game_check_msg = ("The " + home_team_dec + " (" + home_wins + "," + home_losses + "," + home_ot + ")" + "\n" + "Host" + "\n" + "The " + away_team_dec + " (" + away_wins + 
                              "," + away_losses + "," + away_ot + ")" + "\n" +  "at " + game_time_est + " est!")
            updater.bot.sendMessage(chat_id=chat_id_set, text=game_check_msg)
    return


def game(update, context):
    """
        Runs the gamecheck funtion for the teams being followed by the user
    """
    chat_id_set = update.effective_chat.id
    chatsdf = pd.read_csv(chatdb)
    chat_index = int(chatsdf.index[chatsdf['ChatID'] == chat_id_set].values)
    chat_team_ids = chatsdf.loc[[chat_index], ['TeamIDs']].values
    if str(chat_team_ids) == '[[nan]]':
        return
    formatted_chat_team_ids = str(chat_team_ids)[3:-3]
    api_url = f'https://statsapi.web.nhl.com/api/v1/schedule?teamId={formatted_chat_team_ids}&date={todays_date}'
    r = requests.get(api_url)
    team_data = r.json() 
    number_of_teams = int(json.dumps(team_data['totalGames']))
    autonotify = 0
    if not seasoncheck(chat_id_set, autonotify):
        return

    if number_of_teams > 0:
        gamecheck(chat_id_set, number_of_teams, team_data)
    if number_of_teams == 0:
        game_check_msg = 'There is not a game today'
        context.bot.send_message(chat_id=chat_id_set, text=game_check_msg)


def automation():
    """
        Handles the inital data for the daily notifications
        and restarts the timer for the next day at 8am
    """
    global todays_date
    todays_date = date.today()
    chatsdf = pd.read_csv(chatdb)
    chats_to_notify = list(chatsdf.loc[chatsdf['Notifications'] == 1, 'ChatID'])

    while len(chats_to_notify) != 0:
        userid = chats_to_notify[0]
        automaticgamenotification(userid)
        chats_to_notify.remove(userid)
    timer()


def automaticgamenotification(userid):
    """
        Handles sending the daily notifications
    """
    global chatsdf
    chatsdf = pd.read_csv(chatdb)
    chat_index = int(chatsdf.index[chatsdf['ChatID'] == userid].values)
    chat_team_ids = chatsdf.loc[[chat_index], ['TeamIDs']].values
    formatted_chat_team_ids = str(chat_team_ids)[3:-3]
    chat_id_set = userid
    api_url = f'https://statsapi.web.nhl.com/api/v1/schedule?teamId={formatted_chat_team_ids}&date={todays_date}'
    r = requests.get(api_url)
    team_data = r.json() 
    number_of_teams = int(json.dumps(team_data['totalGames']))

    autonotify = 1
    if not seasoncheck(chat_id_set, autonotify):
        return

    df = pd.DataFrame(columns=('HomeIDs', 'AwayIDs', 'Time'))
    index = 0

    if team_data['totalItems'] >= 1:
        for i in team_data['dates'][0]['games']:
            home_team = i['teams']['home']['team']['id']
            away_team = i['teams']['away']['team']['id']

            if dst_check == False:
                game_fulltime = i['gameDate'] 
                game_time = game_fulltime[12:-2]
                if dst_check == True:
                    game_time_obj = datetime.strptime(game_time, '%H:%M:%S') - timedelta(hours=4)
                if dst_check ==False:
                    game_time_obj = datetime.strptime(game_time, '%H:%M:%S') - timedelta(hours=5) 
                    game_time_obj - timedelta(minutes= game_time_obj.minute % 10)
                game_start = str(datetime.strftime(game_time_obj, '%H:%M'))

            df.loc[index] = [home_team, away_team, game_start]
            index = index+1
        df.to_csv(todays_db, index=False, header=True)

    if number_of_teams > 0:
        gamecheck(chat_id_set, number_of_teams, team_data)


def gametimecheck ():
    now = datetime.now() + timedelta (minutes=10)
    now -= timedelta(minutes = now.minute % 10)
    current_time = now.strftime('%H:%M')
    todays_df = pd.read_csv(todays_db)
    teamid_inx = list(todays_df.index[todays_df['Time'] == current_time])
    for i in teamid_inx:
        teamid_home = str(todays_df.loc[i, 'HomeIDs'])
        teamid_away = str(todays_df.loc[i, 'AwayIDs'])
        teamid_now = teamid_home + ',' +teamid_away
        gametimenotif(teamid_now)
    dailynotiftimer()

def gametimenotif(teamid_now):
    teamids = list(teamid_now.split(','))
    chatdf = pd.read_csv(chatdb)
    notif_ids = []
    for i in teamids:
        notif_chats = chatdf[(chatdf['Notifications'] == 1) & (chatdf['TeamIDs'].str.contains(i))]
        for i in notif_chats.index:
            if notif_chats.loc[i, 'ChatID'] not in notif_ids: 
                notif_ids.append(notif_chats.loc[i, 'ChatID'])
    api_url = f'https://statsapi.web.nhl.com/api/v1/schedule?teamId={teamid_now}&date={todays_date}'
    r = requests.get(api_url)
    game_notif = r.json() 
    # the encoding is so that Montréal has its é, can't forget that
    away_team =     json.dumps(game_notif['dates'][0]['games'][0]['teams']['away']['team']['name'], ensure_ascii=False).encode('utf8')
    away_team_fin = away_team[1:-1]
    away_team_dec = str(away_team_fin.decode("utf8"))
    home_team =     json.dumps(game_notif['dates'][0]['games'][0]['teams']['home']['team']['name'], ensure_ascii=False).encode('utf8')
    home_team_fin = home_team[1:-1]
    home_team_dec = str(home_team_fin.decode("utf8"))
    game_fulltime = json.dumps(game_notif['dates'][0]['games'][0]['gameDate'])
    game_time = game_fulltime[12:-2]
    if dst_check == True:
        game_time_obj = datetime.strptime(game_time, '%H:%M:%S') - timedelta(hours=4)
    if dst_check ==False:
        game_time_obj = datetime.strptime(game_time, '%H:%M:%S') - timedelta(hours=5)
    game_time_est = datetime.strftime(game_time_obj, '%-I:%M%p')

    game_time_msg = ('Game Time!' + '\n' + '\n' +'The ' + home_team_dec + '\n' + 'Host' + '\n' + 'The ' + away_team_dec + '\n' + '@ ' + game_time_est + ' est!')

    for i in notif_ids:
        id = int(i)
        updater.bot.sendMessage(chat_id=id, text=game_time_msg) 


def last(update, context):
    """
    Returns the score of the last game for the team submitted by the user
    If the game is a playoff game the seiers standings will be returned as well
    """
    last_game_request = update.message.text
    if last_game_request.count(' ') == 0:
        context.bot.send_message(chat_id=update.effective_chat.id, text=("Please indicate the team you want the last game for." + '\n' + "e.g. /lastgame Pens"))
        return
    team_name = last_game_request[10:].lower()
    lastdf = pd.read_csv(teamsdb, index_col=None) 

    if not teamdatabasecheck(update, context, team_name):
        return

    teamid_last = int(lastdf.loc[lastdf.TeamName == team_name, 'TeamID'].values)

    api_url = f'https://statsapi.web.nhl.com/api/v1/teams/{teamid_last}?expand=team.schedule.previous'
    r = requests.get(api_url)
    last_game = r.json()

    game_pk = json.dumps(last_game['teams'][0]['previousGameSchedule']['dates'][0]['games'][0]['gamePk'])
    api2_url = f'https://statsapi.web.nhl.com/api/v1/game/{game_pk}/feed/live'
    r2 = requests.get(api2_url)
    last_game_stats = r2.json()

    # the encoding is so that Montréal has its é, can't forget that
    home_team =           json.dumps(last_game_stats['liveData']['linescore']['teams']['home']['team']['name'], ensure_ascii=False).encode('utf8')
    home_team_fin = home_team[1:-1]
    home_team_dec = str(home_team_fin.decode("utf8"))
    away_team =           json.dumps(last_game_stats['liveData']['linescore']['teams']['away']['team']['name'], ensure_ascii=False).encode('utf8')
    away_team_fin = away_team[1:-1]
    away_team_dec = str(away_team_fin.decode("utf8"))
    away_team_score =     json.dumps(last_game_stats['liveData']['linescore']['teams']['away']['goals'])
    home_team_score =     json.dumps(last_game_stats['liveData']['linescore']['teams']['home']['goals'])
    overtime_check =  int(json.dumps(last_game_stats['liveData']['linescore']['currentPeriod']))
    playoff_check =       json.dumps(last_game['teams'][0]['previousGameSchedule']['dates'][0]['games'][0]['gameType']).strip('\"')

    if playoff_check == 'P':
        if overtime_check == 3:
            overtime_msg = ''
        if overtime_check > 3:
            overtime_check -= 3
            overtime_check_str = str(overtime_check)
            overtime_msg = 'In Overtime ' + overtime_check_str + '!'
    elif overtime_check == 3:
        overtime_msg = ''
    elif overtime_check == 4:
        overtime_msg = 'In Overtime!'
    elif overtime_check == 5:
        overtime_msg = 'In a Shootout!'
    if away_team_score > home_team_score:
        last_game_msg = ("The " + away_team_dec + ":    " + away_team_score + "\n" + " The " + home_team_dec + ":    " + home_team_score + "\n" + overtime_msg)
    if home_team_score > away_team_score:
        last_game_msg = ("The " + home_team_dec + ":    " + home_team_score + "\n" + " The " + away_team_dec + ":    " + away_team_score + "\n" + overtime_msg)

    updater.bot.sendMessage(chat_id=update.effective_chat.id, text=last_game_msg)


def notifications(update, context: CallbackContext):
    """
        Allows the user to select whether or not they want daily notifications
    """
    # this needs to be global because the handler for the buttons cant be passed variables
    global chat_id_noti
    chat_id_noti = update.effective_chat.id
    chatsdf = pd.read_csv(chatdb)
    notiexists = chatsdf.index[chatsdf['ChatID'] == chat_id_noti].values
    if notiexists.size > 0:            
        reply_buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Yes", callback_data='yes'),
                InlineKeyboardButton("No", callback_data='no')
            ],    
        ])
        updater.bot.sendMessage(chat_id=chat_id_noti, text=(
                                                            'Would you like daily game notifications?' + "\n" + "Notifications are sent at 8am est."), reply_markup=reply_buttons
                                )
        return False
    updater.bot.sendMessage(chat_id=update.effective_chat.id, text="Please run /setup first!")


def status(update, context):
    """
        Tells the user what teams the are following and if they are getting daily notifications
    """
    users_teams = ''
    teams_list = ''
    chat_id_status = update.effective_chat.id
    chatsdf = pd.read_csv(chatdb)
    team_names_df = pd.read_csv(teamsdb, encoding="ISO-8859-1")
    users_team_ids = list(chatsdf.loc[chatsdf['ChatID'] == chat_id_status, 'TeamIDs'].values)
    if users_team_ids == []:
        updater.bot.sendMessage(chat_id=update.effective_chat.id, text="You have no data, please run /setup first!")
        return
    users_team_ids_form = str(users_team_ids)[2:-2]
    users_team_ids_list = [int(x) for x in users_team_ids_form.split(',')]
    formatted_teams_df = team_names_df.loc[team_names_df['Formatted'] == 1]
    while len(users_team_ids_list) > 0:
        team = users_team_ids_list[0]
        users_teams = formatted_teams_df.loc[formatted_teams_df['TeamID'] == team, 'TeamName'].values
        teams_list = teams_list + users_teams + '?The '
        users_team_ids_list.remove(team)
    isusernotifi = chatsdf.loc[chatsdf['ChatID'] == chat_id_status, 'Notifications'].values
    if isusernotifi == 0:
        notif_status = 'are not'
    if isusernotifi == 1:
        notif_status = 'are'
    finalteamslist = str(teams_list)[2:-7]
    status_message = ('You are following:' + '\n' + 'The ' + finalteamslist.replace('?', '\n') + '\n' + '\n' + 'You ' + notif_status + 
                      ' receiving daily notifications.')
    updater.bot.sendMessage(chat_id=update.effective_chat.id, text=status_message)


def cupcheck(update, context):
    """
        Returns the days since the Flyers and the Penguins have won the cup
        Lets Go Pens!
    """
    f_Date = date(1975, 5, 27)
    f_sincecup = f_Date - todays_date
    f_dayssincecup = str(f_sincecup.days)[1:]

    p_Date = date(2017, 6, 11)
    p_sincecup = p_Date - todays_date
    p_dayssincecup = str(p_sincecup.days)[1:]

    cup_msg = ('It has been ' + f_dayssincecup + ' days since the Flyers have won the Stanley Cup,' + '\n' + "but only " + p_dayssincecup + ' days since the Penguins have won the Stanley Cup.' + '\n' + 'Lets Go Pens!')
    updater.bot.sendMessage(chat_id=update.effective_chat.id, text=cup_msg)


def roster(update, context):
    """
        returns the roster for a given team
    """
    # setsp formatting for table
    table = pt.PrettyTable(['Number', 'Full Name', 'Position'])
    table.align['Position'] = 'l'

    # gets the team name the user submitted
    roster_request = update.message.text
    team_name = roster_request[8:].lower()
    if roster_request.count(' ') == 0:
        context.bot.send_message(chat_id=update.effective_chat.id, text=("Please indicate the team you want the roster of." + '\n' + "e.g. /roster Pens"))
        return

    # check if the user submitted a supported team name
    if not teamdatabasecheck(update, context, team_name):
        return

    # searches the api for the team name
    teamdf = pd.read_csv(teamsdb, index_col=None) 
    teamID = int(teamdf.loc[teamdf.TeamName == team_name, 'TeamID'])
    api_url = f'https://statsapi.web.nhl.com/api/v1/teams/{teamID}?expand=team.roster'
    r = requests.get(api_url)
    team_data = r.json() 
    roster = team_data['teams'][0]['roster']['roster']
    team = json.dumps(team_data['teams'][0]['name'], ensure_ascii=False).encode('utf8')
    team_fin = team[1:-1]
    team_dec = str(team_fin.decode("utf8"))
    for player in roster:
        name =     player['person']['fullName']
        number =   int(player['jerseyNumber'])
        position = player['position']['name']
        table.add_row([number, name, position])
    table.title = 'Team Roster For The ' + team_dec
    sorted_table = table.get_string(sortby='Number')
    updater.bot.sendMessage(chat_id=update.effective_chat.id, text=f'<pre>{sorted_table}</pre>', parse_mode=ParseMode.HTML)

        
def player(update, context):
    """
        Returns the 
        jersey number, full name, and position 
        of a given player for a given team
    """
    # formats the users message to search the api for the player
    player_request = update.message.text
    if player_request.count(' ') == 0:
        context.bot.send_message(chat_id=update.effective_chat.id, text=("Please indicate a team and player." + '\n' + "e.g. /player Pens Crosby"))
        return
    if player_request.count(' ') > 3:
        context.bot.send_message(chat_id=update.effective_chat.id, text="One player at a time please.")
        return
    if player_request.count(' ') == 3:
        team_name, fname, lname = player_request[8:].lower().split(' ')
        player_info = fname + ' ' + lname
    if player_request.count(' ') < 3:    
        team_name, player_info = player_request[8:].lower().split(' ')
    if player_info.isnumeric():
        player_info = int(player_info)

    # check if the user submitted a supported team name
    if not teamdatabasecheck(update, context, team_name):
        return

    # Seaches the api for requested player
    teamdf = pd.read_cs(teamsdb, index_col=None) 
    teamID = int(teamdf.loc[teamdf.TeamName == team_name, 'TeamID'])
    api_url = f'https://statsapi.web.nhl.com/api/v1/teams/{teamID}?expand=team.roster'
    r = requests.get(api_url)
    team_data = r.json() 
    roster = team_data['teams'][0]['roster']['roster']
    team = json.dumps(team_data['teams'][0]['name'], ensure_ascii=False).encode('utf8')
    team_fin = team[1:-1]
    team_dec = str(team_fin.decode("utf8"))
    found = 0
    for player in roster:
        number = int(player['jerseyNumber'])
        name =       player['person']['fullName']
        first, last = name.split(' ')
        if number == player_info or first.lower() == player_info or last.lower() == player_info or name.lower() == player_info:
            number = player['jerseyNumber']
            position = player['position']['name']
            player_msg = (number + '\n' + name + '\n' + position)
            found = 1
    if found == 0:
        player_info = str(player_info)
        if player_info.isnumeric():
            player_msg = 'I cant find number ' + player_info + ' on The ' + team_dec
        else:
            player_name_cap = player_info.title()
            player_msg = 'I cant find anyone named ' + player_name_cap + ' on The ' + team_dec

    context.bot.send_message(chat_id=update.effective_chat.id, text=player_msg)


def stats(update, context):
    """
        Returns the regular season stats for
        a team or a player submitted by the user
    """
    stats_request = update.message.text
    if stats_request.count(' ') == 0:
        context.bot.send_message(chat_id=update.effective_chat.id, text=("Please indicate a team and/or player." + '\n' + "e.g. /stats Pens " + " "*3 + "or" + " " * 3 + "/stats Pens Crosby"))
        return
    if stats_request.count(' ') > 3:
        context.bot.send_message(chat_id=update.effective_chat.id, text="One player or team at a time please.")
        return
    if stats_request.count(' ') == 3:
        team_name, fname, lname = stats_request[7:].lower().split(' ')
        player_info = fname + ' ' + lname
        teamstats = 0
    if stats_request.count(' ') == 2:    
        team_name, player_info = stats_request[7:].lower().split(' ')
        teamstats = 0
    if stats_request.count(' ') == 1:    
        team_name = stats_request[7:].lower()
        teamstats = 1
    if not teamdatabasecheck(update, context, team_name):
        return

    # If the user asks for the stats from a player
    if teamstats == 0:
        table = pt.PrettyTable(
            ['Games Played', 'Goals', 'Assists', 'Points', 'Penalty Minutes', '+/-']
            )
        teamdf = pd.read_csv(teamsdb, index_col=None) 
        teamID = int(teamdf.loc[teamdf.TeamName == team_name, 'TeamID'])
        if player_info.isnumeric():
            player_info = int(player_info)
        api_url = f'https://statsapi.web.nhl.com/api/v1/teams/{teamID}?expand=team.roster'
        r = requests.get(api_url)
        player_data = r.json() 
        team = json.dumps(player_data['teams'][0]['name'], ensure_ascii=False).encode('utf8')
        team_fin = team[1:-1]
        team_dec = str(team_fin.decode("utf8"))
        found = 0
        for n in player_data['teams'][0]['roster']['roster']:
            number = int(n['jerseyNumber'])
            name = n['person']['fullName']
            first, last = name.split(' ')
            if number == player_info or first.lower() == player_info or last.lower() == player_info or name.lower() == player_info:
                player_id = n['person']['id']
                player_name = n['person']['fullName']
                found = 1

        if found == 0:
            player_info = str(player_info)
            if player_info.isnumeric():
                player_msg = 'I cant find number ' + player_info + ' on The ' + team_dec
            else:
                player_name_cap = player_info.title()
                player_msg = 'I cant find anyone named ' + player_name_cap + ' on The ' + team_dec
            updater.bot.sendMessage(chat_id=update.effective_chat.id, text=player_msg)
            return

        stats_url = f'https://statsapi.web.nhl.com/api/v1/people/{player_id}/stats?stats=statsSingleSeason'
        r_stats = requests.get(stats_url)
        player_stats = r_stats.json() 

        games =     player_stats['stats'][0]['splits'][0]['stat']['games']
        goals =     player_stats['stats'][0]['splits'][0]['stat']['goals']
        assists =   player_stats['stats'][0]['splits'][0]['stat']['assists']
        points =    player_stats['stats'][0]['splits'][0]['stat']['games']
        pim =       player_stats['stats'][0]['splits'][0]['stat']['pim']
        plusminus = player_stats['stats'][0]['splits'][0]['stat']['plusMinus']
        if int(plusminus) > 0:
            plusminus = '+' + str(plusminus)
        table.add_row(
            [games, goals, assists, points, pim, plusminus]
            )
        table.title = player_name + "'s Regular Season Stats"
        updater.bot.sendMessage(chat_id=update.effective_chat.id, text=f'<pre>{table}</pre>', parse_mode=ParseMode.HTML)

    # If the user asks for the stats from a team
    if teamstats == 1:
        table = pt.PrettyTable(
            ['Games Played', 'Wins', 'Losses', 'OT Losses', 'Points', 'Division', 'Standings']
            )
        teamdf = pd.read_csv(teamsdb, index_col=None) 
        teamID = int(teamdf.loc[teamdf.TeamName == team_name, 'TeamID'])
        api_url = f'https://statsapi.web.nhl.com/api/v1/teams/{teamID}/stats'
        r = requests.get(api_url)
        team_data = r.json() 
        team = json.dumps(team_data['stats'][0]['splits'][0]['team']['name'], ensure_ascii=False).encode('utf8')
        team_fin = team[1:-1]
        team_dec = str(team_fin.decode("utf8"))

        games_played =           json.dumps(team_data['stats'][0]['splits'][0]['stat']['gamesPlayed'])
        wins =                   json.dumps(team_data['stats'][0]['splits'][0]['stat']['wins'])
        losses =                 json.dumps(team_data['stats'][0]['splits'][0]['stat']['losses'])
        ot_losses =              json.dumps(team_data['stats'][0]['splits'][0]['stat']['ot'])
        points =                 json.dumps(team_data['stats'][0]['splits'][0]['stat']['pts'])

        api_url_standings = 'https://statsapi.web.nhl.com/api/v1/standings'
        r_standings = requests.get(api_url_standings)
        team_standings = r_standings.json() 
        division = ''
        for n in team_standings['records']:
            for x in n['teamRecords']:
                team_id = x['team']['id']
                if int(team_id) == teamID:
                    division = n['division']['name']
                    standing = x['divisionRank']
        table.add_row(
            [games_played, wins, losses, ot_losses, points, division, standing]
            )
        table.title = 'The ' + team_dec + "'s Regular Season Stats"
        updater.bot.sendMessage(chat_id=update.effective_chat.id, text=f'<pre>{table}</pre>', parse_mode=ParseMode.HTML)


def standings(update, context):
    """
        Returns the regular season standings
        for a given division or for all divisions
    """
    division_msg = update.message.text

    # If the user specifies a division only that division is returned
    if division_msg.count(' ') == 1:
        division_request = division_msg[11:].lower()
        api_url_standings = 'https://statsapi.web.nhl.com/api/v1/standings'
        r_standings = requests.get(api_url_standings)
        standings = r_standings.json() 
        found = 0
        for n in standings['records']:
            division = n['division']['name'].lower()
            if division == division_request:
                table = pt.PrettyTable(
                                        ['Standings', 'Teams', 'Points', 'Wins', 'Losses', 'OT Losses']
                                      )
                table.title = division.title() + ' Division Standings'
                for x in n['teamRecords']:
                    standings = x['divisionRank']
                    team_name = x['team']['name']
                    points = x['points']
                    wins = x['leagueRecord']['wins']
                    losses = x['leagueRecord']['losses']
                    ot_losses = x['leagueRecord']['ot']
                    table.add_row(
                                    [standings, team_name, points, wins, losses, ot_losses]
                                 )
                found = 1
        if found == 1:
            updater.bot.sendMessage(chat_id=update.effective_chat.id, text=f'<pre>{table}</pre>', parse_mode=ParseMode.HTML)
        if found == 0:

            standings_msg = "That is not a division I know." + "\n" + "The divisions are Central, Metropolitan, Pacific, and Atlantic"
            updater.bot.sendMessage(chat_id=update.effective_chat.id, text=standings_msg)
            return

    if division_msg.count(' ') > 1:
        standings_msg = "One division at a time please."
        updater.bot.sendMessage(chat_id=update.effective_chat.id, text=standings_msg)
        return

    # If the user does not specify a division all division standings are returned as individual messages
    if division_msg.count(' ') == 0:
        api_url_standings = 'https://statsapi.web.nhl.com/api/v1/standings'
        r_standings = requests.get(api_url_standings)
        standings = r_standings.json() 
        for n in standings['records']:
            table = pt.PrettyTable(
                                    ['Standings', 'Teams', 'Points', 'Wins', 'Losses', 'OT Losses']
                                  )
            division = n['division']['name']
            table.title = division + ' Division Standings'
            for x in n['teamRecords']:
                standings = x['divisionRank']
                team_name = x['team']['name']
                points = x['points']
                wins = x['leagueRecord']['wins']
                losses = x['leagueRecord']['losses']
                ot_losses = x['leagueRecord']['ot']
                table.add_row(
                                [standings, team_name, points, wins, losses, ot_losses]
                             )
            updater.bot.sendMessage(chat_id=update.effective_chat.id, text=f'<pre>{table}</pre>', parse_mode=ParseMode.HTML)


def today(update, context):
    """
    DEBUGING FUCTION  
        sends what the bot thinks today is
    """
    today_msg = str(todays_date)
    updater.bot.sendMessage(chat_id=update.effective_chat.id, text=today_msg)


def testautonotify(update, context):
    """
    DEBUGING FUCTION  
        runs the daily notifications on command
    """
    if update.effective_chat.id == 110799848:
        updater.bot.sendMessage(chat_id=update.effective_chat.id, text='Testing Automatic Notifications')
        automation()
        gametimecheck()



def bye(update, context):
    """
        Removed the users data from the bots database
    """
    global chat_id_noti
    chat_id_noti = update.effective_chat.id
    chatsdf = pd.read_csv(chatdb)
    notiexists = chatsdf.index[chatsdf['ChatID'] == chat_id_noti].values
    if notiexists.size > 0:            
        reply_buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Yes", callback_data='bye'),
                InlineKeyboardButton("No", callback_data='stay')
            ],    
        ])
        updater.bot.sendMessage(chat_id=chat_id_noti, 
                                text='Are you sure you would like to delete your team and notifications data?', reply_markup=reply_buttons)
        return False
    updater.bot.sendMessage(chat_id=update.effective_chat.id, text="You have no data! Run /Setup to start!")


def timer():
    """
        Send notification at 8am every day
    """
    x = datetime.today()
    y = x.replace(day=x.day, hour=8, minute=0, second=0, microsecond=0) + timedelta(days=1)
    delta_t = y-x

    secs = delta_t.total_seconds()

    t = Timer(secs, automation)
    t.start()


def dailynotiftimer():
    """
        Checks if there is a game in the next ten minutes every ten minutes
    """
    x = datetime.today()
    secs = 600
    current_hour = int(x.strftime('%H'))
    if current_hour >= 9 and current_hour <= 24:
        t = Timer(secs, gametimecheck)
        t.start()
    else:
        t = Timer(secs,dailynotiftimer)
        t.start()


def stop(update, context):
    """
        stop the bot through a telegram command
    """
    if update.effective_chat.id == 110799848:
        updater.bot.sendMessage(chat_id=update.effective_chat.id, text='Shuting Down')
        updater.stop()
        updater.is_idle = False


# starts automation for game notifications
timer()
dailynotiftimer()

# dispatcher for the bot to look for each command
dispatcher = updater.dispatcher
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
dispatcher.add_handler(CommandHandler('roster', roster))
dispatcher.add_handler(CommandHandler('player', player))
dispatcher.add_handler(CommandHandler('stats', stats))
dispatcher.add_handler(CommandHandler('standings', standings))
dispatcher.add_handler(CommandHandler('removeme', bye))
dispatcher.add_handler(CommandHandler('testautonotify', testautonotify))
dispatcher.add_handler(CommandHandler('stop', stop))


# startrs the bot
updater.start_polling()

# stops the bot with Ctrl-C
updater.idle()
