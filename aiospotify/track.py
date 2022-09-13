from typing import Dict, Any, List

from .partials import PartialTrack, PartialAlbum
from .http import HTTPClient

__all__ = (
    'TrackAudioFeatures',
    'TrackAudioAnalysis',
    'TrackAudioAnalysisMeta',
    'TrackAudioAnalysisSegment',
    'TrackAudioAnalysisTrack',
    'TrackAudioAnalysisSection',
    'TrackAudioAnalysisBeat',
    'TrackAudioAnalysisTatum',
    'TrackAudioAnalysisBar',
    'Track', 
    'UserTrack'
)

class TrackAudioFeatures:
    def __init__(self, data: Dict[str, Any]) -> None:
        self.acousticness: float = data['acousticness']
        self.analysis_url: str = data['analysis_url']
        self.danceability: float = data['danceability']
        self.duration_ms: int = data['duration_ms']
        self.energy: float = data['energy']
        self.id: str = data['id']
        self.instrumentalness: float = data['instrumentalness']
        self.key: int = data['key']
        self.liveness: float = data['liveness']
        self.loudness: float = data['loudness']
        self.mode: int = data['mode']
        self.speechiness: float = data['speechiness']
        self.tempo: float = data['tempo']
        self.time_signature: int = data['time_signature']
        self.track_href: str = data['track_href']
        self.type: str = data['type']
        self.uri: str = data['uri']
        self.valence: float = data['valence']

    def __repr__(self) -> str:
        return f'<TrackAudioFeatures id={self.id!r} uri={self.uri!r}>'

class TrackAudioAnalysisMeta:
    def __init__(self, data: Dict[str, Any]) -> None:
        self.analyzer_version: str = data['analyzer_version']
        self.platform: str = data['platform']
        self.detailed_status: str = data['detailed_status']
        self.status_code: int = data['status_code']
        self.timestamp: int = data['timestamp']
        self.analysis_time: int = data['analysis_time']
        self.input_process: str = data['input_process']

    def __repr__(self) -> str:
        return f'<TrackAudioAnalysisMeta platform={self.platform!r} status_code={self.status_code}>'

class TrackAudioAnalysisTrack:
    def __init__(self, data: Dict[str, Any]) -> None:
        self.num_samples: int = data['num_samples']
        self.duration: int = data['duration']
        self.sample_md5: str = data['sample_md5']
        self.offset_seconds: int = data['offset_seconds']
        self.window_seconds: int = data['window_seconds']
        self.analysis_sample_rate: int = data['analysis_sample_rate']
        self.analysis_channels: int = data['analysis_channels']
        self.end_of_fade_in: int = data['end_of_fade_in']
        self.start_of_fade_out: int = data['start_of_fade_out']
        self.loudness: float = data['loudness']
        self.tempo: float = data['tempo']
        self.tempo_confidence: float = data['tempo_confidence']
        self.time_signature: int = data['time_signature']
        self.time_signature_confidence: float = data['time_signature_confidence']
        self.key: int = data['key']
        self.key_confidence: float = data['key_confidence']
        self.mode: int = data['mode']
        self.mode_confidence: float = data['mode_confidence']
        self.codestring: str = data['codestring']
        self.code_version: str = data['code_version']
        self.echoprintstring: str = data['echoprintstring']
        self.echoprint_version: str = data['echoprint_version']
        self.synchstring: str = data['synchstring']
        self.synch_version: str = data['synch_version']
        self.rhythmstring: str = data['rhythmstring']
        self.rhythm_version: str = data['rhythm_version']

    def __repr__(self) -> str:
        return f'<TrackAudioAnalysisTrack num_samples={self.num_samples!r} duration={self.duration!r}>'

class TrackAudioAnalysisBar:
    def __init__(self, data: Dict[str, Any]) -> None:
        self.start: float = data['start']
        self.duration: float = data['duration']
        self.confidence: float = data['confidence']

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} start={self.start!r} duration={self.duration!r}>'

class TrackAudioAnalysisBeat(TrackAudioAnalysisBar):
    pass

class TrackAudioAnalysisSection(TrackAudioAnalysisBar):
    def __init__(self, data: Dict[str, Any]) -> None:
        super().__init__(data)
        self.loudness: float = data['loudness']
        self.tempo: float = data['tempo']
        self.tempo_confidence: float = data['tempo_confidence']
        self.key: int = data['key']
        self.key_confidence: float = data['key_confidence']
        self.mode: int = data['mode']
        self.mode_confidence: float = data['mode_confidence']
        self.time_signature: int = data['time_signature']
        self.time_signature_confidence: float = data['time_signature_confidence']

    def __repr__(self) -> str:
        return f'<TrackAudioAnalysisSection start={self.start!r} duration={self.duration!r} loudness={self.loudness!r} tempo={self.tempo!r}>'

class TrackAudioAnalysisSegment(TrackAudioAnalysisBar):
    def __init__(self, data: Dict[str, Any]) -> None:
        super().__init__(data)
        self.loudness_start: float = data['loudness_start']
        self.loudness_max: float = data['loudness_max']
        self.loudness_max_time: float = data['loudness_max_time']
        self.loudness_end: float = data['loudness_end']
        self.pitches: List[float] = data['pitches']
        self.timbre: List[float] = data['timbre']

class TrackAudioAnalysisTatum(TrackAudioAnalysisBar):
    pass

class TrackAudioAnalysis:
    def __init__(self, data: Dict[str, Any]) -> None:
        self.meta = TrackAudioAnalysisMeta(data['meta'])
        self.track = TrackAudioAnalysisTrack(data['track'])
        self.bars = [TrackAudioAnalysisBar(bar) for bar in data['bars']]
        self.beats = [TrackAudioAnalysisBeat(beat) for beat in data['beats']]
        self.sections = [TrackAudioAnalysisSection(section) for section in data['sections']]
        self.segments = [TrackAudioAnalysisSegment(segment) for segment in data['segments']]
        self.tatums = [TrackAudioAnalysisTatum(tatum) for tatum in data['tatums']]

class Track(PartialTrack):
    __slots__ = PartialTrack.__slots__ + ('_http', 'is_playable', 'linked_from')

    def __init__(self, data: Dict[str, Any], http: HTTPClient) -> None:
        self._http = http
        super().__init__(data)

        self.is_playable: bool = data.get('is_playable', False)
        self.linked_from = PartialTrack(data['linked_from']) if data.get('linked_from') else None

    @property
    def album(self) -> PartialAlbum:
        return PartialAlbum(self._data['album'], self._http)

    async def fetch_audio_features(self) -> TrackAudioFeatures:
        data = await self._http.get_track_audio_features(self.id)
        return TrackAudioFeatures(data)

    async def fetch_audio_analysis(self) -> TrackAudioAnalysis:
        data = await self._http.get_track_audio_analysis(self.id)
        return TrackAudioAnalysis(data)

class UserTrack(Track):
    __slots__ = Track.__slots__ + ('added_at',)

    def __init__(self, data: Dict[str, Any], http: HTTPClient) -> None:
        super().__init__(data['track'], http)
        self.added_at = data['added_at']
