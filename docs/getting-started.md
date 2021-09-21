
# Installation

Installation is done via pip and git:

```bash
# Windows
py -3 -m pip install git+https://github.com/blanketsucks/aiospotify.git

# Linux or MacOS
python3 -m pip install git+https://github.com/blanketsucks/aiospotify.git
```

# Basic Usage

```py
import asyncio
import aiospotify

client_id = 'your-client-id'
client_secret = 'your-client-secret'

async def main():
    client = aiospotify.SpotifyClient(client_id, client_secret, oauth2=False)

    async with client:
        result = await client.search(
            q='バイバイ YESTERDAY'
        )

        print(result.tracks)

asyncio.run(main())
```
