from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.hapi.services import token_delete_pb2
from hiero_sdk_python.response_code import ResponseCode

class TokenDeleteTransaction(Transaction):
    """
    Represents a token deletion transaction on the Hedera network.

    This transaction deletes a specified token, rendering it inactive.

    Inherits from the base Transaction class and implements the required methods
    to build and execute a token deletion transaction.
    """

    def __init__(self, token_id=None):
        """
        Initializes a new TokenDeleteTransaction instance with optional token_id.

        Args:
            token_id (TokenId, optional): The ID of the token to be deleted.
        """
        super().__init__()
        self.token_id = token_id
        self._default_transaction_fee = 3_000_000_000

    def set_token_id(self, token_id):
        """
        Sets the ID of the token to be deleted.

        Args:
            token_id (TokenId): The ID of the token to be deleted.

        Returns:
            TokenDeleteTransaction: Returns self for method chaining.
        """
        self._require_not_frozen()
        self.token_id = token_id
        return self

    def build_transaction_body(self):
        """
        Builds and returns the protobuf transaction body for token deletion.

        Returns:
            TransactionBody: The protobuf transaction body containing the token deletion details.

        Raises:
            ValueError: If the token ID is missing.
        """
        if not self.token_id:
            raise ValueError("Missing required TokenID.")

        token_delete_body = token_delete_pb2.TokenDeleteTransactionBody(
            token=self.token_id.to_proto()
        )

        transaction_body = self.build_base_transaction_body()
        transaction_body.tokenDeletion.CopyFrom(token_delete_body)

        return transaction_body

    def _execute_transaction(self, client, transaction_proto):
        """
        Executes the token deletion transaction using the provided client.

        Args:
            client (Client): The client instance to use for execution.
            transaction_proto (Transaction): The protobuf Transaction message.

        Returns:
            TransactionReceipt: The receipt from the network after transaction execution.

        Raises:
            Exception: If the transaction submission fails or receives an error response.
        """
        response = client.token_stub.deleteToken(transaction_proto)

        if response.nodeTransactionPrecheckCode != ResponseCode.OK:
            error_code = response.nodeTransactionPrecheckCode
            error_message = ResponseCode.get_name(error_code)
            raise Exception(f"Error during transaction submission: {error_code} ({error_message})")

        receipt = self.get_receipt(client)
        return receipt
