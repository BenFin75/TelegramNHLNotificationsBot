# TelegramNHLNotifcationBot

A telegram bot to get notifications for NHL games.  
To use the bot add @NHLGameNotificationsBot on telegram. The bot can be added to groups or used individually.  

This is my first python project, constructive feedback for improvement is welcome!  
I hope you like it!

# Important for redeploying
In order to keep the bot tokens private they are stored in a seperate csv.  
If you want to use this code for your own bot you will need to create a csv or remove:

```
bot_token_df = pd.read_csv((os.path.join(os.path.dirname(os.getcwd()),"TelegramBotTokens.csv")))
bot_index = int(bot_token_df.index[bot_token_df['Bot Name'] == 'Hockey Bot'].values)
bot_token = str(bot_token_df.loc[[bot_index], ['Bot Token']].values).strip("'[]")

bot = Bot(bot_token)
updater=Updater(bot_token, use_context=True)
```

and replace it with:

```
bot = Bot(bot_token)
updater=Updater(bot_token, use_context=True)
```
 where bot_token is your bots token

 I also have the stop command set to only be able to be run in my chat,  
 so if you want to be able to shut down your bot in telegram you will have to change 110799848 to your chatid here:

```
def stoplink(update, context):
    if update.message.chat.id == 110799848:
```
