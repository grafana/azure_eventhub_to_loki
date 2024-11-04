from typing import ClassVar as _ClassVar
from typing import Iterable as _Iterable
from typing import Mapping as _Mapping
from typing import Optional as _Optional
from typing import Union as _Union

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers

DESCRIPTOR: _descriptor.FileDescriptor

class PushRequest(_message.Message):
    __slots__ = ("streams",)
    STREAMS_FIELD_NUMBER: _ClassVar[int]
    streams: _containers.RepeatedCompositeFieldContainer[StreamAdapter]
    def __init__(
        self, streams: _Optional[_Iterable[_Union[StreamAdapter, _Mapping]]] = ...
    ) -> None: ...

class PushResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class StreamAdapter(_message.Message):
    __slots__ = ("labels", "entries", "hash")
    LABELS_FIELD_NUMBER: _ClassVar[int]
    ENTRIES_FIELD_NUMBER: _ClassVar[int]
    HASH_FIELD_NUMBER: _ClassVar[int]
    labels: str
    entries: _containers.RepeatedCompositeFieldContainer[EntryAdapter]
    hash: int
    def __init__(
        self,
        labels: _Optional[str] = ...,
        entries: _Optional[_Iterable[_Union[EntryAdapter, _Mapping]]] = ...,
        hash: _Optional[int] = ...,
    ) -> None: ...

class LabelPairAdapter(_message.Message):
    __slots__ = ("name", "value")
    NAME_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    name: str
    value: str
    def __init__(
        self, name: _Optional[str] = ..., value: _Optional[str] = ...
    ) -> None: ...

class EntryAdapter(_message.Message):
    __slots__ = ("timestamp", "line", "structuredMetadata")
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    LINE_FIELD_NUMBER: _ClassVar[int]
    STRUCTUREDMETADATA_FIELD_NUMBER: _ClassVar[int]
    timestamp: _timestamp_pb2.Timestamp
    line: str
    structuredMetadata: _containers.RepeatedCompositeFieldContainer[LabelPairAdapter]
    def __init__(
        self,
        timestamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...,
        line: _Optional[str] = ...,
        structuredMetadata: _Optional[
            _Iterable[_Union[LabelPairAdapter, _Mapping]]
        ] = ...,
    ) -> None: ...
