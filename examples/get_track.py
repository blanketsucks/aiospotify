import aiospotify
import asyncio

client_id = 'your-client-id'
client_secret = 'your-client-secret'
track_url = 'https://open.spotify.com/track/2sWdQfVWACeiCfE0rK6Gf7?si=016bd00e7bfd4a4b'
# the track_url can be also be a URI or just a plain ID
# the format for URIs is: 'spotify:<type>:<id>'

async def main():
    client = aiospotify.SpotifyClient(client_id, client_secret, oauth2=False)

    # context manager so it automatically closes the client
    async with client:
        track = await client.fetch_track(
            uri=track_url
        )

        print(track)

asyncio.run(main())