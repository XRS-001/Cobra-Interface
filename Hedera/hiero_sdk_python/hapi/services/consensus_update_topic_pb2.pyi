from google.protobuf import wrappers_pb2 as _wrappers_pb2
import basic_types_pb2 as _basic_types_pb2
import duration_pb2 as _duration_pb2
import timestamp_pb2 as _timestamp_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ConsensusUpdateTopicTransactionBody(_message.Message):
    __slots__ = ("topicID", "memo", "expirationTime", "adminKey", "submitKey", "autoRenewPeriod", "autoRenewAccount")
    TOPICID_FIELD_NUMBER: _ClassVar[int]
    MEMO_FIELD_NUMBER: _ClassVar[int]
    EXPIRATIONTIME_FIELD_NUMBER: _ClassVar[int]
    ADMINKEY_FIELD_NUMBER: _ClassVar[int]
    SUBMITKEY_FIELD_NUMBER: _ClassVar[int]
    AUTORENEWPERIOD_FIELD_NUMBER: _ClassVar[int]
    AUTORENEWACCOUNT_FIELD_NUMBER: _ClassVar[int]
    topicID: _basic_types_pb2.TopicID
    memo: _wrappers_pb2.StringValue
    expirationTime: _timestamp_pb2.Timestamp
    adminKey: _basic_types_pb2.Key
    submitKey: _basic_types_pb2.Key
    autoRenewPeriod: _duration_pb2.Duration
    autoRenewAccount: _basic_types_pb2.AccountID
    def __init__(self, topicID: _Optional[_Union[_basic_types_pb2.TopicID, _Mapping]] = ..., memo: _Optional[_Union[_wrappers_pb2.StringValue, _Mapping]] = ..., expirationTime: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., adminKey: _Optional[_Union[_basic_types_pb2.Key, _Mapping]] = ..., submitKey: _Optional[_Union[_basic_types_pb2.Key, _Mapping]] = ..., autoRenewPeriod: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ..., autoRenewAccount: _Optional[_Union[_basic_types_pb2.AccountID, _Mapping]] = ...) -> None: ...
