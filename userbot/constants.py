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
    SPEECH_TO_TEXT = (5974441981391145918, "🗣")
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
    # https://t.me/addemoji/dev_emojis_solid
    EDITOR_ANDROID_STUDIO = (5301067044400146520, "👩‍💻")
    EDITOR_CLION = (5300950543412241242, "👩‍💻")
    EDITOR_DATAGRIP = (5301009899860272439, "👩‍💻")
    EDITOR_EMACS = (5355053194172965841, "👩‍💻")
    EDITOR_IDEA = (5300959605793235101, "👩‍💻")
    EDITOR_GOLAND = (5301072614972727404, "👩‍💻")
    EDITOR_NEOVIM = (5300989606139797864, "👩‍💻")
    EDITOR_NPP = (5300844878626824738, "👩‍💻")
    EDITOR_PHPSTORM = (5301168530182383496, "👩‍💻")
    EDITOR_PYCHARM = (5300905068298509813, "👩‍💻")
    EDITOR_RIDER = (5301187986384233017, "👩‍💻")
    EDITOR_RUBYMINE = (5300761835434157641, "👩‍💻")
    EDITOR_SUBLIME = (5300967525712929829, "👩‍💻")
    EDITOR_VIM = (5300761723765007779, "👩‍💻")
    EDITOR_VS = (5301087466969637386, "👩‍💻")
    EDITOR_VSCODE = (5301201579955725162, "👩‍💻")
    EDITOR_WEBSTORM = (5301054236807667881, "👩‍💻")
    EDITOR_XCODE = (5301295626854606173, "👩‍💻")
    LANG_BASH = (5300744500946148517, "👩‍💻")
    LANG_C = (5301241853864059003, "👩‍💻")
    LANG_CPP = (5301090211453739345, "👩‍💻")
    LANG_CSHARP = (5301164462848352743, "👩‍💻")
    LANG_CSS = (5301277643826536470, "👩‍💻")
    LANG_DART = (5301142081773772964, "👩‍💻")
    LANG_DOCKER = (5301137237050663843, "👩‍💻")
    LANG_GIT = (5301184838173204859, "👩‍💻")
    LANG_GO = (5300888829027165969, "👩‍💻")
    LANG_HTML = (5301117377121887562, "👩‍💻")
    LANG_HTTP = (5301002546876259463, "👩‍💻")
    LANG_JAVA = (5301179216061015693, "👩‍💻")
    LANG_JS = (5300896259320586992, "👩‍💻")
    LANG_KOTLIN = (5300983790754078428, "👩‍💻")
    LANG_LUA = (5300895632255361378, "👩‍💻")
    LANG_MARKDOWN = (5301281492117233700, "👩‍💻")
    LANG_NGINX = (5301053291914863195, "👩‍💻")
    LANG_NODEJS = (5301104616774050249, "👩‍💻")
    LANG_OBJECTIVE_C = (5300877967054873746, "👩‍💻")
    LANG_PHP = (5303045701473671851, "👩‍💻")
    LANG_PYTHON = (5300928913956938544, "👩‍💻")
    LANG_REACT = (5301232280381956336, "👩‍💻")
    LANG_RUBY = (5303402295428390127, "👩‍💻")
    LANG_RUST = (5301209568594894358, "👩‍💻")
    LANG_SASS = (5301021930063668426, "👩‍💻")
    LANG_SHELL = (5301233981189005137, "👩‍💻")
    LANG_VUE = (5300879633502184552, "👩‍💻")
    LANG_TYPESCRIPT = (5301254000031572585, "👩‍💻")
    OS_APPLE = (5301155675345265040, "👩‍💻")
    OS_LINUX = (5300957668762987048, "👩‍💻")
    OS_WINDOWS = (5366318141771096216, "👩‍💻")

    def __str__(self) -> str:
        custom_emoji_id, emoji = self.value[:2]
        return f"<emoji id={custom_emoji_id}>{emoji}</emoji>"
