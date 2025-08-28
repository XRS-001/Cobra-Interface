from hiero_sdk_python.query.query import Query
from hiero_sdk_python.hapi.services import query_pb2, consensus_get_topic_info_pb2
from hiero_sdk_python.consensus.topic_id import TopicId
from hiero_sdk_python.consensus.topic_info import TopicInfo

class TopicInfoQuery(Query):
    """
    A query to retrieve information about a specific Hedera topic.
    """

    def __init__(self, topic_id=None):
        """
        Initializes a new TopicInfoQuery instance with an optional topic_id.

        Args:
            topic_id (TopicId, optional): The ID of the topic to query.
        """
        super().__init__()
        self.topic_id = topic_id
        self._frozen = False 

    def _require_not_frozen(self):
        """
        Ensures the query is not frozen before making changes.
        """
        if self._frozen:
            raise ValueError("This query is frozen and cannot be modified.")

    def set_topic_id(self, topic_id: TopicId):
        """
        Sets the ID of the topic to query.

        Args:
            topic_id (TopicId): The ID of the topic.

        Returns:
            TopicInfoQuery: Returns self for method chaining.
        """
        self._require_not_frozen()
        self.topic_id = topic_id
        return self

    def freeze(self):
        """
        Marks the query as frozen, preventing further modification.

        Returns:
            TopicInfoQuery: Returns self for chaining.
        """
        self._frozen = True
        return self

    def _make_request(self):
        """
        Constructs the protobuf request for the query.

        Returns:
            Query: The protobuf query message.

        Raises:
            ValueError: If the topic ID is not set.
        """
        if not self.topic_id:
            raise ValueError("Topic ID must be set before making the request.")

        query_header = self._make_request_header()

        topic_info_query = consensus_get_topic_info_pb2.ConsensusGetTopicInfoQuery()
        topic_info_query.header.CopyFrom(query_header)
        topic_info_query.topicID.CopyFrom(self.topic_id.to_proto())

        query = query_pb2.Query()
        query.consensusGetTopicInfo.CopyFrom(topic_info_query)
        return query

    def _get_status_from_response(self, response):
        """
        Extracts the status from the query response.

        Args:
            response: The response protobuf message.

        Returns:
            ResponseCode: The status code from the response.
        """
        return response.consensusGetTopicInfo.header.nodeTransactionPrecheckCode

    def _map_response(self, response):
        """
        Maps the protobuf response to a TopicInfo instance.

        Args:
            response: The response protobuf message.

        Returns:
            TopicInfo: The topic info.

        Raises:
            Exception: If no topicInfo is returned in the response.
        """
        if not response.consensusGetTopicInfo.topicInfo:
            raise Exception("No topicInfo returned in the response.")

        proto_topic_info = response.consensusGetTopicInfo.topicInfo
        return TopicInfo.from_proto(proto_topic_info)
