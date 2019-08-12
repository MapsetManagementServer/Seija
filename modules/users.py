
from modules import db
import discord
import time
import datetime
import asyncio
import upsidedown
import pycountry
from collections import Counter
import operator

from modules.connections import osu as osu
from osuembed import osuembed


async def send_notice(notice, channel, now):
    if not db.query(["SELECT notice FROM notices WHERE notice = ?", [notice]]):
        await channel.send(notice)
        db.query(["INSERT INTO notices VALUES (?, ?)", [str(now.isoformat()), notice]])


async def statscalc(data):
    results = dict(Counter(data))
    return reversed(sorted(results.items(), key=operator.itemgetter(1)))


async def demographics(client, ctx):
    async with ctx.channel.typing():
        masterlist = []
        for member in ctx.guild.members:
            if not member.bot:
                query = db.query(["SELECT country FROM users WHERE user_id = ?", [str(member.id)]])
                if query: # [5]
                    masterlist.append(query[0][0])
        stats = await statscalc(masterlist)

        rank = 0
        contents = ""
        memberamount = len(masterlist)

        for oneentry in stats:
            rank += 1
            amount = str(oneentry[1])+" Members"
            percentage = str(round(float(int(oneentry[1]) * 100 / memberamount), 2))
            try:
                countryobject = pycountry.countries.get(alpha_2=oneentry[0])
                countryname = countryobject.name
                countryflag = ":flag_%s:" % (oneentry[0].lower())
            except:
                countryflag = ":gay_pride_flag:"
                countryname = oneentry[0]
            contents += "**[%s]** : %s **%s** : %s : %s %% \n" % (rank, countryflag, countryname, amount, percentage)
            if len(contents) > 1800:
                statsembed = discord.Embed(description=contents, color=0xbd3661)
                statsembed.set_author(name="Server Demographics")
                await ctx.send(embed=statsembed)
                contents = ""
        
        if contents == "":
            contents = "\n"
        statsembed = discord.Embed(description=contents, color=0xbd3661)
        statsembed.set_author(name="Server Demographics")
    await ctx.send(embed=statsembed)


async def users_from(client, ctx, country_code):
    async with ctx.channel.typing():
        try:
            if len(country_code) == 2:
                countryobject = pycountry.countries.get(alpha_2=country_code.upper())
            elif len(country_code) == 3:
                countryobject = pycountry.countries.get(alpha_3=country_code.upper())
            else:
                countryobject = pycountry.countries.get(name=country_code)
            countryname = countryobject.name
            countryflag = ":flag_%s:" % (countryobject.alpha_2.lower())
        except:
            countryobject = None
            countryflag = "\n"
            countryname = "Country not found. Keep in mind that full country names are case-sensetive.\nYou can also try searching with alpha 2 codes."
        masterlist = []
        if countryobject:
            for member in ctx.guild.members:
                if not member.bot:
                    query = db.query(["SELECT osu_username, osu_id FROM users WHERE country = ? AND user_id = ?", [str(countryobject.alpha_2.upper()), str(member.id)]])
                    if query:
                        masterlist.append(query[0])
        memberamount = len(masterlist)
        masterlist.sort()
        contents = "%s members from %s %s\n" % (str(memberamount), countryflag, countryname)

        for one_member in masterlist:
            contents += "[%s](https://osu.ppy.sh/users/%s)\n" % (one_member[0], one_member[1])
            if len(contents) > 1800:
                statsembed = discord.Embed(description=contents, color=0xbd3661)
                statsembed.set_author(name="Country Demographics")
                await ctx.send(embed=statsembed)
                contents = ""
        
        if contents == "":
            contents = "\n"
        statsembed = discord.Embed(description=contents, color=0xbd3661)
        statsembed.set_author(name="Country Demographics")
    await ctx.send(embed=statsembed)


