from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class TssShareSignatureTransactionBody(_message.Message):
    __slots__ = ("roster_hash", "share_index", "message_hash", "share_signature")
    ROSTER_HASH_FIELD_NUMBER: _ClassVar[int]
    SHARE_INDEX_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_HASH_FIELD_NUMBER: _ClassVar[int]
    SHARE_SIGNATURE_FIELD_NUMBER: _ClassVar[int]
    roster_hash: bytes
    share_index: int
    message_hash: bytes
    share_signature: bytes
    def __init__(self, roster_hash: _Optional[bytes] = ..., share_index: _Optional[int] = ..., message_hash: _Optional[bytes] = ..., share_signature: _Optional[bytes] = ...) -> None: ...
