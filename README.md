# userbot

<!-- region Some nice badges because I love them ^^ -->
[![wakatime](https://wakatime.com/badge/github/evgfilim1/userbot.svg)](https://wakatime.com/badge/github/evgfilim1/userbot)
[![Crowdin](https://badges.crowdin.net/evgfilim1-userbot/localized.svg)](https://crowdin.com/project/evgfilim1-userbot)

[![Commit activity](https://img.shields.io/github/commit-activity/m/evgfilim1/userbot)](https://github.com/evgfilim1/userbot/commits/)
[![Latest commit](https://img.shields.io/github/last-commit/evgfilim1/userbot/master)](https://github.com/evgfilim1/userbot/commits/)
[![Total LoC](https://img.shields.io/tokei/lines/github/evgfilim1/userbot)](https://github.com/evgfilim1/userbot)
[![Code size](https://img.shields.io/github/languages/code-size/evgfilim1/userbot)](https://github.com/evgfilim1/userbot)
[![License](https://img.shields.io/github/license/evgfilim1/userbot)](LICENSE)
[![Python version](https://img.shields.io/badge/python-3.11-yellow.svg?logo=python&logoColor=yellow&labelColor=blue)](https://github.com/python/cpython)
[![black code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

[![Build status](https://github.com/evgfilim1/userbot/actions/workflows/build.yaml/badge.svg)](https://github.com/evgfilim1/userbot/actions/workflows/build.yaml)
[![Code quality check](https://github.com/evgfilim1/userbot/actions/workflows/lint.yaml/badge.svg)](https://github.com/evgfilim1/userbot/actions/workflows/lint.yaml)
[![Deployment status](https://github.com/evgfilim1/userbot/actions/workflows/deploy.yaml/badge.svg)](https://github.com/evgfilim1/userbot/actions/workflows/deploy.yaml)
<!-- endregion -->

The userbot I use with some specific features written in Pyrogram.

## Features

### Commands

Commands work only when sent by the user who runs userbot. Default command prefix is `,` unless
overriden in config.

<details>
<summary>Click to expand full command list</summary>

```
List of userbot commands available:

About:
• about — Shows information about this userbot.
• help [command] — Sends help for all commands or for a specific one.
• stats ['bot'|'short'|'full'] — Shows some statistics about this userbot.

Chat administration:
• chatban|chatrestrict <'reply'|user_id|username|user_group> ['0'|'forever'|timespec] ['*'|perms] [reason...] — Restricts or bans a user in a chat.
• chatcleardel — Kicks Deleted Accounts from the chat.
• chatinvite <user_id|username|user_group> — Invites users to the current chat.
• chatunban <'reply'|user_id|username|user_group> — Unbans a user in a chat.
• <in reply> no_react2ban|noreact2ban — Stops react2ban on the message.
• <in reply> pin ['silent'] — Pins the message.
• <in reply> promote <admin_title...> — Promotes a user to an admin without any rights but with title.
• react2ban — Bans a user whoever reacted to the message.
• <in reply> s_pin ['silent'] — Pins the message silently (without returning the result).

Chat info:
• rndinfo ['photo'|'title'] — Sets random chat photo and/or title.
• rndmsg — Sends a random message from the chat.

Colors:
• color <color_spec> — Sends a specified color sample.
• usercolor [user_id|username|user_group] — Sends a color sample of user's color as shown in clients.

Content converters:
• toaudio — Extracts audio from video.
• togif — Converts a video to a mpeg4 gif.
• tosticker ['png'|'webp'] — Converts a photo to a sticker-ready png or webp.

Dice:
• roll|dice <dice_spec> — Rolls dice according to `d20.roll` syntax.

Download:
• download|dl ['single'|'all'] [filename]... — Downloads a file or files.

Hooks:
• hooklist|hook_list — Lists all available hooks.
• hookshere|hooks_here — Lists enabled hooks in the chat.

Language:
• lang [language_code] — Gets or changes the language of the bot for the current chat.

Messages:
• <in reply> copyhere|cphere|cph — Copies replied message to current chat.
• <in reply> delete|delet|del — Deletes replied message for everyone.
• dump [jq_query...] — Dumps entire message or its attribute specified with `jq` syntax.
• userfirstmsg — Looks for the user's very first message in the chat.

Notes:
• get|note|n <key...> — Sends saved note.
• note_del|ndel <key...> — Deletes saved note.
• notes|ns — Shows all saved notes.
• <in reply> save|note_add|nadd <key...> — Saves replied message as note for later use.

Reactions:
• <in reply> r [emoji] — Reacts to a message with a specified emoji or removes any reaction.
• <in reply> rr — Reacts to a message with a random available emoji.
• <in reply> rs — Gets message reactions with users who reacted to it.

Reminders:
• remind <time> [message...] — Sets a reminder in the chat.
• remindme <time> [message...] — Sets a reminder for myself.
• sremind <time> [message...] — Sets a silent reminder in the chat (no confirmation about scheduled message).
• sremindme <time> [message...] — Sets a silent reminder for myself (no confirmation about scheduled message).

Stickers:
• longcat — Sends random longcat.
• rnds <pack_shortlink|pack_alias|emoji> — Sends random sticker from specified pack or one matching specified emoji.

Text converters:
• <in reply> caps — Toggles capslock on the message.
• <in reply> s <args...> — sed-like replacement.
• <in reply> tr ['en'|'ru'] — Swaps keyboard layout from en to ru or vice versa.

Tools:
• cal [month] [year] — Sends a calendar for a specified month and year.
• calc|eval <python_expr...> — Evaluates Python expression.
• exec <python_code...> — Executes Python code.
• <in reply> id — Sends replied user's ID as link.

User groups:
• usergroupadd|ugadd <group_name> [user_id|username|user_group]... — Adds a user to the user group for later use with user resolving.
• usergroupdel|ugdel <group_name> [user_id|username|user_group]... — Removes a user from the user group.
• usergrouplist|uglist <group_name> ['resolve'] — Lists the users in the user group.
• usergroups|ugs — Lists all user groups.

Wakatime:
• wakatime|waka — Gets your Wakatime stats for today and the last 7 days.
```

</details>

### Hooks (triggers)

Triggers can be enabled by `.<hookname>here` and disabled by `.no<hookname>here`. They are disabled
everywhere by default. To check if a hook is enabled or disabled, use `.hookshere`.

- `emojis`:
  - Sends a duck emoji (🦆) when someone writes "дак" (pronounced as "duck") or "кря"
    (pronounces as "krya", English equivalent is "quack")
  - Sends a pancake emoji (🥞) when someone writes "блин" (English equivalent is "pancake", also
    that's how Russian equivalent to the English "f*ck" may be "censored")
- `tap`: Sends a sticker with a finger touching a seal when someone writes "тык" or sends that
  sticker itself ([link to the pack](https://t.me/addstickers/belek_vk))
- `mibib`: Sends a sticker (with 20% chance) with an animated pixelated bear when someone sends that
  sticker itself ([link to the pack](https://t.me/addstickers/bttv_hlam))
- `bra`: Sends a picture from [this](https://www.reddit.com/r/anime_irl/comments/u4zxol/anime_irl/)
  Reddit post when someone sends "бра" or "bra"
- `uwu`: Sends a [picture](https://imgur.com/a/bDzntL5) when someone sends "uwu", "owo", "уву"
  or "ово"

### Shortcuts

Shortcuts work only when sent by the user who runs userbot.

<details>
<summary>Click to expand full shortcut list</summary>

- `yt:<id>` — Sends a YouTube video with the specified ID
- `@:<id>` — Mentions a user with the specified ID
  - `@:<id>:<name>@` — Mentions a user with the specified ID with a custom name
- `github:<username>` or `gh:<username>` — Sends a GitHub link to the specified user's profile
  - `github:<username>/<repo>` — ... to the specified repo, `<repo>` can be "`@`" which means "same
    as `<username>`"
  - `github:<username>/<repo>:/<path>` — ... to the specified path on the default branch
  - `github:<username>/<repo>:/<path>#<line1>` — ... to the specified line in file
  - `github:<username>/<repo>:/<path>#<line1>-<line2>` — ... to the specified lines in file
  - `github:<username>/<repo>@<branch-or-commit>` — ... to the specified branch or commit of the repo
  - `github:<username>/<repo>@<branch-or-commit>:/<path>` — ... to the specified path on the branch or commit
  - `github:<username>/<repo>@<branch-or-commit>:/<path>#<line1>` — ... to the specified line in file
  - `github:<username>/<repo>@<branch-or-commit>:/<path>#<line1>-<line2>` — ... to the specified lines in file
  - `github:<username>/<repo>#<issue-or-pr>` — ... to the specified issue or pull request
- `:uwu:` — Sends a `🥺👉👈` emoji
  - `:uwu<number>:` — Sends a `👉👈` emoji with the specified number of finger pairs
- `google://<query>/` — Sends a link to a Google search for the specified query
- `:shrug:` — Sends a shrug kaomoji `¯\_(ツ)_/¯`
- `n://<key>/` — Sends a saved note with the specified key
- `xkcd:<number>` — Sends a link to XKCD comic with the specified number
- `pypi://<package>/` or `pip://<package>/` — Sends a link to PyPI page of the specified package
- `tg:<username>/<message-id>` or `tg:<username>#<message-id>` — Sends a link to the specified
  message in the specified chat

</details>

## Installation and running

1. Copy [`.env.example`](.env.example) file to `.env` and modify for yourself.
2. Make sure docker is installed, then run `docker-compose build`.
3. Go through interactive authentication (needed only once as `/data` is mounted as docker volume)
  by running `docker-compose run --rm main python -m userbot`.
4. Stop the script by pressing <kbd>Ctrl</kbd>+<kbd>C</kbd> as soon as you see `Bot started` message
  in console.
5. Run `docker-compose up -d` to run the userbot in the background.
6. To run migrations, run
   `docker-compose run --rm --entrypoint /usr/bin/env main python3.11 -m userbot.migrations`.
   Userbot must be stopped before running any migrations to prevent conflicts.

## Contributing

_TODO_