async def verify(channel, member, guild, lookup_type, lookup_string, response):
    # Defaults
    osuusername = None
    osu_join_date = ""
    pp = "0"
    country = ""
    ranked_amount = "0"
    no_sync = "0"

    try:
        if lookup_type == "u":
            osuprofile = await osu.get_user(u=lookup_string)
            if osuprofile:
                osuusername = str(osuprofile.name)
                osuaccountid = str(osuprofile.id)
                osu_join_date = str(osuprofile.join_date)
                pp = str(osuprofile.pp_raw)
                country = str(osuprofile.country)
                embed = await osuembed.user(osuprofile)
        elif lookup_type == "s":
            authorsmapset = await osu.get_beatmapset(s=lookup_string)
            if authorsmapset:
                osuusername = str(authorsmapset.creator)
                osuaccountid = str(authorsmapset.creator_id)
                embed = await osuembed.beatmapset(authorsmapset)

        if osuusername:

            ranked_amount = len(await get_ranked_maps(await osu.get_beatmaps(u=str(osuaccountid))))

            if ranked_amount >= 10:
                role = discord.utils.get(guild.roles, id=int((db.query(["SELECT value FROM config WHERE setting = ? AND parent = ?", ["guild_experienced_mapper_role", str(guild.id)]]))[0][0]))
            elif ranked_amount >= 1:
                role = discord.utils.get(guild.roles, id=int((db.query(["SELECT value FROM config WHERE setting = ? AND parent = ?", ["guild_ranked_mapper_role", str(guild.id)]]))[0][0]))
            else:
                role = discord.utils.get(guild.roles, id=int((db.query(["SELECT value FROM config WHERE setting = ? AND parent = ?", ["guild_mapper_role", str(guild.id)]]))[0][0]))

            if type(member) is str:
                user_id = member
            else:
                user_id = str(member.id)
                try:
                    await member.add_roles(role)
                    await member.edit(nick=osuusername)
                except Exception as e:
                    print(time.strftime('%X %x %Z'))
                    print("in users.verify")
                    print(e)

            if db.query(["SELECT user_id FROM users WHERE user_id = ?", [user_id, ]]):
                print("user %s already in database" % (user_id,))
                # possibly force update the entry in future
            else:
                print("adding user %s in database" % (user_id,))
                db.query(["INSERT INTO users VALUES (?,?,?,?,?,?,?,?)", [user_id, osuaccountid, osuusername, osu_join_date, pp, country, ranked_amount, no_sync]])

            if not response:
                response = "verified <@%s>" % (user_id)

            await channel.send(content=response, embed=embed)
            return True
        else:
            return None
    except Exception as e:
        print(e)
        print("Connection issues?")
        await channel.send(content="It looks like osu's website is down so I can't verify at this moment. Ping managers or something or try again later.")

async def unverify(ctx, user_id):
    db.query(["DELETE FROM users WHERE user_id = ?", [user_id, ]])
    member = ctx.guild.get_member(int(user_id))
    if member:
        try:
            await member.edit(roles=[])
            await ctx.send("Done")
        except Exception as e:
            await ctx.send(e)

async def guildnamesync(ctx):
    now = datetime.datetime.now()
    for member in ctx.guild.members:
        if not member.bot:
            query = db.query(["SELECT * FROM users WHERE user_id = ?", [str(member.id)]])
            if query:
                try:
                    osuprofile = osu.get_user(u=query[0][1])
                    if osuprofile:
                        await one_guild_member_sync(ctx.channel, query, now, member, osuprofile)
                    else:
                        await ctx.channel.send("%s | `%s` | `%s` | <https://osu.ppy.sh/users/%s> | restricted" % (member.mention, str(query[0][2]), str(query[0][1]), str(query[0][1])))
                except Exception as e:
                    print(e)
                    print("Connection issues?")
            else:
                await ctx.send("%s | not in db" % (member.mention))

async def roleless(ctx, mention):
    for member in ctx.guild.members:
        if len(member.roles) < 2:
            await ctx.send(member.mention)
            if mention:
                try:
                    query = db.query(["SELECT osu_id FROM users WHERE user_id = ?", [str(member.id)]])
                    if query:
                        await ctx.send("person above is in my database and linked to <https://osu.ppy.sh/users/%s>" % (query[0][0]))
                except Exception as e:
                    await ctx.send(e)



