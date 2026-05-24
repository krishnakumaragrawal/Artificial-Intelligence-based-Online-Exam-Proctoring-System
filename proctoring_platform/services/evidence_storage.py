import hashlib
from pathlib import Path
from typing import BinaryIO, Tuple
from uuid import uuid4


class FileSystemEvidenceStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def save(self, session_id: int, filename: str, stream: BinaryIO) -> Tuple[str, int, str]:
        extension = Path(filename or "evidence.bin").suffix or ".bin"
        directory = self.root / "sessions" / str(session_id)
        directory.mkdir(parents=True, exist_ok=True)

        storage_key = f"sessions/{session_id}/{uuid4().hex}{extension}"
        destination = self.root / storage_key

        digest = hashlib.sha256()
        total_bytes = 0

        with destination.open("wb") as output:
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                total_bytes += len(chunk)
                digest.update(chunk)
                output.write(chunk)

        return storage_key, total_bytes, digest.hexdigest()
