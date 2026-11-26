import asyncio
import logging
import os

import discord
from discord import app_commands

WELCOME = """WELCOME TO EXECUTIVE DECISIONS.
This is the inner circle of a fashion house built for women who run the room — the executives, the secretaries, the ones closing deals in heels. Sexy. Authoritative. Never asking permission.
What happens here:
🔥 HYPE — Be first in line. Drops are announced here before anywhere else on the internet.
🛍️ DROPS — Members get early access windows, restock alerts, and exclusive colorways the public never sees.
👥 THE BOARDROOM — Community lounge. Fit checks, career wins, “what was on our schedule today” energy.
🎁 GIVEAWAYS — Pieces, gift cards, and secret drops. Active members get weighted entries.
📅 EVENTS — Launch parties, pop-ups, live styling sessions, AMAs.
📰 NEWS — Brand announcements, behind-the-scenes from design to production.
🤫 SECRETS — Classified channel. Codes, teasers, and intel for those cleared for it. You’ll know when you’ve earned it.
The decision was hers. She made it. Now make yours.
“Executive Decisions.” — full stop."""

DESCRIPTION = (
    "Executive Decisions - where she decided. Official home of the brand: first "
    "access to drops, members-only giveaways, events, insider news & secrets. "
    "The boardroom is open. Make yours. 💼"
)

ANNOUNCEMENTS = {
    "announcements": "Official announcements from Executive Decisions.",
    "hype": "First looks, teasers, and drop countdowns.",
    "drops": "Early access, restocks, and exclusive colorways.",
    "giveaways": "Official giveaway posts and entry details.",
    "events": "Launch parties, pop-ups, styling sessions, and AMAs.",
    "news": "Brand news and behind-the-scenes updates.",
}


class ExecutiveDecisions(discord.Client):
    def __init__(self, guild_id: int):
        super().__init__(intents=discord.Intents(guilds=True))
        self.target = discord.Object(id=guild_id)
        self.tree = app_commands.CommandTree(self)
        self.tree.add_command(setup, guild=self.target)
        self.setup_lock = asyncio.Lock()

    async def setup_hook(self):
        await self.tree.sync(guild=self.target)


async def get_role(guild, name):
    matches = [role for role in await guild.fetch_roles() if role.name == name]
    if len(matches) > 1:
        raise ValueError(f"Multiple roles are named {name!r}. Give them unique names and retry.")
    if matches:
        return matches[0]
    return await guild.create_role(name=name, permissions=discord.Permissions.none())


