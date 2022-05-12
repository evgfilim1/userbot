import asyncio
import html
import logging
import random
import re
from calendar import TextCalendar
from datetime import datetime, timedelta
from functools import partial
from pathlib import Path
from tempfile import NamedTemporaryFile

import d20
import yaml
from httpx import AsyncClient
from pyrogram import Client, filters
from pyrogram.errors import BadRequest, MessageNotModified, ReactionEmpty, ReactionInvalid, \
    MsgIdInvalid
from pyrogram.methods.utilities.idle import idle
from pyrogram.raw import functions, types
from pyrogram.types import Message, Sticker

from modules import CommandsModule, HooksModule, ShortcutTransformersModule
from storage import PickleStorage, Storage
from utils import (
    GitHubMatch,
    HTMLDiceStringifier,
    create_filled_pic,
    edit_or_reply,
    en2ru_tr,
    enru2ruen_tr,
    get_text,
    ru2en_tr,
    sticker,
)

# region constants
TAP_STICKER = "CAADAgADVDIAAulVBRivj7VIBrE0GRYE"
TAP_FLT = "AgADVDIAAulVBRg"
MIBIB_STICKER = "CAACAgIAAx0CV1p3VwABAyvIYJY88iCdTjk40KWSi6qaQXm2dzkAAlwAAw56-wrkoTwgHGVmzx4E"
MIBIB_FLT = "AgADXAADDnr7Cg"
LONGCAT = dict(
    head_white=[
        "CAADBAADZQMAAuJy2QABJ1cx-fQb77sWBA",
        "CAADBAADgQMAAuJy2QABf0C0EPLQO0UWBA",
        "CAADBAADfQMAAuJy2QABdqWPKQVZFjAWBA",
    ],
    head_black=[
        "CAADBAADawMAAuJy2QABFA81XvWYIZ8WBA",
        "CAADBAADdQMAAuJy2QABt8J1yVBTIQoWBA",
        "CAADBAADdwMAAuJy2QABtC8HfQgRltwWBA",
    ],
    body_white="CAADBAADZwMAAuJy2QABQmx2g0C_s3cWBA",
    body_black="CAADBAADbQMAAuJy2QABwedDhS7jvv0WBA",
    feet_white=[
        "CAADBAADewMAAuJy2QABUy5kWdB3OU0WBA",
        "CAADBAADfwMAAuJy2QABCmgtpnxudVYWBA",
        "CAADBAADcQMAAuJy2QABQCpE5DuquCEWBA",
    ],
    feet_black=[
        "CAADBAADbwMAAuJy2QAB281pZP4ga8cWBA",
        "CAADBAADeQMAAuJy2QABvWnzh6NyAu4WBA",
    ],
)
PACK_ALIASES = {
    "a": "Degrodpack",
    "aa": "TrialITA",
    "ls": "ls_solyanka",
    "thomas": "thomas_shelby_kringepack",
    "hehe": "nothehe",
    "1px": "onepixel",
    "amogus": "tradinoi",
}
GH_PATTERN = re.compile(  # https://regex101.com/r/bvjYVf/1
    r"(?:github|gh):(?P<username>[a-zA-Z0-9\-_]+)(?:/(?P<repo>[a-zA-Z0-9\-_.]+|@)"
    r"(?:#(?P<issue>\d+)|(?:@(?P<branch>[a-zA-Z0-9.\-_/]+))?(?::/(?:(?P<path>[a-zA-Z0-9.\-_/]+)"
    r"(?:#L?(?P<line1>\d+)(?:-L?(?P<line2>\d+))?)?)?)?)?)?"
)
# endregion

logging.basicConfig(level=logging.WARNING)
commands = CommandsModule()
hooks = HooksModule()
shortcuts = ShortcutTransformersModule()


# region hooks
@hooks.add("duck", filters.regex(r"\b(?:дак|кря)\b", flags=re.I))
async def on_duck(_: Client, message: Message) -> None:
    await message.reply("🦆" * len(message.matches))


@hooks.add("tap", (filters.regex(r"\b(?:тык|nsr)\b", flags=re.I) | sticker(TAP_FLT)))
async def on_tap(_: Client, message: Message) -> None:
    await message.reply_sticker(TAP_STICKER)


@hooks.add("mibib", filters.sticker & sticker(MIBIB_FLT))
async def mibib(client: Client, message: Message) -> None:
    # TODO (2022-02-13): Don't send it again for N minutes
    if random.random() <= (1 / 5):
        await client.send_sticker(message.chat.id, MIBIB_STICKER)


