from typing import Dict, Any, List, Optional, Union

from .http import HTTPClient
from .enums import DeviceType, ObjectType, RepeatState, ShuffleState, CurrentPlayingType
from .objects import ExternalURLs
from .partials import PartialTrack, PartialEpisode

__all__ = (
    'Device',
    'PlaybackContext',
    'PlaybackActions',
    'UserPlayback'
)

class Device:
    def __init__(self, data: Dict[str, Any]) -> None:
        self.id: str = data['id']
        self.name: str = data['name']
        self.type: DeviceType = DeviceType(data['type'])
        self.volume: int = data['volume_percent']

        self.is_active: bool = data['is_active']
        self.is_private_session: bool = data['is_private_session']
        self.is_restricted: bool = data['is_restricted']

    def __repr__(self) -> str:
        return f'<Device id={self.id!r} name={self.name!r} type={self.type!r} volume={self.volume!r}>'

class PlaybackContext:
    def __init__(self, data: Dict[str, Any]):
        self.type = ObjectType(data['type'])
        self.uri: str = data['uri']
        self.href: str = data['href']

        self.external_urls = ExternalURLs(data['external_urls'])

    def __repr__(self) -> str:
        return f'<PlaybackContext type={self.type!r} uri={self.uri!r}>'

class PlaybackActions:
    def __init__(self, data: Dict[str, Any]):
        self.interrupting_playback: Optional[bool] = data.get('interrupting_playback')
        self.pausing: Optional[bool] = data.get('pausing')
        self.resuming: Optional[bool] = data.get('resuming')
        self.seeking: Optional[bool] = data.get('seeking')
        self.skipping_next: Optional[bool] = data.get('skipping_next')
        self.skipping_prev: Optional[bool] = data.get('skipping_prev')
        self.toggling_repeat_context: Optional[bool] = data.get('toggling_repeat_context')
        self.toggling_shuffle: Optional[bool] = data.get('toggling_shuffle')
        self.toggling_repeat_track: Optional[bool] = data.get('toggling_repeat_track')
        self.transferring_playback: Optional[bool] = data.get('transferring_playback')

class UserPlayback:
    def __init__(self, data: Dict[str, Any], http: HTTPClient) -> None:
        self._data = data
        self._http = http

        self.repeat = RepeatState(data['repeat_state'])
        self.shuffle = ShuffleState(data['shuffle_state'])
        self.timestamp: int = data['timestamp']
        self.progress_ms: Optional[int] = data['progress_ms']
        self.is_playing: bool = data['is_playing']
        self.currently_playing_type = CurrentPlayingType(data['currently_playing_type'])

    @property
    def actions(self) -> PlaybackActions:
        return PlaybackActions(self._data['actions'])

    @property
    def context(self) -> Optional[PlaybackContext]:
        context = self._data.get('context')
        return PlaybackContext(context) if context else None

    @property
    def device(self) -> Device:
        return Device(self._data['device'])

    async def fetch_devices(self) -> List[Device]:
        data = await self._http.get_user_devices()
        return [Device(device) for device in data['devices']]

    async def skip(self, *, next: bool = True, device: Optional[Device] = None) -> None:
        device_id = device.id if device else None
        await self._http.skip_user_playback(next=next, device_id=device_id)

    async def seek(self, position_ms: int, *, device: Optional[Device] = None) -> None:
        device_id = device.id if device else None
        await self._http.seek_to_position_in_currently_playing_track(
            position_ms=position_ms, device_id=device_id
        )

    async def set_repeat(self, state: RepeatState, *, device: Optional[Device] = None) -> None:
        device_id = device.id if device else None
        await self._http.set_repeat_on_user_playback(state.value, device_id=device_id)

    async def set_shuffle(self, state: ShuffleState, *, device: Optional[Device] = None) -> None:
        device_id = device.id if device else None
        value = True if state is ShuffleState.On else False

        await self._http.toggle_shuffle_for_user_playback(value, device_id=device_id)

    async def set_volume(self, volume: int, *, device: Optional[Device] = None) -> None:
        device_id = device.id if device else None
        await self._http.set_volume_for_user_playback(volume, device_id=device_id)

    async def transfer(self, devices: List[Device], *, play: Optional[bool] = None) -> None:
        device_ids = [device.id for device in devices]
        await self._http.transfer_user_playback(device_ids=device_ids, play=play)

    async def queue(self, item: Union[PartialTrack, PartialEpisode], *, device: Optional[Device] = None) -> None:
        device_id = device.id if device else None
        await self._http.add_item_to_queue(item.uri, device_id=device_id)