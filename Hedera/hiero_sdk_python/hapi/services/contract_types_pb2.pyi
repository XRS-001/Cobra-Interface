import basic_types_pb2 as _basic_types_pb2
from google.protobuf import wrappers_pb2 as _wrappers_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ContractNonceInfo(_message.Message):
    __slots__ = ("contract_id", "nonce")
    CONTRACT_ID_FIELD_NUMBER: _ClassVar[int]
    NONCE_FIELD_NUMBER: _ClassVar[int]
    contract_id: _basic_types_pb2.ContractID
    nonce: int
    def __init__(self, contract_id: _Optional[_Union[_basic_types_pb2.ContractID, _Mapping]] = ..., nonce: _Optional[int] = ...) -> None: ...
