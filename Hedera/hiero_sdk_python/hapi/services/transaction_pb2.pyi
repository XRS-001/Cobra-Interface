import basic_types_pb2 as _basic_types_pb2
import transaction_body_pb2 as _transaction_body_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Transaction(_message.Message):
    __slots__ = ("body", "sigs", "sigMap", "bodyBytes", "signedTransactionBytes")
    BODY_FIELD_NUMBER: _ClassVar[int]
    SIGS_FIELD_NUMBER: _ClassVar[int]
    SIGMAP_FIELD_NUMBER: _ClassVar[int]
    BODYBYTES_FIELD_NUMBER: _ClassVar[int]
    SIGNEDTRANSACTIONBYTES_FIELD_NUMBER: _ClassVar[int]
    body: _transaction_body_pb2.TransactionBody
    sigs: _basic_types_pb2.SignatureList
    sigMap: _basic_types_pb2.SignatureMap
    bodyBytes: bytes
    signedTransactionBytes: bytes
    def __init__(self, body: _Optional[_Union[_transaction_body_pb2.TransactionBody, _Mapping]] = ..., sigs: _Optional[_Union[_basic_types_pb2.SignatureList, _Mapping]] = ..., sigMap: _Optional[_Union[_basic_types_pb2.SignatureMap, _Mapping]] = ..., bodyBytes: _Optional[bytes] = ..., signedTransactionBytes: _Optional[bytes] = ...) -> None: ...