async def check_hooks(_: Client, message: Message, __: str, *, storage: Storage) -> str:
    enabled = await storage.list_enabled_hooks(message.chat.id)
    return "Hooks in this chat: <code>" + "</code>, <code>".join(enabled) + "</code>"


# endregion


# region commands
@commands.add("longcat", usage="")
async def longcat(client: Client, message: Message, _: str) -> None:
    """Sends random longcat"""
    key = "black" if random.random() >= 0.5 else "white"
    head, body, tail = (
        random.choice(LONGCAT[f"head_{key}"]),
        LONGCAT[f"body_{key}"],
        random.choice(LONGCAT[f"feet_{key}"]),
    )
    body_len = random.randint(0, 3)
    await message.delete()
    for s in (head, *((body,) * body_len), tail):
        await client.send_sticker(message.chat.id, s)


@commands.add(["delete", "delet", "del"], usage="<reply>")
async def delete_this(_: Client, message: Message, __: str) -> None:
    """Deletes replied message"""
    try:
        await message.reply_to_message.delete()
    except BadRequest:
        pass
    await message.delete()


@commands.add("dump", usage="[dot-separated-attrs]")
async def dump(_: Client, message: Message, args: str) -> str:
    """Dumps entire message or its specified attribute"""
    obj = message.reply_to_message or message
    attrs = args.split(".")
    for attr in attrs:
        if attr:
            obj = getattr(obj, attr, None)
    return f"<b>Attribute</b> <code>{args}</code>\n\n<pre>{str(obj)}</pre>"


@commands.add("id", usage="<reply>")
async def mention_with_id(_: Client, message: Message, __: str) -> str:
    """Sends replied user's ID as link"""
    user = message.reply_to_message.from_user
    return f"<a href='tg://user?id={user.id}'>{user.id}</a>"


@commands.add(["roll", "dice"], usage="<dice-spec>")
async def dice(_: Client, __: Message, args: str) -> str:
    """Rolls dice according to d20.roll syntax"""
    return f"🎲 {d20.roll(args, stringifier=HTMLDiceStringifier())}"


@commands.add("promote", usage="<admin-title>")
async def promote(client: Client, message: Message, args: str) -> str:
    """Promotes a user to an admin without any rights but with title"""
    await client.invoke(
        functions.channels.EditAdmin(
            channel=await client.resolve_peer(message.chat.id),
            user_id=await client.resolve_peer(message.reply_to_message.from_user.id),
            admin_rights=types.chat_admin_rights.ChatAdminRights(
                change_info=False,
                delete_messages=False,
                ban_users=False,
                invite_users=False,
                pin_messages=False,
                add_admins=False,
                anonymous=False,
                manage_call=False,
                other=True,
            ),
            rank=args,
        )
    )
    return f"Должность в чате установлена на <i>{html.escape(args)}</i>"


@commands.add("calc", usage="<python-expr>")
async def calc(_: Client, __: Message, args: str) -> str:
    """Evaluates Python expression"""
    result = html.escape(f"{args} = {eval(args)!r}", quote=False)
    return f"<code>{result}</code>"


@commands.add("rnds", usage="<pack-link|pack-alias>")
async def random_sticker(client: Client, message: Message, args: str) -> None:
    """Sends random sticker from specified pack"""
    set_name = PACK_ALIASES.get(args, args)
    stickerset: types.messages.StickerSet = await client.invoke(
        functions.messages.GetStickerSet(
            stickerset=types.InputStickerSetShortName(
                short_name=set_name,
            ),
            hash=0,
        ),
    )
    sticker_raw: types.Document = random.choice(stickerset.documents)
    attributes = {type(i): i for i in sticker_raw.attributes}
    s = await Sticker._parse(  # huh...
        client,
        sticker_raw,
        attributes.get(types.DocumentAttributeImageSize, None),
        attributes[types.DocumentAttributeSticker],
        attributes[types.DocumentAttributeFilename],
    )
    kw = {}
    if message.reply_to_message is not None:
        kw["reply_to_message_id"] = message.reply_to_message.id
    await client.send_sticker(message.chat.id, s.file_id, **kw)
    await message.delete()


