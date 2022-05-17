# userbot

[![wakatime](https://wakatime.com/badge/github/evgfilim1/userbot.svg)](https://wakatime.com/badge/github/evgfilim1/userbot)

The userbot I use with some specific features written in Pyrogram.

## Features

### Commands

Commands work only when sent by the user who runs userbot. Command prefix is `.`.

```
List of commands available:

longcat — Sends random longcat
delete|delet|del <reply> — Deletes replied message
dump [dot-separated-attrs] — Dumps entire message or its specified attribute
id <reply> — Sends replied user's ID as link
roll|dice <dice-spec> — Rolls dice according to d20.roll syntax
promote <admin-title> — Promotes a user to an admin without any rights but with title
calc <python-expr> — Evaluates Python expression
rnds <pack-link|pack-alias> — Sends random sticker from specified pack
tr <reply> ['en'|'ru'] — Swaps keyboard layout from en to ru or vice versa
s <reply> <find-re>/<replace-re>/[flags] — sed-like replacement
color <color-spec> — Sends a specified color sample
usercolor <reply> — Sends a color sample of user's color as shown in clients
userfirstmsg [reply] — Replies to user's very first message in the chat
r <reply> [emoji] — Reacts to a message with a specified emoji or removes any reaction
rs <reply> — Gets message reactions
rr <reply> — Reacts to a message with a random emoji
cal <month> [year] — Sends a calendar for a specified month and year
togif [reply] — Converts a video to a mpeg4 gif
chatban <id> [time] [reason...] — Bans a user in a chat
download|dl [reply] [filename] — Downloads a file or files
help — Sends this message
```

### Hooks (triggers)

Triggers can be enabled by `.<hookname>here` and disabled by `.no<hookname>here`. They are disabled
everywhere by default. To check if a hook is enabled or disabled, use `.hookshere`.

- `duck`: Sends a duck emoji (🦆) when someone writes "дак" (pronounced as "duck") or "кря"
  (pronounces as "krya", English equivalent is "quack")
- `tap`: Sends a sticker with a finger touching a seal when someone writes "тык" or sends that
  sticker itself
- `mibib`: Sends a sticker (with 20% chance) with an animated pixelated bear when someone sends that
  sticker itself

### Shortcuts

Shortcuts work only when sent by the user who runs userbot.

- `yt:<id>` — Sends a YouTube video with the specified ID
- `@<id>` — Mentions a user with the specified ID
  - `@<id>:Some name@` — Mentions a user with the specified ID with a custom name
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

## Installation and running

1. Copy the following to `config.yaml` and modify for yourself:
    ```yaml
    session: evgfilim1 # Name for session file
    api_id: ""  # Insert your Telegram api_id here
    api_hash: ""  # Insert your Telegram api_hash here 
    kwargs:  # Optional, will be passed directly to `pyrogram.Client`, see docs for more info
      phone_number: "+1234567890"
      # ...
    data_location: /data  # Data location
    ```
2. Make sure docker is installed, then run `docker-compose build`.
3. Go through interactive authentication (needed only once as `/data` is mounted as docker volume)
  by running `docker-compose run --rm main python -m userbot`.
4. Stop the script by pressing <kbd>Ctrl</kbd>+<kbd>C</kbd> as soon as you see `Bot started` message
  in console.
5. Run `docker-compose up -d` to run the userbot in the background.
