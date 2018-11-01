import discord
import asyncio
from discord.ext import commands
from tinydb import TinyDB, Query

import logging

##logging##
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

##tinydb init##
settings_db = TinyDB('settings.json')
users_db = TinyDB('players.json')
query = Query()

##bot##
client = commands.Bot(command_prefix='g!')

@client.event
async def on_ready():
    logger.info("Succesfully connected.")


@client.command(pass_context = True)
@commands.is_owner()
async def ping(ctx):

    await ctx.send("pong")

@client.command(pass_context = True)
@commands.is_owner()
async def reset_settings(ctx):
    
    settings_db.purge()
    await ctx.send("Settings deleted!")
    logger.info(f"{ctx.guild.name}, {ctx.channel.name}, {ctx.message.author.name} - Settings Deleted.")
    
@client.command(pass_context = True)
@commands.is_owner()
async def new_self_role(ctx):

    settings_db.remove(query.type == "message")
    settings_db.remove(query.type == "emoji")

    msg = await ctx.send("NSFW'ye katılmak için emojiye tıklayın.")
    
    logger.info(f"{ctx.guild.name}, {ctx.channel.name}, {ctx.message.author.name} - Self role initiated.")

    reaction,user = await client.wait_for('reaction_add')

    if user == ctx.message.author:

        settings_db.insert({"type":"message", "id":msg.id})
        settings_db.insert({"type":"emoji" , "id":reaction.emoji.id})

        logger.info(f"{ctx.guild.name}, {ctx.channel.name}, {ctx.message.author.name} - Self role finished.")

@client.command(pass_context = True)
@commands.is_owner()
async def set_nsfw_roles(ctx, temp_role:discord.Role, nsfw_role:discord.Role):

    settings_db.remove(query.type == "temp_role")
    settings_db.remove(query.type == "nsfw_role")

    settings_db.insert({"type":"temp_role", "id":temp_role.id })
    settings_db.insert({"type":"nsfw_role", "id":nsfw_role.id })

    await ctx.send("NSFW rolleri kaydedildi!")
    logger.info(f"{ctx.guild.name}, {ctx.channel.name}, {ctx.message.author.name} - NSFW roles added.")

@client.command(pass_context = True)
@commands.is_owner()
async def set_guards(ctx, guard_role:discord.Role):

    settings_db.remove(query.type == "guard_role")
    settings_db.insert({"type":"guard_role", "id":guard_role.id })

    await ctx.send("Guardian rolü kaydedildi!")
    logger.info(f"{ctx.guild.name}, {ctx.channel.name}, {ctx.message.author.name} - Guardian role added.")

@client.command(pass_context = True)
@commands.is_owner()
async def set_channels(ctx, temp_channel:discord.TextChannel, nsfw_channel:discord.TextChannel):

    settings_db.remove(query.type == "temp_channel")
    settings_db.remove(query.type == "nsfw_channel")

    settings_db.insert({"type":"temp_channel", "id":temp_channel.id })
    settings_db.insert({"type":"nsfw_channel", "id":nsfw_channel.id })

    await ctx.send("NSFW kanalları kaydedildi!")
    logger.info(f"{ctx.guild.name}, {ctx.channel.name}, {ctx.message.author.name} - NSFW channels added.")

