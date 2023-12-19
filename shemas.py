from dataclasses import dataclass

@dataclass
class Channel():
    url: str

@dataclass
class Channels():
    channels: list[Channel]

@dataclass
class BaseOutput():
    message: str

@dataclass
class SimChannel(Channel):
    similatity: float

@dataclass
class SimilarutyOutput200():
    top_channels: list[SimChannel]