async def mapping_username_loop(client):
    try:
        await asyncio.sleep(3600)
        print(time.strftime('%X %x %Z')+' | user event tracker')
        memberfeedchannellist = db.query(["SELECT * FROM config WHERE setting = ?", ["guild_user_event_tracker"]])
        if memberfeedchannellist:
            now = datetime.datetime.now()
            for onechannel in memberfeedchannellist:
                auditchannel = client.get_channel(int(onechannel[3]))
                feedchannel = client.get_channel(int(onechannel[2]))
                guild = client.get_guild(int(onechannel[1]))
                for member in guild.members:
                    if not member.bot:
                        query = db.query(["SELECT * FROM users WHERE user_id = ?", [str(member.id)]])
                        if query:
                            try:
                                check_if_restricted_user_in_db = db.query(["SELECT osu_id FROM restricted_users WHERE guild_id = ? AND osu_id = ?", [str(guild.id), str(query[0][1])]])
                                osuprofile = await osu.get_user(u=query[0][1], event_days="1")
                                if osuprofile:
                                    await one_guild_member_sync(auditchannel, query, now, member, osuprofile)
                                    await check_events(client, feedchannel, osuprofile, "user_event_history")
                                    if check_if_restricted_user_in_db:
                                        await auditchannel.send("%s | `%s` | `%s` | <https://osu.ppy.sh/users/%s> | unrestricted lol" % (member.mention, str(query[0][2]), str(query[0][1]), str(query[0][1])))
                                        db.query(["DELETE FROM restricted_users WHERE guild_id = ? AND osu_id = ?", [str(guild.id), str(query[0][1])]])
                                else:
                                    # at this point we are sure that the user is restricted.
                                    if not check_if_restricted_user_in_db:
                                        await auditchannel.send("%s | `%s` | `%s` | <https://osu.ppy.sh/users/%s> | restricted" % (member.mention, str(query[0][2]), str(query[0][1]), str(query[0][1])))
                                        db.query(["INSERT INTO restricted_users VALUES (?,?)", [str(guild.id), str(query[0][1])]])
                            except Exception as e:
                                print(e)
                                print("Connection issues?")
                                await asyncio.sleep(120)
                        else:
                            await send_notice("%s | not in db" % (member.mention), auditchannel, now)
                        await asyncio.sleep(1)
        print(time.strftime('%X %x %Z')+' | mapping username loop finished')
        await asyncio.sleep(3600)
    except Exception as e:
        print(time.strftime('%X %x %Z'))
        print("in membertrack")
        print(e)
        await asyncio.sleep(7200)


async def check_events(client, channel, user, history_table_name):
    print(time.strftime('%X %x %Z')+" | currently checking %s" % (user.name))
    for event in user.events:
        if not db.query(["SELECT event_id FROM %s WHERE event_id = ?" % (history_table_name), [str(event.id)]]):
            db.query(["INSERT INTO %s VALUES (?, ?, ?)" % (history_table_name), [str(user.id), str(event.id), str(channel.id)]])
            event_color = await get_event_color(event.display_text)
            if event_color:
                result = await osu.get_beatmapset(s=event.beatmapset_id)
                embed = await osuembed.beatmapset(result, event_color)
                if embed:
                    display_text = (event.display_text).replace("@", "")
                    print(display_text)
                    await channel.send(display_text, embed=embed)


async def get_event_color(string):
    if 'has submitted' in string:
        return 0x2a52b2
    elif 'has updated' in string:
        #return 0xb2532a
        return None
    elif 'qualified' in string:
        return 0x2ecc71
    elif 'has been revived' in string:
        return 0xff93c9
    elif 'has been deleted' in string:
        return 0xf2d7d5
    else:
        return None