@client.event
async def on_raw_reaction_add(payload):
    
    if settings_db.contains(query.type == "emoji"):
        
        guild = client.get_guild(payload.guild_id)

        message_id= settings_db.get(query.type == "message")["id"]
        emoji_id = settings_db.get(query.type == "emoji")["id"]

        emoji = client.get_emoji(emoji_id) 

        if payload.message_id == message_id and payload.emoji.id == emoji_id:

            member = guild.get_member(payload.user_id)
            logger.info(f"{member.name} - clicked the emoji!")

            if users_db.contains(query.id == member.id):
                
                role_id = settings_db.get(query.type == "nsfw_role")["id"]
                role = guild.get_role(role_id)
                
                await member.add_roles(role)
                logger.info(f"{member.name} - was already in database, NSFW role has given.")

            else:
                role_id = settings_db.get(query.type == "temp_role")["id"]
                role = guild.get_role(role_id)
                
                await member.add_roles(role)
                logger.info(f"{member.name} - New user, temporary role has given.")

                channel_id = settings_db.get(query.type == "temp_channel")["id"]
                channel = guild.get_channel(channel_id)
                msg = await channel.send(f"{member.mention} NSFW kanalına hoş geldin! Bu serverda aramızda gizli saklı yoktur. Bu nedenden dolayı diğerlerine katılmadan önce yapman gereken küçük bir şey var. Face Reveal(yüzünün resmini) bu kanala atmalısın. Merak etme, şu anda nsfw rolü olan herkes bunu çoktan yaptı. İçeriye girdiğinde diğerlerinin fotoğraflarına ulaşabilirsin. Kontrol edildikten sonra NSFW rolünü alacaksın. Unutma! burada izleniyorsun. Yanlış davranışlarda cezalandırılabilirsin! Eğer bunlar hoşuna gitmediyse bu mesajın altındaki emojiye tıklayarak buradan çıkabilirsin. Seni aramızda görmekten mutluluk duyacağız!")
                
                await msg.add_reaction(emoji)
                
                reaction,user = await client.wait_for('reaction_add')
                
                if reaction.emoji.id == emoji_id and user == member:
                    
                    temp_roles=[]
                    for role_element in member.roles:
                        if role_element != role:
                            temp_roles.append(role_element)

                    await member.edit(roles = temp_roles)
                    logger.info(f"{member.name} - user decided to leave NSFW.")

@client.event
async def on_raw_reaction_remove(payload):

    emoji_id = settings_db.get(query.type == "emoji")["id"]
    
    if payload.emoji.id == emoji_id and settings_db.contains(query.type == "emoji"):
        
        guild = client.get_guild(payload.guild_id)

        temp_role_id = settings_db.get(query.type == "temp_role")["id"]
        nsfw_role_id = settings_db.get(query.type == "nsfw_role")["id"]

        temp_role = guild.get_role(temp_role_id)
        nsfw_role = guild.get_role(nsfw_role_id)
                
        member = guild.get_member(payload.user_id)

        await member.remove_roles(nsfw_role, temp_role)
        logger.info(f"{member.name} - User left NSFW.")

@client.command(pass_context = True)
async def allow(ctx, user:discord.Member):
    
    guild = ctx.guild

    guard_role_id = settings_db.get(query.type == "guard_role")["id"]
    guard_role = guild.get_role(guard_role_id)

    temp_role_id = settings_db.get(query.type == "temp_role")["id"]
    temp_role = guild.get_role(temp_role_id)

    if( guard_role in ctx.message.author.roles or ctx.message.author.id == 142828565359099905)and temp_role in user.roles and not users_db.contains(query.id == user.id):

        nsfw_role_id = settings_db.get(query.type == "nsfw_role")["id"]    
        nsfw_role = guild.get_role(nsfw_role_id)
        
        temp_roles=[]
        for role in user.roles:
            if role == temp_role:
                temp_roles.append(nsfw_role)
            else:
                temp_roles.append(role)

        await user.edit(roles = temp_roles)

        users_db.insert({"username":user.name, "id":user.id})

        channel_id = settings_db.get(query.type == "nsfw_channel")["id"]
        channel = guild.get_channel(channel_id)
        await channel.send(f"{user.mention} Artık aramızdan birisin! İyi eğlenceler!")

        logger.info(f"{user.name} - User added to nsfw by {ctx.message.author.name}.")
    
@client.command(pass_context = True)
@commands.is_owner()
async def reset_people(ctx):
    users_db.purge()
    
    await ctx.send("User database deleted!")
    logger.info(f"{ctx.guild.name} - user database has been reset.")


@client.command(pass_context = True)
@commands.is_owner()
async def add_people(ctx, role : discord.Role):

    for member in role.members:
        if not users_db.contains(query.id == member.id):

            users_db.insert({"username":member.name, "id":member.id})

    await ctx.send(f"{role.name} users added to database.")
    logger.info(f"{ctx.guild.name} - Members with {role.name} role are added to user database.")

client.run('TOKEN')