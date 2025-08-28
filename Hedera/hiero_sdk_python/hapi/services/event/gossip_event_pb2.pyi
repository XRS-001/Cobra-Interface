from event import event_transaction_pb2 as _event_transaction_pb2
from event import event_core_pb2 as _event_core_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GossipEvent(_message.Message):
    __slots__ = ("event_core", "signature", "event_transaction", "transactions")
    EVENT_CORE_FIELD_NUMBER: _ClassVar[int]
    SIGNATURE_FIELD_NUMBER: _ClassVar[int]
    EVENT_TRANSACTION_FIELD_NUMBER: _ClassVar[int]
    TRANSACTIONS_FIELD_NUMBER: _ClassVar[int]
    event_core: _event_core_pb2.EventCore
    signature: bytes
    event_transaction: _containers.RepeatedCompositeFieldContainer[_event_transaction_pb2.EventTransaction]
    transactions: _containers.RepeatedScalarFieldContainer[bytes]
    def __init__(self, event_core: _Optional[_Union[_event_core_pb2.EventCore, _Mapping]] = ..., signature: _Optional[bytes] = ..., event_transaction: _Optional[_Iterable[_Union[_event_transaction_pb2.EventTransaction, _Mapping]]] = ..., transactions: _Optional[_Iterable[bytes]] = ...) -> None: ...
