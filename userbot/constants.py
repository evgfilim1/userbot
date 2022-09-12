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
    TRASH = (6050677771154231040, "🗑")
    INFO = (6050744746874244036, "ℹ")
    CROSS = (6041914500272098262, "🚫")
    STOP = (5798760304108113223, "🚫")
    PERSON_BLOCK = (6037623961087380601, "🚫")
    PERSON_TICK = (5801094618833489205, "✅")
    PICTURE = (6048727692793089927, "🖼")
    PENCIL = (6039884277821213379, "✏")
    COLOR = (6048474766463996499, "🎨")
    BOOKMARK = (6041768050477239766, "⭐")
    WARNING = (6037615384037690578, "❗")
    QUESTION = (6037389971269094179, "❓")
    DOWNLOAD = (6050713964843633615, "⬇")
    WATCH = (5798396069406576367, "🕒")
    NOTIFICATION = (6039513858366773821, "🔔")
    # https://t.me/addemoji/uxtools
    GITHUB = (6318902906900711458, "🌐")
    # https://t.me/addemoji/MaterialIconsAlpha
    GIT = (5469770984670108755, "💩")

    def get_icon(self, is_premium: bool) -> str:
        if is_premium:
            return self.premium_icon
        return self.icon

    @property
    def premium_icon(self) -> str:
        custom_emoji_id, emoji = self.value[:2]
        return f"<emoji id={custom_emoji_id}>{emoji}</emoji>"

    @property
    def icon(self) -> str:
        return self.value[1]
