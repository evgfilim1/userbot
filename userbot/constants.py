__all__ = [
    "BRA_MEME_PICTURE",
    "GH_PATTERN",
    "Icons",
    "LONGCAT",
    "MIBIB_FLT",
    "MIBIB_STICKER",
    "PACK_ALIASES",
    "TAP_FLT",
    "TAP_STICKER",
    "UWU_MEME_PICTURE",
]

import re
from enum import Enum

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
# https://www.reddit.com/r/anime_irl/comments/u4zxol/anime_irl/
BRA_MEME_PICTURE = "https://i.redd.it/4sm31aa1rwt81.jpg"
# https://imgur.com/a/bDzntL5
UWU_MEME_PICTURE = "https://i.imgur.com/VsuT9ry.jpeg"
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


class Icons(Enum):
    # https://t.me/addemoji/IconsInTg
    ARCHIVED_CHAT = (6039701346574142584, "📥")
    ARCHIVED_STICKER = (6039606071314615141, "🕒")
    BOOKMARK = (6041768050477239766, "⭐")
    BOT = (5971808079811972376, "🤖")
    CHANNEL_CHAT = (5764623873974734153, "📢")
    COLOR = (6048474766463996499, "🎨")
    COMMAND = (5974226571601382719, "🔨")
    CROSS = (6041914500272098262, "🚫")
    DIAGRAM = (5974083454701145202, "📊")
    DOWNLOAD = (6050713964843633615, "⬇")
    EMOJI = (5971928678198676594, "🙂")
    GIF = (6048825205730577727, "🎞")
    GLOBE = (6037284117505116849, "🌐")
    GROUP_CHAT = (6037355667365300960, "👥")
    INFO = (6050744746874244036, "ℹ")
    LOCK = (6003424016977628379, "🔒")
    MESSAGE = (6041858261970324774, "💬")
    NOTIFICATION = (6039513858366773821, "🔔")
    PENCIL = (6039884277821213379, "✏")
    PERSON_BLOCK = (6037623961087380601, "🚫")
    PERSON_TICK = (5801094618833489205, "✅")
    PICTURE = (6048727692793089927, "🖼")
    PIN = (5974352611711651172, "📌")
    PREMIUM = (5782804629452492061, "⭐")
    PRIVATE_CHAT = (6037122016849432064, "👤")
    SETTINGS = (6039769000898988691, "⚙")
    STICKER = (6037128751358151991, "📑")
    STOP = (5798760304108113223, "🚫")
    TRASH = (6050677771154231040, "🗑")
    WATCH = (5798396069406576367, "🕒")
    WARNING = (6037615384037690578, "❗")
    QUESTION = (5974229895906069525, "❓")
    # https://t.me/addemoji/uxtools
    GITHUB = (6318902906900711458, "🌐")
    # https://t.me/addemoji/MaterialIconsAlpha
    GIT = (5469770984670108755, "💩")

    def __str__(self) -> str:
        custom_emoji_id, emoji = self.value[:2]
        return f"<emoji id={custom_emoji_id}>{emoji}</emoji>"
