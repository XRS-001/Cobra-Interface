import basic_types_pb2 as _basic_types_pb2
import duration_pb2 as _duration_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ConsensusCreateTopicTransactionBody(_message.Message):
    __slots__ = ("memo", "adminKey", "submitKey", "autoRenewPeriod", "autoRenewAccount")
    MEMO_FIELD_NUMBER: _ClassVar[int]
    ADMINKEY_FIELD_NUMBER: _ClassVar[int]
    SUBMITKEY_FIELD_NUMBER: _ClassVar[int]
    AUTORENEWPERIOD_FIELD_NUMBER: _ClassVar[int]
    AUTORENEWACCOUNT_FIELD_NUMBER: _ClassVar[int]
    memo: str
    adminKey: _basic_types_pb2.Key
    submitKey: _basic_types_pb2.Key
    autoRenewPeriod: _duration_pb2.Duration
    autoRenewAccount: _basic_types_pb2.AccountID
    def __init__(self, memo: _Optional[str] = ..., adminKey: _Optional[_Union[_basic_types_pb2.Key, _Mapping]] = ..., submitKey: _Optional[_Union[_basic_types_pb2.Key, _Mapping]] = ..., autoRenewPeriod: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ..., autoRenewAccount: _Optional[_Union[_basic_types_pb2.AccountID, _Mapping]] = ...) -> None: ...
