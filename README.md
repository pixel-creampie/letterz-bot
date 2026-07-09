
# Letterz Discord Bot
Letterz is a super shiny discord bot which allows you to send and receive letters inside servers.The letters can be sent in anonymous format depending on the choice of the sender.

## Features
* Send Private Letters to Users inside the server.
* Moderators can ban and unban users to use this bot from particular server.
* Optional Server Logging for moderation.
* Dynamic Bot Status
* Per Server opt out feature.

## `/letter`

Send a private letter to another member.

### Parameters

| Parameter | Description               |
| --------- | ------------------------- |
| recipient | User receiving the letter |
| anonymous | Yes / No                  |

Features:

* Anonymous option
* Non-anonymous option
* Prevents sending to bots
* Prevents sending to yourself
* Respects opt-out settings
* Respects guild bans
* Respects global bans

---

## `/no-letter`

Opt out (or back into) the letter system for the current server.

Options:

* **Yes** → Opt out
* **No** → Opt back in

Users who opt out:

* Cannot send letters
* Cannot receive letters

---

## `/letter-log`

Configure a logging channel.

Requires:

* Manage Server permission

The bot also requires:

* Send Messages
* Embed Links

Every letter sent will create an embed containing:

* Sender
* Recipient
* Anonymous status
* Letter contents
* Channel name
* Timestamp

---

## `/letter-log-remove`

Disables letter logging for the current server.

Requires:

* Manage Server permission

---

## `/ban-user`

Ban a user from using the bot in the current server.

Requires:

* Manage Server permission

If a user accumulates bans in **3 different servers**, they become **globally banned**.

---

## `/unban-user`

Remove a user's server-specific ban.

Requires:

* Manage Server permission

Users that are globally banned cannot be unbanned with this command.

---

# How It Works

1. User runs `/letter`
2. Selects a recipient.
3. Chooses anonymous or not.
4. A modal opens for writing the letter.
5. The bot posts a notification with an **Open Letter** button.
6. Only the selected recipient can press the button.
7. The letter is shown as an ephemeral embed.
8. The button changes to **Opened**.

---

# Logging System

Confezzion supports two logging systems.

## Server Logging

Each server can configure its own log channel using:

```
/letter-log
```

Every sent letter is logged as an embed.

---

## Global Hub Logging

The bot can also log activity into a dedicated "hub" server.

When joining a new server, the bot automatically:

* Creates a text channel named after the server
* Posts server information
* Sends future letter logs to that channel

This is configured using environment variables.

---

# Data Storage

The bot stores data locally using JSON files.

| File                     | Purpose                          |
| ------------------------ | -------------------------------- |
| `letter_log_config.json` | Server log channel configuration |
| `optout-user-guild.json` | Users opted out per guild        |
| `banned-user-guild.json` | Guild-specific bans              |
| `banned-globally.json`   | Global ban list                  |

---

## Variables

| Variable      | Description                                       |
| ------------- | ------------------------------------------------- |
| `TOKEN`       | Discord Bot Token                                 |
| `Main_Guild`  | Central logging server ID                         |
| `Server_Logs` | Category ID where new server channels are created |


---

# Required Bot Intents

Enable the following intents in the Discord Developer Portal:

* Server Members Intent
* Message Content Intent

The bot also uses:

* Guilds
* Members
* Message Content

---

# Required Permissions

Recommended permissions:

* Send Messages
* Read Messages/View Channels
* Embed Links
* Use Slash Commands
* Read Message History

---

# Project Structure

```
.
├── bot.py
├── .env
├── letter_log_config.json
├── banned-user-guild.json
├── banned-globally.json
├── optout-user-guild.json
└── README.md
```
---