async def one_guild_member_sync(auditchannel, query, now, member, osuprofile):
    if "04-01T" in str(now.isoformat()):
        osuusername = upsidedown.transform(osuprofile.name)
    else:
        osuusername = osuprofile.name
    if str(query[0][2]) != osuusername:
        await auditchannel.send("`%s` namechanged to `%s`. osu_id = `%s`" % (str(query[0][2]), osuusername, str(query[0][1])))
        if str(query[0][1]) == str(4116573):
            await auditchannel.send("This is bor btw. Yes, I actually added this specific message for bor in this bot.")
    if member.display_name != osuusername:
        if "1" in str(query[0][7]):
            await send_notice("%s | `%s` | `%s` | username not updated as `no_sync` was set for this user" % (str(member.mention), osuusername, str(query[0][1])), auditchannel, now)
        else:
            old_nickname = member.display_name
            try:
                await member.edit(nick=osuusername)
            except Exception as e:
                await auditchannel.send(e)
                await auditchannel.send("%s | `%s` | `%s` | no perms to update" % (member.mention, osuusername, str(query[0][1])))
            await auditchannel.send("%s | `%s` | `%s` | nickname updated, old nickname `%s`" % (member.mention, osuusername, str(query[0][1]), old_nickname))
    db.query(
        [
            "UPDATE users SET country = ?, pp = ?, osu_join_date = ?, osu_username = ? WHERE user_id = ?;",
            [
                str(osuprofile.country),
                str(osuprofile.pp_raw),
                str(osuprofile.join_date),
                str(osuprofile.name),
                str(member.id)
            ]
        ]
    )


async def on_member_join(client, member):
    try:
        guildverifychannel = db.query(["SELECT value FROM config WHERE setting = ? AND parent = ?", ["guild_verify_channel", str(member.guild.id)]])
        if guildverifychannel:
            join_channel_object = client.get_channel(int((guildverifychannel)[0][0]))
            if not member.bot:
                lookupuser = db.query(["SELECT osu_id FROM users WHERE user_id = ?", [str(member.id), ]])
                if lookupuser:
                    print("user %s joined with osu_id %s" % (str(member.id), str(lookupuser[0][0])))
                    verifyattempt = await verify(join_channel_object, member, member.guild, "u", lookupuser[0][0], "Welcome aboard %s! Since we know who you are, I have automatically verified you. Enjoy your stay!" % (member.mention))

                    if not verifyattempt:
                        await join_channel_object.send("Hello %s. We have a verification system in this server, to keep raids and spam out. It seems like you are in my database but the profile I know of you is restricted. If this is correct, please link any of your uploaded maps (new website only) and I'll verify you instantly. If this is not correct, tag Kyuunex." % (member.mention))
                else:
                    await join_channel_object.send("Welcome %s! We have a verification system in this server so that we know who you are, give you appropriate roles and keep raids/spam out." % (member.mention))
                    try:
                        osuprofile = await osu.get_user(u=member.name)
                    except Exception as e:
                        print(e)
                        print("Connection issues?")
                        osuprofile = None
                    if osuprofile:
                        await join_channel_object.send(content='Is this your osu profile? If yes, type `yes`, if not, link your profile.', embed=await osuembed.user(osuprofile))
                    else:
                        await join_channel_object.send('Please post a link to your osu profile and I will verify you instantly.')
            else:
                await join_channel_object.send('beep boop boop beep, %s has joined our army of bots' % (member.mention))
    except Exception as e:
        print(time.strftime('%X %x %Z'))
        print("in on_member_join")
        print(e)


async def on_member_remove(client, member):
    try:
        guildverifychannel = db.query(["SELECT value FROM config WHERE setting = ? AND parent = ?", ["guild_verify_channel", str(member.guild.id)]])
        if guildverifychannel:
            join_channel_object = client.get_channel(int((guildverifychannel)[0][0]))
            if not member.bot:
                osu_id = db.query(["SELECT osu_username FROM users WHERE user_id = ?", [str(member.id)]])
                if osu_id:
                    try:
                        memberprofile = await osu.get_user(u=osu_id[0][0])
                        embed = await osuembed.user(memberprofile)
                    except Exception as e:
                        print(e)
                        print("Connection issues?")
                        embed = None
                else:
                    embed = None
                await join_channel_object.send("%s left this server. Godspeed!" % (str(member.name)), embed=embed)
            else:
                await join_channel_object.send('beep boop boop beep, %s has left our army of bots' % (member.mention))
    except Exception as e:
        print(time.strftime('%X %x %Z'))
        print("in on_member_join")
        print(e)


