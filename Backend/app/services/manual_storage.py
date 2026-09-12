from io import BytesIO

from bson import ObjectId
from gridfs import GridFS

from app.core.mongodb import get_database


class ManualStorage:

    def __init__(self) -> None:
        self.db = get_database()
        self.fs = GridFS(self.db)

    def save_pdf(
        self,
        filename: str,
        content: bytes,
        machine_id: str,
    ) -> str:

        file_id = self.fs.put(
            BytesIO(content),
            filename=filename,
            content_type="application/pdf",
            metadata={
                "machine_id": machine_id,
                "type": "machine_user_manual",
            },
        )

        return str(file_id)

    def get_pdf(
        self,
        file_id: str,
    ) -> bytes:

        grid_file = self.fs.get(
            ObjectId(file_id)
        )

        return grid_file.read()