@commands.add("tr", usage="<reply> ['en'|'ru']")
async def tr(_: Client, message: Message, args: str) -> None:
    """Swaps keyboard layout from en to ru or vice versa"""
    # TODO (2021-12-01): detect ambiguous replacements via previous char
    # TODO (2022-02-17): work with entities
    text = get_text(message.reply_to_message)
    if args == "en":
        tr_abc = ru2en_tr
    elif args == "ru":
        tr_abc = en2ru_tr
    else:
        tr_abc = enru2ruen_tr
    translated = text.translate(tr_abc)
    answer, delete = edit_or_reply(message)
    try:
        await answer(translated)
    except MessageNotModified:
        pass
    if delete:
        await message.delete()


@commands.add("s", usage="<reply> <find-re>/<replace-re>/[flags]")
async def sed(_: Client, message: Message, args: str) -> None:
    """sed-like replacement"""
    # TODO (2022-02-17): work with entities
    text = get_text(message.reply_to_message)
    find_re, replace_re, flags_str = re.split(r"(?<!\\)/", args)
    find_re = find_re.replace("\\/", "/")
    replace_re = replace_re.replace("\\/", "/")
    flags = 0
    for flag in flags_str:
        flags |= getattr(re, flag.upper())
    text = re.sub(find_re, replace_re, text, flags=flags)
    answer, delete = edit_or_reply(message)
    try:
        await answer(text)
    except MessageNotModified:
        pass
    if delete:
        await message.delete()


@commands.add("color", usage="<color-spec>")
async def color(client: Client, message: Message, args: str) -> None:
    """Sends a specified color sample"""
    tmp = create_filled_pic(args)
    reply = getattr(message.reply_to_message, "message_id", None)
    await client.send_photo(
        message.chat.id,
        tmp,
        caption=f"Color {args}",
        reply_to_message_id=reply,
        disable_notification=True,
    )
    await message.delete()


@commands.add("usercolor", usage="<reply>")
async def user_color(client: Client, message: Message, _: str) -> None:
    """Sends a color sample of user's color as shown in clients"""
    colors = ("e17076", "eda86c", "a695e7", "7bc862", "6ec9cb", "65aadd", "ee7aae")
    c = f"#{colors[message.reply_to_message.from_user.id % 7]}"
    tmp = create_filled_pic(c)
    await client.send_photo(
        message.chat.id,
        tmp,
        caption=f"Your color is {c}",
        reply_to_message_id=message.reply_to_message.id,
        disable_notification=True,
    )
    await message.delete()


@commands.add(
    "userfirstmsg",
    usage="[reply]",
    waiting_message="<i>Searching for user's first message...</i>",
)
async def user_first_message(client: Client, message: Message, _: str) -> str | None:
    """Replies to user's very first message in the chat"""
    if (user := (message.reply_to_message or message).from_user) is None:
        return "Cannot search for first message from channel"
    chat_peer = await client.resolve_peer(message.chat.id)
    user_peer = await client.resolve_peer(user.id)
    first_msg_raw = None
    while True:
        # It's rather slow, but it works properly
        messages: types.messages.Messages = await client.invoke(
            functions.messages.Search(
                peer=chat_peer,
                q="",
                filter=types.InputMessagesFilterEmpty(),
                min_date=0,
                max_date=first_msg_raw.date if first_msg_raw else 0,
                offset_id=0,
                add_offset=0,
                limit=100,
                min_id=0,
                max_id=0,
                from_id=user_peer,
                hash=0,
            ),
            sleep_threshold=60,
        )
        prev_max_id = first_msg_raw.id if first_msg_raw else 0
        for m in messages.messages:
            if m.id < (first_msg_raw.id if first_msg_raw is not None else 2**64):
                first_msg_raw = m
        await asyncio.sleep(0.1)
        if not messages.messages or prev_max_id == first_msg_raw.id:
            break
    if not first_msg_raw:
        return "🐞⚠ Cannot find any messages from this user (wtf?)"
    text = f"This is the first message of {user.mention}"
    if isinstance(first_msg_raw.peer_id, types.PeerChannel):
        text += f"\nPermalink: https://t.me/c/{first_msg_raw.peer_id.channel_id}/{first_msg_raw.id}"
    await client.send_message(
        message.chat.id,
        text,
        reply_to_message_id=first_msg_raw.id,
        disable_notification=True,
    )
    await message.delete()


@commands.add("r", usage="<reply> [emoji]")
async def put_reaction(_: Client, message: Message, args: str) -> str | None:
    """Reacts to a message with a specified emoji or removes any reaction"""
    try:
        await message.reply_to_message.react(args)
    except ReactionInvalid:
        return args
    except ReactionEmpty:
        pass  # ignore
    await message.delete()


