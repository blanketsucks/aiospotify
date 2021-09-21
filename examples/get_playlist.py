import aiospotify
import asyncio

client_id = 'your-client-id'
client_secret = 'your-client-secret'
playlist_url = 'https://open.spotify.com/playlist/1OCUhdY1ePwqKdkHzIuUxr?si=29364f5d0c834174'
# as mentioned in the get_track.py example, this can be either a URI or just an ID

async def main():
    client = aiospotify.SpotifyClient(client_id, client_secret, oauth2=False)

    async with client:
        playlist = await client.fetch_playlist(
            uri=playlist_url
        )

        print(playlist)

        # cases in which you're going to use the Paginator class is when you don't want
        # to have to bother with all the offset stuff and worrying about extra stuff.
        # the Paginator supports being iterated through and also getting all items at once.
        # in this case of the playlist above, it over 130 tracks.
        # now, why are we using `read` instead of just using `tracks`? it's because
        # `tracks` doesn't give all the playlist's tracks, while `read` is an API call to an
        # endpoint that supports pagination.

        paginator = aiospotify.Paginator(
            callback=playlist.read
        )

        tracks = await paginator.all() 
        print(tracks)

        # or alternatively

        tracks = await aiospotify.Paginator(
            callback=playlist.read
        )

        print(tracks)

        # OR

        paginator = aiospotify.Paginator(
            callback=playlist.read
        )

        tracks = []
        async for items in paginator:
            tracks.extend(items)

        print(tracks)

asyncio.run(main())