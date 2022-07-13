import re

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
