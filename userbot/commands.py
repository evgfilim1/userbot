# FIXME (2022-06-18): 550+ lines may become unreadable at some moment, refactor this ASAP.

import asyncio
import html
import random
import re
from calendar import TextCalendar
from datetime import datetime, time, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile

import d20
from PIL import Image
from pyrogram import Client
from pyrogram.enums import ChatType, ParseMode
from pyrogram.errors import (
    BadRequest,
    MessageNotModified,
    MsgIdInvalid,
    ReactionEmpty,
    ReactionInvalid,
)
from pyrogram.raw import functions, types
from pyrogram.types import Message, Sticker
from pyrogram.utils import get_channel_id

from .constants import LONGCAT, PACK_ALIASES
from .modules import CommandsModule
from .utils import (
    HTMLDiceStringifier,
    Unset,
    create_filled_pic,
    downloader,
    edit_or_reply,
    en2ru_tr,
    enru2ruen_tr,
    get_text,
    parse_delta,
    ru2en_tr,
)

commands = CommandsModule()


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
    unset = Unset()
    for attr in attrs:
        if attr:
            obj = getattr(obj, attr, unset)
    return f"<b>Attribute</b> <code>{args}</code>\n\n<pre>{html.escape(str(obj))}</pre>"


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
    if not isinstance(peer, types.InputPeerChannel):
        messages: types.messages.Messages = await client.invoke(
            functions.messages.GetMessages(
                id=ids,
            )
        )
    else:
        messages: types.messages.Messages = await client.invoke(
            functions.channels.GetMessages(
                channel=types.InputChannel(
                    channel_id=peer.channel_id,
                    access_hash=peer.access_hash,
                ),
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
            return "<i>Message not found or has no reactions</i>"
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
    return t or "<i>No reactions here</i>"


@commands.add("rr", usage="<reply>")
async def put_random_reaction(client: Client, message: Message, _: str) -> None:
    """Reacts to a message with a random emoji"""
    chat = await client.get_chat(message.chat.id)
    await message.reply_to_message.react(random.choice(chat.available_reactions))
    await message.delete()


@commands.add("cal", usage="[month] [year]")
async def calendar(_: Client, message: Message, args: str) -> str:
    """Sends a calendar for a specified month and year"""
    args_list = args.split()
    # It's more reliable to get current date/time from the message
    now = message.edit_date or message.date or datetime.now()
    if len(args_list) >= 1:
        month = int(args_list[0])
    else:
        month = now.month
    if len(args_list) == 2:
        year = int(args_list[1])
    else:
        year = now.year
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
    now = message.edit_date or message.date or datetime.now()
    if len(args_list) > 1:
        delta = parse_delta(args_list[1])
        t = now + delta
    else:
        delta = None
        t = datetime.fromtimestamp(0)
    reason = " ".join(args_list[2:])
    await client.ban_chat_member(message.chat.id, user_id, t)
    user = await client.get_chat(user_id)
    text = f"<a href='tg://user?id={user_id}'>{user.first_name}</a> <b>banned</b> in this chat"
    if delta:
        text += f" for <i>{args_list[1]}</i>."
    if reason:
        text += f"\n<b>Reason:</b> {reason}"
    return text


@commands.add("testerror")
async def test_error(_: Client, __: Message, ___: str) -> None:
    """Always throws an error"""
    raise RuntimeError("Test error")


async def download(client: Client, message: Message, args: str, *, data_dir: Path) -> str:
    """Downloads a file or files"""
    msg = message.reply_to_message if message.reply_to_message else message
    if msg.media_group_id:
        all_messages = await msg.get_media_group()
    else:
        all_messages = [msg]

    t = ""
    for m in all_messages:
        try:
            t += await downloader(client, m, args if len(all_messages) == 1 else "", data_dir)
        except Exception as e:
            t += f"⚠ <code>{type(e).__name__}: {e}</code>"
        finally:
            t += "\n"
    return t


@commands.add(
    "tosticker",
    usage="[reply] ['png'|'webp']",
    waiting_message="<i>Converting to sticker...</i>",
)
async def to_sticker(client: Client, message: Message, args: str) -> None:
    """Converts a photo to a sticker-ready png or webp"""
    msg = message.reply_to_message if message.reply_to_message else message
    output_io = await client.download_media(msg, in_memory=True)
    output_io.seek(0)
    im: Image.Image = Image.open(output_io)
    im.thumbnail((512, 512))
    output_io.seek(0)
    fmt = args.lower() if args else "png"
    if fmt not in ("png", "webp"):
        raise ValueError(f"Unsupported format: {fmt}")
    im.save(output_io, args or "png")
    output_io.seek(0)
    output_io.name = f"sticker.{fmt}"
    match fmt:
        case "png":
            await msg.reply_document(output_io, file_name="sticker.png")
        case "webp":
            await msg.reply_sticker(output_io)
        case _:
            raise AssertionError("Wrong format, this should never happen")
    if message.reply_to_message:
        await message.delete()


@commands.add("caps", usage="<reply>")
async def caps(_: Client, message: Message, __: str) -> None:
    """Toggles capslock on the message"""
    text = get_text(message.reply_to_message)
    answer, delete = edit_or_reply(message)
    try:
        await answer(text.swapcase())
    except MessageNotModified:
        pass
    if delete:
        await message.delete()


def _remind_common(message: Message, args_list: list[str]) -> datetime:
    """Common code for `remind` and `remind_me`"""
    now = message.edit_date or message.date or datetime.now()
    if (delta := parse_delta(args_list[0])) is not None:
        t = now + delta
    else:
        h, m = map(int, args_list[0].split(":", maxsplit=1))
        parsed_time = time(h, m)
        if parsed_time < now.time():
            t = datetime.combine(now + timedelta(days=1), parsed_time)
        else:
            t = datetime.combine(now, parsed_time)
    return t


@commands.add("remind", usage="[reply] <time> [message...]")
async def remind(client: Client, message: Message, args: str) -> str:
    """Sets a reminder"""
    args_list = args.split(" ")
    if len(args_list) >= 2:
        text = " ".join(args_list[1:])
    else:
        text = "⏰ <b>Reminder!</b>"
    t = _remind_common(message, args_list)
    await client.send_message(
        message.chat.id,
        text,
        parse_mode=ParseMode.HTML,
        reply_to_message_id=message.reply_to_message_id,
        schedule_date=t,
    )
    return f"⏰ Reminder was set for <i>{t.time()}</i>"


@commands.add("remindme", usage="[reply] <time> [message...]")
async def remind_me(client: Client, message: Message, args: str) -> str:
    """Sets a reminder for myself"""
    args_list = args.split(" ")
    if len(args_list) >= 2:
        text = " ".join(args_list[1:])
    else:
        text = "⏰ <b>Reminder!</b>"
    if message.reply_to_message_id is not None and message.chat.type == ChatType.SUPERGROUP:
        chat_id = get_channel_id(message.chat.id)
        text += f"\n\nhttps://t.me/c/{chat_id}/{message.reply_to_message_id}"
    t = _remind_common(message, args_list)
    await client.send_message(
        "me",
        text,
        parse_mode=ParseMode.HTML,
        schedule_date=t,
    )
    return f"⏰ Reminder was set for <i>{t.time()}</i>"
