# temporary

Post something interesting to your Discord server using a webhook.

## Setup
1. Create a Discord webhook in your server settings.
2. Export the webhook URL:

```bash
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
```

## Usage
Post a random fun fact (the script will prompt for webhook/message):

```bash
python3 discord_post.py
```

Post your own message:

```bash
python3 discord_post.py --message "Here is something cool from Python!"
```

Provide the webhook URL inline instead of env var:

```bash
python3 discord_post.py --webhook "https://discord.com/api/webhooks/..." --message "Hello Discord!"
```

Attach a file:

```bash
python3 discord_post.py --attachment "/path/to/file.png"
```