async def on_message(client, message):
    if message.author.id != client.user.id:
        try:
            verifychannel_id = db.query(["SELECT value FROM config WHERE setting = ? AND parent = ?", ["guild_verify_channel", str(message.guild.id)]])
            if verifychannel_id:
                if message.channel.id == int(verifychannel_id[0][0]):
                    split_message = []
                    if '/' in message.content:
                        split_message = message.content.split('/')

                    if 'https://osu.ppy.sh/u' in message.content:
                        verifyattempt = await verify(message.channel, message.author, message.guild, "u", (split_message[4].split(' ')[0]), "`Verified: %s`" % (message.author.name))
                        if not verifyattempt:
                            await message.channel.send('verification failure, I can\'t find any profile from that link. If you are restricted, link any of your recently uploaded maps (new website only). if you are not restricted, then maybe osu website is down at this moment and in that case, ping Kyuunex or try again later.')
                    elif 'https://osu.ppy.sh/beatmapsets/' in message.content:
                        verifyattempt = await verify(message.channel, message.author, message.guild, "s", (split_message[4].split('#')[0]), "`Verified through mapset: %s`" % (message.author.name))
                        if not verifyattempt:
                            await message.channel.send('verification failure, I can\'t find any map with that link')
                    elif message.content.lower() == 'yes':
                        verifyattempt = await verify(message.channel, message.author, message.guild, "u", message.author.name, "`Verified: %s`" % (message.author.name))
                        if not verifyattempt:
                            await message.channel.send('verification failure, your discord username does not match a username of any osu account. possible reason can be that you changed your discord username before typing `yes`. In this case, link your profile.')
                    elif 'https://ripple.moe/u' in message.content:
                        await message.channel.send('ugh, this bot does not do automatic verification from ripple, please ping Kyuunex')
                    elif 'https://osu.gatari.pw/u' in message.content:
                        await message.channel.send('ugh, this bot does not do automatic verification from gatari, please ping Kyuunex')
        except Exception as e:
            print(time.strftime('%X %x %Z'))
            print("in on_message")
            print(e)


async def get_ranked_maps(beatmaps):
    try:
        ranked_maps = []
        if beatmaps:
            for beatmap in beatmaps:
                if beatmap.approved == "1" or beatmap.approved == "2":
                    if not beatmap.beatmapset_id in ranked_maps:
                        ranked_maps.append(beatmap.beatmapset_id)
        return ranked_maps
    except Exception as e:
        print(e)
        return []


async def check_ranked(ctx, mention):
    role = discord.utils.get(ctx.guild.roles, id=int((db.query(["SELECT value FROM config WHERE setting = ? AND parent = ?", ["guild_mapper_role", str(ctx.guild.id)]]))[0][0]))
    if role:
        output = "These fella's have at least 1 ranked map:\n"
        async with ctx.channel.typing():
            for member in role.members:
                lookupuser = db.query(["SELECT osu_id FROM users WHERE user_id = ?", [str(member.id), ]])
                if lookupuser:
                    mapsbythisguy = await osu.get_beatmaps(u=str(lookupuser[0][0]))
                    if mapsbythisguy:
                        try:
                            ranked_amount = len(await get_ranked_maps(mapsbythisguy))
                        except Exception as e:
                            print(e)
                            print("Connection issues?")
                            ranked_amount = 0
                        if ranked_amount >= 1:
                            output += "%s\n" % (member.mention)
                    else:
                        print("problem with %s" % (member.display_name))
                await asyncio.sleep(0.5)
        await ctx.send(output)
    else:
        await ctx.send("Nope")