@commands.add("rs", usage="<reply>")
async def get_reactions(client: Client, message: Message, __: str) -> str:
    """Gets message reactions"""
    peer = await client.resolve_peer(message.chat.id)
    ids = [types.InputMessageID(id=message.reply_to_message.id)]
    if isinstance(peer, types.InputPeerChannel):
        messages: types.messages.Messages = await client.invoke(
            functions.messages.GetMessages(
                id=ids,
            )
        )
    else:
        messages: types.messages.Messages = await client.invoke(
            functions.channels.GetMessages(
                channel=peer,
                id=ids,
            )
        )
    t = ""
    if (
        not isinstance(messages.messages[0], types.MessageEmpty)
        and (reactions := messages.messages[0].reactions) is not None
    ):
        for r in reactions.results:
            t += f"<code>{r.reaction}</code>: {r.count}\n"
            for rr in reactions.recent_reactions or []:
                if rr.reaction == r.reaction:
                    peer = await client.get_chat(rr.peer_id.user_id)
                    peer_name = f"{peer.first_name or 'Deleted Account'} (#{peer.id})"
                    t += f"- <a href='tg://user?id={rr.peer_id.user_id}'>{peer_name}</a>\n"
    else:
        try:
            messages: types.messages.MessageReactionsList = await client.invoke(
                functions.messages.GetMessageReactionsList(
                    peer=peer,
                    id=message.reply_to_message.id,
                    limit=100,
                )
            )
        except MsgIdInvalid:
            return "⚠ Message not found, deleted or has no reactions"
        reactions = {}
        for r in messages.reactions:
            reactions.setdefault(r.reaction, set()).add(r.peer_id.user_id)
        for reaction, peers in reactions.items():
            t += f"<code>{reaction}</code>: {len(peers)}\n"
            for peer_id in peers:
                for user in messages.users:
                    if user.id == peer_id:
                        peer_name = f"{user.first_name or 'Deleted Account'} (#{user.id})"
                        break
                else:
                    peer_name = peer_id
                t += f"- <a href='tg://user?id={peer_id}'>{peer_name}</a>\n"
    return t


@commands.add("rr", usage="<reply>")
async def put_random_reaction(client: Client, message: Message, _: str) -> None:
    """Reacts to a message with a random emoji"""
    chat = await client.get_chat(message.chat.id)
    await message.reply_to_message.react(random.choice(chat.available_reactions))
    await message.delete()


@commands.add("cal", usage="<month> [year]")
async def calendar(_: Client, __: Message, args: str) -> str:
    """Sends a calendar for a specified month and year"""
    args_list = args.split()
    month = int(args_list[0])
    if len(args_list) == 2:
        year = int(args_list[1])
    else:
        year = datetime.utcnow().year
    return f"<code>{TextCalendar().formatmonth(year, month)}</code>"


