# aiospotify

An async wrapper for the spotify web API.

# Installation

Installation is done via pip and git:

```bash
# Windows
py -3 -m pip install git+https://github.com/blanketsucks/aiospotify.git

# Linux or MacOS
python3 -m pip install git+https://github.com/blanketsucks/aiospotify.git
```

# Building documentation

Since documentation is not hosted anywhere and i don't plan on doing so, you'll have to host it yourself (if you want to of course).

```bash
pip install mkdocstrings
git clone https://github.com/blanketsucks/aiospotify
cd aiospotify
mkdocs serve
```

# Basic Usage

```py
import asyncio
import aiospotify

client_id = 'your-client-id'
client_secret = 'your-client-secret'

async def main():
    client = aiospotify.SpotifyClient(client_id, client_secret)

    async with client:
        result = await client.search(query='バイバイ YESTERDAY')
        print(result.tracks)

asyncio.run(main())
```