async def check_experienced(ctx, mention):
    role = discord.utils.get(ctx.guild.roles, id=int((db.query(["SELECT value FROM config WHERE setting = ? AND parent = ?", ["guild_ranked_mapper_role", str(ctx.guild.id)]]))[0][0]))
    if role:
        output = "These fella's have at least 10 ranked maps:\n"
        async with ctx.channel.typing():
            for member in role.members:
                lookupuser = db.query(["SELECT osu_id FROM users WHERE user_id = ?", [str(member.id), ]])
                if lookupuser:
                    mapsbythisguy = await osu.get_beatmaps(u=str(lookupuser[0][0]))
                    if mapsbythisguy:
                        try:
                            ranked_amount = len(await get_ranked_maps(mapsbythisguy))
                        except Exception as e:
                            print(e)
                            print("Connection issues?")
                            ranked_amount = 0
                        if ranked_amount >= 10:
                            output += "%s\n" % (member.mention)
                    else:
                        print("problem with %s" % (member.display_name))
                await asyncio.sleep(0.5)
        await ctx.send(output)
    else:
        await ctx.send("Nope")


async def print_all(ctx, mention):
    try:
        if mention == "m":
            tag = "<@%s> / %s"
        else:
            tag = "%s / %s"
        for oneuser in db.query("SELECT * FROM users"):
            try:
                userprofile = await osu.get_user(u=oneuser[1])
                embed = await osuembed.user(userprofile)
            except:
                print("Connection issues?")
                await ctx.send("Connection issues?")
                await asyncio.sleep(10)
                embed = None
            if embed:
                await ctx.send(content=tag % (oneuser[0], oneuser[2]), embed=embed)
    except Exception as e:
        print(time.strftime('%X %x %Z'))
        print("in userdb")
        print(e)


async def mass_verify(ctx, mention):
    try:
        userarray = open("data/users.csv", encoding="utf8").read().splitlines()
        if mention == "m":
            tag = "Preverified: <@%s>"
        else:
            tag = "Preverified: %s"
        for oneuser in userarray:
            uzer = oneuser.split(',')
            await verify(ctx.message.channel, str(uzer[1]), None, "u", uzer[0], tag % (str(uzer[1])))
            await asyncio.sleep(1)
    except Exception as e:
        print(time.strftime('%X %x %Z'))
        print("in userdb")
        print(e)


async def server_check(ctx, mention):
    try:
        responce = "These users are not in my database:\n"
        count = 0
        for member in ctx.guild.members:
            if not member.bot:
                if not db.query(["SELECT osu_id FROM users WHERE user_id = ?", [str(member.id), ]]):
                    count += 1
                    if mention == "m":
                        responce += ("<@%s>\n" % (str(member.id)))
                    else:
                        responce += ("\"%s\" %s\n" % (str(member.display_name), str(member.id)))
                    if count > 40:
                        count = 0
                        responce += ""
                        await ctx.send(responce)
                        responce = "\n"
        responce += ""
        await ctx.send(responce)
    except Exception as e:
        print(time.strftime('%X %x %Z'))
        print("in userdb")
        print(e)


async def mverify(ctx, lookup_type, osu_id, user_id, preverify):
    try:
        if preverify == "preverify":
            await verify(ctx.message.channel, str(user_id), None, lookup_type, osu_id, "Preverified: %s" % (str(user_id)))
        elif preverify == "restricted":
            db.query(["INSERT INTO users VALUES (?,?,?,?,?,?,?,?)", [user_id, osu_id, "", "", "", "", "", ""]])
            await ctx.send("lol ok")
        else:
            await verify(ctx.message.channel, ctx.guild.get_member(user_id), ctx.message.guild, lookup_type, osu_id, "Manually Verified: %s" % (ctx.guild.get_member(user_id).name))
    except Exception as e:
        print(time.strftime('%X %x %Z'))
        print("in verify")
        print(e)

#TODO: add general welcome message with one message template chosen from db