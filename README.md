# Executive Decisions Discord bot

Run **/setup** as the Discord server owner to build the Executive Decisions layout in a server you own.

| Category | Channels | Access |
| --- | --- | --- |
| @Executive Decisions ! | #welcome, #fineprint, #boosts | Everyone can read. Executive Staff can post. |
| •1˚₊ | #hype, #drops | Everyone can read. Executive Staff can post. |
| •2˚₊ | #announcements, #giveaways, #events, #news | Everyone can read. Executive Staff can post. |
| •3˚₊ | #the-boardroom, #fit-checks | Everyone can read and post. |
| •4˚₊ | #secrets | Executive Staff and Secrets Clearance. |
| •5˚₊ | Boardroom, After Hours, Runway Stage | Open to everyone. Runway Stage requires Community. |
| • priv vcs | Closed Session | Executive Staff and Secrets Clearance. |
| • staff | #staff-announcements, #staff-room, #staff-guide, #drop-planning, #appeals, #staff-cmds, Staff Voice, Staff Stage | Executive Staff. Staff Stage requires Community. |
| • staff logs | #mod-log, #security-alerts, #staff-log, #ticket-transcripts, #voice-logs, #member-logs, #server-logs | Executive Staff. |

The bot posts your full welcome message and uses your short brand description as the #welcome topic. Discord’s server owner and anyone with Administrator can access all channels. Give staff **Executive Staff** and selected members **Secrets Clearance**. Clearance grants access to #secrets and Closed Session.

## Deploy to Railway from GitHub

1. Create a Discord server and install your bot using steps 1–4 under **Discord setup and local run**. Keep the bot token and server ID handy.
2. Create a GitHub repository and upload the **contents** of this folder, including `.gitignore` and `.dockerignore`. The repository root should contain `bot.py`, `Dockerfile`, `requirements.txt`, and `railway.toml`.
3. In Railway, choose **New Project → Deploy from GitHub repo** and select your repository. If you keep this folder inside a larger repository, set the service **Root Directory** to `/executive-decisions` and its **Config File Path** to `/executive-decisions/railway.toml`.
4. In the Railway service’s **Variables** tab, add `DISCORD_TOKEN` with your bot token and `DISCORD_GUILD_ID` with your server ID. Apply the changes to deploy. Keep the token in Railway and out of the GitHub repository.
5. Check the deployment logs for the Discord Gateway connection. Then run **/setup** in your Discord server as its owner.

The Railway service runs as a background worker. It uses Discord’s outbound Gateway connection and needs no public domain or HTTP health check. Keep one replica running.

## Discord setup and local run

1. Create a blank Discord server called **Executive Decisions**. This is the server the bot will configure.
2. Create an application in the [Discord Developer Portal](https://discord.com/developers/applications). In its **Bot** settings, generate a bot token. Keep the token private.
3. In the application’s **Installation** settings, enable **Guild Install** with the `bot` and `applications.commands` scopes. For setup, grant the bot **Administrator**, then open the installation link and add it to Executive Decisions. You can remove the bot after setup if you only need the layout.
4. In Discord, enable **Developer Mode** under **User Settings → Advanced**. Right-click the server icon and choose **Copy Server ID**.
5. From this folder, use Python 3.10 or later. In macOS or Linux, run:

   ```bash
   python3 -m venv .venv
   . .venv/bin/activate
   python -m pip install -r requirements.txt
   read -rsp 'Discord bot token: ' DISCORD_TOKEN
   echo
   export DISCORD_TOKEN
   export DISCORD_GUILD_ID='paste-server-id-here'
   python bot.py
   ```

   In Windows PowerShell, run:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   $env:DISCORD_TOKEN = Read-Host 'Discord bot token' -MaskInput
   $env:DISCORD_GUILD_ID = 'paste-server-id-here'
   .\.venv\Scripts\python.exe bot.py
   ```

   The masked input example uses PowerShell 7.

6. Run **/setup** in Discord, then assign roles under **Server Settings → Roles**.

If Discord Community is enabled, the bot creates Stage channels and makes #welcome, #boosts, and the numbered announcement feeds followable. Otherwise those feeds are read-only text channels for members. After enabling Community you can rerun **/setup** to add the stages and upgrade the feeds.

Rerunning **/setup** reuses matching role, category, and channel names and reapplies the layout’s permissions. If you ran the earlier Executive Decisions bot, the update can rename its original categories and move its announcement feeds with their message history. You can drag any existing categories into your preferred order in Discord.

The bot creates the log, transcripts, and rules channels for you to configure. Staff can use the rooms manually or connect a separate moderation bot for automatic logs and tickets. The setup bot can be stopped once the layout is ready.
