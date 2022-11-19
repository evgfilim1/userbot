# userbot

[![wakatime](https://wakatime.com/badge/github/evgfilim1/userbot.svg)](https://wakatime.com/badge/github/evgfilim1/userbot)
[![Crowdin](https://badges.crowdin.net/evgfilim1-userbot/localized.svg)](https://crowdin.com/project/evgfilim1-userbot)
[![black code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[![build status](https://github.com/evgfilim1/userbot/actions/workflows/build.yaml/badge.svg)](https://github.com/evgfilim1/userbot/actions/workflows/build.yaml)
[![code quality](https://github.com/evgfilim1/userbot/actions/workflows/lint.yaml/badge.svg)](https://github.com/evgfilim1/userbot/actions/workflows/lint.yaml)
[![deployment status](https://github.com/evgfilim1/userbot/actions/workflows/deploy.yaml/badge.svg)](https://github.com/evgfilim1/userbot/actions/workflows/deploy.yaml)

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
• about — Shows information about this userbot
• help [command] — Sends help for all commands or for a specific one

Chat administration:
• chatban|chatrestrict <reply 'reply'|id> [timespec] [perms] [reason...] — Restricts or bans a user in a chat
• chatunban <reply 'reply'|id> — Unbans a user in a chat
• no_react2ban|noreact2ban <reply> — Stops react2ban on the message
• pin <reply> ['silent'] — Pins the message
• promote <admin-title> — Promotes a user to an admin without any rights but with title
• react2ban — Bans a user whoever reacted to the message
• s_pin <reply> ['silent'] — Pins the message silently (without returning the result)

Chat info:
• rndinfo ['photo'|'title'] — Sets random chat photo and/or title
• rndmsg — Sends a random message from the chat

Colors:
• color <color-spec> — Sends a specified color sample
• usercolor <reply|id> — Sends a color sample of user's color as shown in clients

Content converters:
• toaudio [reply] — Extracts audio from video
• togif [reply] — Converts a video to a mpeg4 gif
• tosticker [reply] ['png'|'webp'] — Converts a photo to a sticker-ready png or webp

Dice:
• roll|dice <dice-spec> — Rolls dice according to d20.roll syntax

Download:
• download|dl [reply] [filename] — Downloads a file or files

Hooks:
• hooklist|hook_list — List all available hooks
• hookshere|hooks_here — List enabled hooks in the chat

Language:
• lang [language-code] — Get or change the language of the bot for the current chat

Messages:
• copyhere|cphere|cph <reply> — Copies replied message to current chat
• delete|delet|del <reply> — Deletes replied message for everyone
• dump [jq-query] — Dumps entire message or its attribute specified with jq syntax
• userfirstmsg [reply] — Replies to user's very first message in the chat

Notes:
• get|note|n <name> — Sends saved note
• note_del|ndel <name> — Deletes saved note
• notes|ns — Shows all saved notes
• save|note_add|nadd <reply> <name> — Saves replied message as note for later use

Reactions:
• r <reply> [emoji] — Reacts to a message with a specified emoji or removes any reaction
• rr <reply> — Reacts to a message with a random available emoji
• rs <reply> — Gets message reactions with users who reacted to it

Reminders:
• remind [reply] <time> [message...] — Sets a reminder in the chat
• remindme [reply] <time> [message...] — Sets a reminder for myself
• sremind [reply] <time> [message...] — Sets a silent reminder in the chat (no confirmation about scheduled message)
• sremindme [reply] <time> [message...] — Sets a silent reminder for myself (no confirmation about scheduled message)

Stickers:
• longcat — Sends random longcat
• rnds <pack-shortlink|pack-alias|emoji> — Sends random sticker from specified pack or one matching specified emoji

Text converters:
• caps <reply> — Toggles capslock on the message
• s <reply> <find-re>/<replace-re>/[flags] — sed-like replacement
• tr <reply> ['en'|'ru'] — Swaps keyboard layout from en to ru or vice versa

Tools:
• cal [month] [year] — Sends a calendar for a specified month and year
• calc|eval <python-expr> — Evaluates Python expression
• exec <python-expr> — Executes Python expression
• id <reply> — Sends replied user's ID as link
```

</details>

### Hooks (triggers)

Triggers can be enabled by `.<hookname>here` and disabled by `.no<hookname>here`. They are disabled
everywhere by default. To check if a hook is enabled or disabled, use `.hookshere`.

- `emojis`:
  - Sends a duck emoji (🦆) when someone writes "дак" (pronounced as "duck") or "кря"
    (pronounces as "krya", English equivalent is "quack")
  - Sends a pancake emoji (🥞) when someone writes "блин" (English equivalent is "pancake", also
    that's how Russian equivalent to the English "f*ck" is "censored")
- `tap`: Sends a sticker with a finger touching a seal when someone writes "тык" or sends that
  sticker itself
- `mibib`: Sends a sticker (with 20% chance) with an animated pixelated bear when someone sends that
  sticker itself
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
