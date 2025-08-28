import basic_types_pb2 as _basic_types_pb2
import query_header_pb2 as _query_header_pb2
import response_header_pb2 as _response_header_pb2
import contract_types_pb2 as _contract_types_pb2
from google.protobuf import wrappers_pb2 as _wrappers_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ContractLoginfo(_message.Message):
    __slots__ = ("contractID", "bloom", "topic", "data")
    CONTRACTID_FIELD_NUMBER: _ClassVar[int]
    BLOOM_FIELD_NUMBER: _ClassVar[int]
    TOPIC_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    contractID: _basic_types_pb2.ContractID
    bloom: bytes
    topic: _containers.RepeatedScalarFieldContainer[bytes]
    data: bytes
    def __init__(self, contractID: _Optional[_Union[_basic_types_pb2.ContractID, _Mapping]] = ..., bloom: _Optional[bytes] = ..., topic: _Optional[_Iterable[bytes]] = ..., data: _Optional[bytes] = ...) -> None: ...

class ContractFunctionResult(_message.Message):
    __slots__ = ("contractID", "contractCallResult", "errorMessage", "bloom", "gasUsed", "logInfo", "createdContractIDs", "evm_address", "gas", "amount", "functionParameters", "sender_id", "contract_nonces", "signer_nonce")
    CONTRACTID_FIELD_NUMBER: _ClassVar[int]
    CONTRACTCALLRESULT_FIELD_NUMBER: _ClassVar[int]
    ERRORMESSAGE_FIELD_NUMBER: _ClassVar[int]
    BLOOM_FIELD_NUMBER: _ClassVar[int]
    GASUSED_FIELD_NUMBER: _ClassVar[int]
    LOGINFO_FIELD_NUMBER: _ClassVar[int]
    CREATEDCONTRACTIDS_FIELD_NUMBER: _ClassVar[int]
    EVM_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    GAS_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    FUNCTIONPARAMETERS_FIELD_NUMBER: _ClassVar[int]
    SENDER_ID_FIELD_NUMBER: _ClassVar[int]
    CONTRACT_NONCES_FIELD_NUMBER: _ClassVar[int]
    SIGNER_NONCE_FIELD_NUMBER: _ClassVar[int]
    contractID: _basic_types_pb2.ContractID
    contractCallResult: bytes
    errorMessage: str
    bloom: bytes
    gasUsed: int
    logInfo: _containers.RepeatedCompositeFieldContainer[ContractLoginfo]
    createdContractIDs: _containers.RepeatedCompositeFieldContainer[_basic_types_pb2.ContractID]
    evm_address: _wrappers_pb2.BytesValue
    gas: int
    amount: int
    functionParameters: bytes
    sender_id: _basic_types_pb2.AccountID
    contract_nonces: _containers.RepeatedCompositeFieldContainer[_contract_types_pb2.ContractNonceInfo]
    signer_nonce: _wrappers_pb2.Int64Value
    def __init__(self, contractID: _Optional[_Union[_basic_types_pb2.ContractID, _Mapping]] = ..., contractCallResult: _Optional[bytes] = ..., errorMessage: _Optional[str] = ..., bloom: _Optional[bytes] = ..., gasUsed: _Optional[int] = ..., logInfo: _Optional[_Iterable[_Union[ContractLoginfo, _Mapping]]] = ..., createdContractIDs: _Optional[_Iterable[_Union[_basic_types_pb2.ContractID, _Mapping]]] = ..., evm_address: _Optional[_Union[_wrappers_pb2.BytesValue, _Mapping]] = ..., gas: _Optional[int] = ..., amount: _Optional[int] = ..., functionParameters: _Optional[bytes] = ..., sender_id: _Optional[_Union[_basic_types_pb2.AccountID, _Mapping]] = ..., contract_nonces: _Optional[_Iterable[_Union[_contract_types_pb2.ContractNonceInfo, _Mapping]]] = ..., signer_nonce: _Optional[_Union[_wrappers_pb2.Int64Value, _Mapping]] = ...) -> None: ...

class ContractCallLocalQuery(_message.Message):
    __slots__ = ("header", "contractID", "gas", "functionParameters", "maxResultSize", "sender_id")
    HEADER_FIELD_NUMBER: _ClassVar[int]
    CONTRACTID_FIELD_NUMBER: _ClassVar[int]
    GAS_FIELD_NUMBER: _ClassVar[int]
    FUNCTIONPARAMETERS_FIELD_NUMBER: _ClassVar[int]
    MAXRESULTSIZE_FIELD_NUMBER: _ClassVar[int]
    SENDER_ID_FIELD_NUMBER: _ClassVar[int]
    header: _query_header_pb2.QueryHeader
    contractID: _basic_types_pb2.ContractID
    gas: int
    functionParameters: bytes
    maxResultSize: int
    sender_id: _basic_types_pb2.AccountID
    def __init__(self, header: _Optional[_Union[_query_header_pb2.QueryHeader, _Mapping]] = ..., contractID: _Optional[_Union[_basic_types_pb2.ContractID, _Mapping]] = ..., gas: _Optional[int] = ..., functionParameters: _Optional[bytes] = ..., maxResultSize: _Optional[int] = ..., sender_id: _Optional[_Union[_basic_types_pb2.AccountID, _Mapping]] = ...) -> None: ...

class ContractCallLocalResponse(_message.Message):
    __slots__ = ("header", "functionResult")
    HEADER_FIELD_NUMBER: _ClassVar[int]
    FUNCTIONRESULT_FIELD_NUMBER: _ClassVar[int]
    header: _response_header_pb2.ResponseHeader
    functionResult: ContractFunctionResult
    def __init__(self, header: _Optional[_Union[_response_header_pb2.ResponseHeader, _Mapping]] = ..., functionResult: _Optional[_Union[ContractFunctionResult, _Mapping]] = ...) -> None: ...
