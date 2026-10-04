"""Azure Blob + Queue adapter; works against Azurite (connection string) or Azure (account URL + MI)."""

from __future__ import annotations

from contextlib import suppress

from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient, ContentSettings
from azure.storage.queue import QueueClient, QueueServiceClient

from pmo_core.models import QueueMessage


class AzureStorage:
    """Implements both `BlobStore` and `JobQueue`."""

    def __init__(
        self,
        container: str,
        queue: str,
        connection_string: str = "",
        account_url: str = "",
    ) -> None:
        """Build clients from a connection string (Azurite) or an account URL (Azure)."""
        if connection_string:
            self.blob_service = BlobServiceClient.from_connection_string(connection_string)
            queue_service = QueueServiceClient.from_connection_string(connection_string)
        elif account_url:
            from azure.identity import DefaultAzureCredential

            credential = DefaultAzureCredential()
            self.blob_service = BlobServiceClient(account_url=account_url, credential=credential)
            queue_url = account_url.replace(".blob.", ".queue.")
            queue_service = QueueServiceClient(account_url=queue_url, credential=credential)
        else:
            raise ValueError("Set STORAGE_CONNECTION_STRING or STORAGE_ACCOUNT_URL")
        self.container = self.blob_service.get_container_client(container)
        self.queue: QueueClient = queue_service.get_queue_client(queue)

    def ensure(self) -> None:
        """Create the blob container and the queue if missing."""
        with suppress(ResourceExistsError):
            self.container.create_container()
        with suppress(ResourceExistsError):
            self.queue.create_queue()

    def ping(self) -> None:
        """Raise if the queue is unreachable."""
        self.queue.get_queue_properties()

    def put(self, path: str, data: bytes, content_type: str) -> None:
        """Upload bytes, overwriting any existing blob."""
        self.container.upload_blob(
            path, data, overwrite=True, content_settings=ContentSettings(content_type=content_type)
        )

    def get(self, path: str) -> bytes:
        """Download a blob's bytes."""
        return self.container.download_blob(path).readall()

    def send(self, job_id: str) -> None:
        """Enqueue a job ID."""
        self.queue.send_message(job_id)

    def receive(self, visibility_timeout_s: int = 300) -> QueueMessage | None:
        """Receive at most one message."""
        for message in self.queue.receive_messages(max_messages=1, visibility_timeout=visibility_timeout_s):
            return QueueMessage(
                message_id=message.id,
                pop_receipt=message.pop_receipt or "",
                job_id=str(message.content),
                dequeue_count=message.dequeue_count or 0,
            )
        return None

    def delete(self, msg: QueueMessage) -> None:
        """Delete a processed message."""
        self.queue.delete_message(msg.message_id, msg.pop_receipt)
