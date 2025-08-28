from event import state_signature_transaction_pb2 as _state_signature_transaction_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EventTransaction(_message.Message):
    __slots__ = ("application_transaction", "state_signature_transaction")
    APPLICATION_TRANSACTION_FIELD_NUMBER: _ClassVar[int]
    STATE_SIGNATURE_TRANSACTION_FIELD_NUMBER: _ClassVar[int]
    application_transaction: bytes
    state_signature_transaction: _state_signature_transaction_pb2.StateSignatureTransaction
    def __init__(self, application_transaction: _Optional[bytes] = ..., state_signature_transaction: _Optional[_Union[_state_signature_transaction_pb2.StateSignatureTransaction, _Mapping]] = ...) -> None: ...