async def provision(guild):
    bot = guild.me
    everyone = guild.default_role
    staff = await get_role(guild, "Executive Staff")
    cleared = await get_role(guild, "Secrets Clearance")
    access = discord.PermissionOverwrite(
        view_channel=True, send_messages=True, read_message_history=True
    )
    read_only = discord.PermissionOverwrite(
        view_channel=True,
        read_message_history=True,
        send_messages=False,
        send_messages_in_threads=False,
        create_public_threads=False,
        create_private_threads=False,
    )
    hidden = discord.PermissionOverwrite(view_channel=False)
    public_chat = discord.PermissionOverwrite(
        view_channel=True, send_messages=True, read_message_history=True
    )
    channels = await guild.fetch_channels()
    community = "COMMUNITY" in guild.features

    async def ensure_category(name, overwrites, legacy_name=None):
        matches = [
            channel for channel in channels
            if isinstance(channel, discord.CategoryChannel) and channel.name == name
        ]
        if not matches and legacy_name:
            matches = [
                channel for channel in channels
                if isinstance(channel, discord.CategoryChannel) and channel.name == legacy_name
            ]
        if len(matches) > 1:
            raise ValueError(f"Multiple categories are named {name!r}. Rename the duplicates and retry.")
        if matches:
            return await matches[0].edit(name=name, overwrites=overwrites)
        return await guild.create_category(name, overwrites=overwrites)

    async def ensure_text(
        category, name, topic, overwrites, *, announcement=False, previous_category=None
    ):
        matches = [
            channel for channel in channels
            if isinstance(channel, discord.TextChannel)
            and channel.category_id == category.id and channel.name == name
        ]
        if not matches and previous_category is not None:
            matches = [
                channel for channel in channels
                if isinstance(channel, discord.TextChannel)
                and channel.category_id == previous_category.id and channel.name == name
            ]
        if len(matches) > 1:
            raise ValueError(f"Multiple channels in {category.name!r} are named #{name}. Rename the duplicates and retry.")
        if matches:
            channel = matches[0]
            if channel.category_id != category.id:
                channel = await channel.edit(category=category, sync_permissions=True) or channel
            channel = await channel.edit(topic=topic, overwrites=overwrites)
        else:
            channel = await guild.create_text_channel(
                name, category=category, topic=topic, overwrites=overwrites
            )
        if announcement and community and not channel.is_news():
            channel = await channel.edit(type=discord.ChannelType.news)
        return channel

    async def ensure_audio(category, name, overwrites, *, stage=False):
        channel_class = discord.StageChannel if stage else discord.VoiceChannel
        matches = [
            channel for channel in channels
            if isinstance(channel, channel_class)
            and channel.category_id == category.id and channel.name == name
        ]
        if len(matches) > 1:
            raise ValueError(f"Multiple audio channels in {category.name!r} are named {name!r}.")
        if matches:
            await matches[0].edit(overwrites=overwrites)
            return
        create = guild.create_stage_channel if stage else guild.create_voice_channel
        await create(name, category=category, overwrites=overwrites)

    announcements_access = {everyone: read_only, staff: access, bot: access}
    chat_access = {everyone: public_chat, staff: access, bot: access}
    staff_access = {everyone: hidden, staff: access, bot: access}
    secrets_access = {**staff_access, cleared: access}
    audio_access = discord.PermissionOverwrite(
        view_channel=True, connect=True, speak=True
    )
    open_audio = {everyone: audio_access, staff: audio_access, bot: audio_access}
    staff_audio = {everyone: hidden, staff: audio_access, bot: audio_access}
    cleared_audio = {**staff_audio, cleared: audio_access}

    intro = await ensure_category(
        "@Executive Decisions !", announcements_access, legacy_name="EXECUTIVE DECISIONS"
    )
    welcome = await ensure_text(intro, "welcome", DESCRIPTION, announcements_access, announcement=True)
    await ensure_text(intro, "fineprint", "Server rules and membership guidelines.", announcements_access)
    await ensure_text(intro, "boosts", "Server boost shout-outs.", announcements_access, announcement=True)
    async for message in welcome.history(limit=None):
        if message.author.id == bot.id and message.content == WELCOME:
            break
    else:
        await welcome.send(WELCOME, allowed_mentions=discord.AllowedMentions.none())

    promo = await ensure_category("•1˚₊", announcements_access)
    updates = await ensure_category("•2˚₊", announcements_access)
    for name, topic in ANNOUNCEMENTS.items():
        category = promo if name in {"hype", "drops"} else updates
        await ensure_text(
            category, name, topic, announcements_access, announcement=True, previous_category=intro
        )

    boardroom = await ensure_category("•3˚₊", chat_access, legacy_name="THE BOARDROOM")
    await ensure_text(boardroom, "the-boardroom", "Career wins, daily schedules, and community chat.", chat_access)
    await ensure_text(boardroom, "fit-checks", "Share your looks and styling ideas.", chat_access)

    classified = await ensure_category("•4˚₊", secrets_access, legacy_name="CLASSIFIED")
    await ensure_text(classified, "secrets", "Codes, teasers, and intel for cleared members.", secrets_access)

    voice = await ensure_category("•5˚₊", open_audio)
    await ensure_audio(voice, "• Boardroom", open_audio)
    await ensure_audio(voice, "• After Hours", open_audio)
    if community:
        await ensure_audio(voice, "• Runway Stage", open_audio, stage=True)

    private_voice = await ensure_category("• priv vcs", cleared_audio)
    await ensure_audio(private_voice, "• Closed Session", cleared_audio)

    staff_category = await ensure_category("• staff", staff_access, legacy_name="STAFF ONLY")
    for name, topic in {
        "staff-announcements": "Internal staff announcements.",
        "staff-room": "Internal staff discussion.",
        "staff-guide": "Staff procedures and reference material.",
        "drop-planning": "Coordinate upcoming drops and events.",
        "appeals": "Staff discussion of member appeals.",
        "staff-cmds": "Staff bot commands.",
    }.items():
        await ensure_text(staff_category, name, topic, staff_access)
    await ensure_audio(staff_category, "• Staff Voice", staff_audio)
    if community:
        await ensure_audio(staff_category, "• Staff Stage", staff_audio, stage=True)

    staff_logs = await ensure_category("• staff logs", staff_access)
    for name in ("mod-log", "security-alerts", "staff-log", "ticket-transcripts", "voice-logs", "member-logs", "server-logs"):
        await ensure_text(staff_logs, name, "Private staff records.", staff_access)
    return welcome, community


@app_commands.command(name="setup", description="Build or refresh the Executive Decisions server layout.")
@app_commands.default_permissions(administrator=True)
async def setup(interaction: discord.Interaction):
    guild = interaction.guild
    if guild is None or interaction.user.id != guild.owner_id:
        await interaction.response.send_message("Only the server owner can run setup.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True, thinking=True)
    async with interaction.client.setup_lock:
        try:
            welcome, community = await provision(guild)
        except ValueError as error:
            await interaction.followup.send(str(error), ephemeral=True)
            return
        except discord.HTTPException as error:
            logging.exception("Discord rejected a setup operation for guild %s", guild.id)
            await interaction.followup.send(
                f"Setup paused after a Discord API error ({error.status}, code {error.code}). "
                "Check the bot's permissions and logs, then rerun /setup.",
                ephemeral=True,
            )
            return

    channel_type = (
        "The announcement feeds are Discord Announcement channels."
        if community else
        "The announcement feeds are read-only text channels for members. "
        "Enable Discord Community and rerun /setup to make them followable."
    )
    await interaction.followup.send(
        f"Executive Decisions is ready. Start in {welcome.mention}. {channel_type} "
        "Assign Executive Staff and Secrets Clearance in Server Settings → Roles.",
        ephemeral=True,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        token = os.environ["DISCORD_TOKEN"].strip()
        guild_id = int(os.environ["DISCORD_GUILD_ID"])
        if not token or guild_id <= 0:
            raise ValueError
    except (KeyError, ValueError):
        raise SystemExit("Set DISCORD_TOKEN and DISCORD_GUILD_ID before running the bot.")
    ExecutiveDecisions(guild_id).run(token)
