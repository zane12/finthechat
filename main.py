import os

import pymongo
import discord
from dotenv import load_dotenv


load_dotenv()
DBSERVER = os.getenv('DB_SERVER_URL')
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

myclient = pymongo.MongoClient(DBSERVER)

mydb = myclient["finthechat"]
mycol = mydb["users"]

client = discord.Client()


@client.event
async def on_ready():
    guild = discord.utils.get(client.guilds, name=GUILD)

    print(f'{client.user} has connected to the following server:\n'
          f'{guild.name}(id: {guild.id})')


@client.event
async def on_message(message):

    if message.author.bot:
        return

    if message.content == 'f' or message.content == 'F':

        user = mycol.find_one({"user": message.author.display_name})

        if user == None:
            mycol.insert_one({"user": message.author.display_name, "score": 1})
        else:
            mycol.update_one({"user": message.author.display_name}, {
                             "$set": {"score": user["score"] + 1}})

        await message.channel.send("F")

    if message.content == '!leaderboard':
        leaderboard = mycol.find().sort("score", -1)
        leaderString = ''
        i = 0
        for x in leaderboard:
            i += 1
            if i == 10:
                break
            if i == 1:
                leaderString += "The reigning champ "
            timeString = "time"
            if x["score"] > 1:
                timeString = "times"
            leaderString += x["user"] + " has paid respects " + \
                str(x["score"]) + " " + timeString + "\n"

        await message.channel.send(leaderString)


client.run(TOKEN)