@commands.add("togif", usage="[reply]", waiting_message="<i>Converting...</i>")
async def video_to_gif(client: Client, message: Message, __: str) -> str | None:
    """Converts a video to a mpeg4 gif"""
    msg = message.reply_to_message if message.reply_to_message else message
    video = msg.video
    if not video:
        return "⚠ No video found"
    with NamedTemporaryFile(suffix=".mp4") as src, NamedTemporaryFile(suffix=".mp4") as dst:
        await client.download_media(video.file_id, src.name)
        proc = await asyncio.subprocess.create_subprocess_exec(
            "/usr/bin/ffmpeg",
            "-hide_banner",
            "-i",
            src.name,
            "-c",
            "copy",
            "-an",
            "-movflags",
            "+faststart",
            "-y",
            dst.name,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(
                f"Process finished with error code {proc.returncode}\n{stderr.decode()}"
            )
        await msg.reply_animation(dst.name)
    if message.reply_to_message:
        await message.delete()


@commands.add("chatban", usage="<id> [time] [reason...]")
async def chat_ban(client: Client, message: Message, args: str) -> str:
    """Bans a user in a chat"""
    args_list = args.split(" ")
    user_id = int(args_list[0])
    if len(args_list) > 1:
        match = re.fullmatch(r"(\d+)([mhdwy])?", args_list[1], re.I)
        time_sec = int(match[1])
        match match[2]:
            case "m" | "M":
                time_sec *= 60
            case "h" | "H":
                time_sec *= 60 * 60
            case "d" | "D":
                time_sec *= 60 * 60 * 24
            case "w" | "W":
                time_sec *= 60 * 60 * 24 * 7
            case "y" | "Y":
                time_sec *= 60 * 60 * 24 * 365
        delta = timedelta(seconds=time_sec)
        time = datetime.now() + delta
    else:
        delta = None
        time = datetime.fromtimestamp(0)
    reason = " ".join(args_list[2:])
    await client.ban_chat_member(message.chat.id, user_id, time)
    user = await client.get_chat(user_id)
    t = f"<a href='tg://user?id={user_id}'>{user.first_name}</a> <b>banned</b> in this chat"
    if delta:
        t += f" for <i>{args_list[1]}</i>."
    if reason:
        t += f"\n<b>Reason:</b> {reason}"
    return t


@commands.add("testerror")
async def test_error(_: Client, __: Message, ___: str) -> None:
    """Always throws an error"""
    raise RuntimeError("Test error")


# endregion


# region shortcuts
@shortcuts.add(r"yt:([a-zA-Z0-9_\-]{11})")
async def youtube(match: re.Match[str]) -> str:
    """Sends a link to a YouTube video"""
    return f"https://youtu.be/{match[1]}"


@shortcuts.add(r"@(\d+)(?::(.+)@)?")
async def mention(match: re.Match[str]) -> str:
    """Mentions a user by ID"""
    return f"<a href='tg://user?id={match[1]}'>{match[2] or match[1]}</a>"


async def github(match: re.Match[str], *, client: AsyncClient) -> str:
    """Sends a link to a GitHub repository"""
    m = GitHubMatch(**match.groupdict())
    url = f"https://github.com/{m.username}"
    text = m.username
    if not m.repo:
        return f"<a href='{url}'>{text}</a>"
    if m.repo == "@":
        m.repo = m.username
    url += f"/{m.repo}"
    text += f"/{m.repo}"
    if not m.branch and m.path:
        m.branch = (await client.get(f"/repos/{m.username}/{m.repo}")).json()["default_branch"]
        url += f"/tree/{m.branch}/{m.path}"
        text += f":/{m.path}"
    elif m.branch:
        path = m.path or ""
        url += f"/tree/{m.branch}/{path}"
        if len(m.branch) == 40:  # Full commit hash
            text += f"@{m.branch[:7]}"
        else:
            text += f"@{m.branch}"
        if path:
            text += f":/{path}"
    elif m.issue:
        url += f"/issues/{m.issue}"
        text += f"#{m.issue}"
    if not m.path:
        return f"<a href='{url}'>{text}</a>"
    if m.line1:
        url += f"#L{m.line1}"
        text += f"#L{m.line1}"
        if m.line2:
            url += f"-L{m.line2}"
            text += f"-L{m.line2}"
    return f"<a href='{url}'>{text}</a>"


@shortcuts.add(r":uwu(\d+)?:")
async def uwu(match: re.Match[str]) -> str:
    if not match[1]:
        return "🥺👉👈"
    count = int(match[1])
    return "👉" * count + "👈" * count


# endregion


async def _main(client: Client, storage: Storage, github_client: AsyncClient) -> None:
    async with client, storage, github_client:
        await idle()


def main() -> None:
    for file in ("config.yaml", "/data/config.yaml", "/config.yaml"):
        try:
            with open(file) as f:
                config = yaml.safe_load(f)
        except FileNotFoundError:
            continue
        else:
            break
    else:
        raise FileNotFoundError("Config file not found!")
    data_dir = Path(config.get("data_location", "data")).resolve()
    if not data_dir.exists():
        data_dir.mkdir()
    if not data_dir.is_dir():
        raise NotADirectoryError("config.yaml: `data_location` must be a directory")
    client = Client(
        name=config["session"],
        api_id=config["api_id"],
        api_hash=config["api_hash"],
        app_version="evgfilim1/userbot 0.2.x",
        device_model="Linux",
        workdir=str(data_dir),
        **(config.get("kwargs") or {}),
    )
    storage = PickleStorage(data_dir / f"{config['session']}.pkl")
    github_client = AsyncClient(base_url="https://api.github.com/", http2=True)

    commands.add_handler(check_hooks, ["hookshere", "hooks_here"], kwargs={"storage": storage})
    shortcuts.add_handler(partial(github, client=github_client), GH_PATTERN)

    commands.register(client, with_help=True)
    hooks.register(client, storage)
    shortcuts.register(client)

    client.run(_main(client, storage, github_client))


if __name__ == "__main__":
    main()
