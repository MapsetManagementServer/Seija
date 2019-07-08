# Seija
Hi, if you are reading this, I am most likely gone, otherside you would not have access to this.
Anyways, I am leaving the source code behined so the next person who will take my role can get the place back up and running with minimal effort. 

This bot is built using discord.py rewrite library and uses sqlite3 database.

---

## Installation Instructions

1. Unpack files
2. Install git.
3. Install `python 3.6.7` or newer
4. Install `discord.py rewrite library` using this command `python -m pip install -U discord.py[voice]` for Windows and `python3 -m pip install -U discord.py[voice]` for Linux.
5. `pip install upsidedown feedparser pycountry Pillow`. (`pip3` on linux)
6. Before using, you need to create a folder called `data` and create `token.txt` and `osuapikey.txt` in it. Then put your bot token and osu api key in the files. 
7. If you have an access to `maindb.sqlite3` file which is a database backup, put it in `data` folder before running the bot. and then type `'resetadminlist` to scrap all admin entries and make yourself the bot owner in bot's db, and then manually add other admins with `'makeadmin (user_id)` command.
8. Run `run.py` with command line, like `python run.py` on windows or `python3 run.py` on linux or use the batch file or however you want. It's recommended to run it in a loop so it restarts when it exits. Built-in updater requires this.

## After running do these

1. Type following commands in chat. (the first id in each command is the id if the Mapset Management Server.)
```
'sql INSERT INTO config VALUES ('guild_verify_channel', '460935664712548366', '460952470634496001', '0')
'sql INSERT INTO config VALUES ('guild_veto_channel', '460935664712548366', '502705804990742573', '0')
'sql INSERT INTO config VALUES ('guild_db_dump_channel', '460935664712548366', '532397839784083458', '0')
'sql INSERT INTO config VALUES ('guild_user_event_tracker', '460935664712548366', '478293735315341322', '546583491270279169')

'sql INSERT INTO config VALUES ('guild_verify_role', '460935664712548366', '463790447912026132', '0')
'sql INSERT INTO config VALUES ('guild_ranked_mapper_role', '460935664712548366', '504247029359443969', '0')
'sql INSERT INTO config VALUES ('guild_experienced_mapper_role', '460935664712548366', '548236293428084757', '0')
'sql INSERT INTO config VALUES ('guild_bn_role', '460935664712548366', '489555825665507328', '0')
'sql INSERT INTO config VALUES ('guild_nat_role', '460935664712548366', '510923463368769536', '0')

'sql INSERT INTO config VALUES ('guild_mapset_category', '460935664712548366', '460935665165795328', '0')
'sql INSERT INTO config VALUES ('guild_queue_category', '460935664712548366', '488831339634753546', '0')
'sql INSERT INTO config VALUES ('guild_ranked_queue_category', '460935664712548366', '580708804006772736', '0')
'sql INSERT INTO config VALUES ('guild_bn_nat_queue_category', '460935664712548366', '534640743432847360', '0')
'sql INSERT INTO config VALUES ('guild_archive_category', '460935664712548366', '491572368221929472', '0')
```
2. Use `'makeadmin <new_admin_user_id>` to make users bot admins.
3. Use `'track <mapset_id> <mapset_host_user_id>` to track mapsets.
4. Figure out the rest yourselves. `'help` and `'help admin` commands exist.
