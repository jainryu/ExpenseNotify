from http.client import HTTPException
import os
import aioboto3
from aiohttp import ClientError

from app.models.sns import ExpenseEventType


SNS_REGION = 'us-west-1'
SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN")
SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")


class EventBus:
    def __init__(self):
        self.session = aioboto3.Session()

    async def publish_event(self, message: str, event_type: ExpenseEventType):
        """Publish a message to SNS topic"""
        async with self.session.client("sns", region_name=SNS_REGION) as sns:
            try:
                response = await sns.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Message=message,
                    MessageAttributes={
                        'EventType': {
                            'DataType': 'String',
                            'StringValue': event_type
                        }
                    }
                )
                return response.get("MessageId")
            except ClientError as e:
                raise HTTPException(status_code=500, detail=str(e))
