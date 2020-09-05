import os

import pymongo
import discord
from discord.ext import commands
from dotenv import load_dotenv


load_dotenv()
DBSERVER = os.getenv('DB_SERVER_URL')
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

myclient = pymongo.MongoClient(DBSERVER)


bot = commands.Bot(command_prefix='!')


@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds, name=GUILD)

    print(f'{bot.user} has connected to the following server:\n'
          f'{guild.name}(id: {guild.id})')


@bot.event
async def on_message(message):
    guild = message.guild
    mydb = myclient["finthechat-{}".format(guild.id)]

    userCol = mydb["users"]

    if message.author.bot:
        return

    if message.content == 'f' or message.content == 'F':

        user = userCol.find_one({"user": message.author.id})

        if user == None:
            userCol.insert_one({"user": message.author.id, "score": 1})
        else:
            userCol.update_one({"user": message.author.id}, {
                "$set": {"score": user["score"] + 1}})

        await message.channel.send("F")
    await bot.process_commands(message)


@bot.command()
async def leaderboard(ctx):
    guild = ctx.guild.id
    mydb = myclient["finthechat-{}".format(guild)]

    userCol = mydb["users"]

    leaderboard = userCol.find().sort("score", -1)

    leaderString = ''

    i = 0

    for x in leaderboard:
        i += 1
        if i == 10:
            break

        if i == 1:
            leaderString += "The reigning champ "
        timeString = "time"

        user = bot.get_user(x["user"])

        if user == None:
            continue

        if x["score"] > 1:
            timeString = "times"

        leaderString += user.display_name + " has paid respects " + \
            str(x["score"]) + " " + timeString + "\n"

    await ctx.send(leaderString)


@bot.command()
async def bet(ctx, user: discord.Member, amt: int):
    guild = ctx.guild.id
    mydb = myclient["finthechat-{}".format(guild)]

    betCol = mydb["bets"]

    check = betCol.find()

    found = False
    for x in check:
        if ctx.author.id and user.id in x["users"]:
            found = True

    if found:
        await ctx.send("You may only have one active bet with {} at a time".format(user.display_name))
        return

    betCol.insert_one(
        {"users": [ctx.author.id, user.id], "amt": amt, "winner": None, "loser": None})

    await ctx.send('{} bet {} {} F\'s'.format(ctx.author.display_name, user.display_name, amt))


@bot.command()
async def winBet(ctx, user: discord.Member):
    guild = ctx.guild.id
    mydb = myclient["finthechat-{}".format(guild)]

    userCol = mydb["users"]
    betCol = mydb["bets"]

    check = betCol.find()

    found = False
    for x in check:
        if ctx.author.id and user.id in x["users"]:
            found = True
            bet = x

    if(found):
        betCol.find_one_and_update(bet, {"$set": {"winner": ctx.author.id}})
    else:
        await ctx.send("You don't have an active bet with {}".format(user.display_name))
        return

    if bet["loser"] == user.id:
        amt = bet["amt"]
        userCol.find_one_and_update({"user": ctx.author.id}, {
            "$inc": {"score": amt}})
        userCol.find_one_and_update({"user": user.id}, {
            "$inc": {"score": (0 - amt)}})
        winner = userCol.find_one({"user": ctx.author.id})
        loser = userCol.find_one({"user": user.id})
        betCol.find_one_and_delete({"_id": bet["_id"]})
        await ctx.send("{} now has {} F's \n {} now has {} F's".format(ctx.author.display_name, winner["score"], user.display_name, loser["score"]))

    else:
        await ctx.send("Waiting for {} to confirm the bet".format(user.display_name))


@ bot.command()
async def loseBet(ctx, user: discord.Member):
    guild = ctx.guild.id
    mydb = myclient["finthechat-{}".format(guild)]

    userCol = mydb["users"]
    betCol = mydb["bets"]

    check = betCol.find()

    found = False
    for x in check:
        if ctx.author.id and user.id in x["users"]:
            found = True
            bet = x

    if(found):
        betCol.find_one_and_update(bet, {"$set": {"loser": ctx.author.id}})
    else:
        await ctx.send("You don't have an active bet with {}".format(user.display_name))
        return

    if bet["winner"] == user.id:
        amt = bet["amt"]
        userCol.find_one_and_update({"user": ctx.author.id}, {
            "$inc": {"score": (0 - amt)}})
        userCol.find_one_and_update({"user": user.id}, {
            "$inc": {"score": (amt)}})
        winner = userCol.find_one({"user": user.id})
        loser = userCol.find_one({"user": ctx.author.id})
        betCol.find_one_and_delete({"_id": bet["_id"]})

        await ctx.send("{} now has {} F's \n {} now has {} F's".format(ctx.author.display_name, loser["score"], user.display_name, winner["score"]))

bot.run(TOKEN)
