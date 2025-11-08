"""Session manager for handling conversation persistence with JSON storage."""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any


class SessionManager:
    """Manages conversation sessions with JSON file storage."""

    def __init__(self, storage_dir: Path):
        """
        Initialize the session manager.

        Args:
            storage_dir: Directory where conversation JSON files are stored
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_session_path(self, session_id: str) -> Path:
        """Get the file path for a session."""
        return self.storage_dir / f"{session_id}.json"

    def _generate_session_id(self) -> str:
        """Generate a session ID based on current date and time."""
        return datetime.now().strftime("%Y-%m-%d_%H%M%S")

    def get_today_session_id(self) -> str:
        """Get or create today's session ID."""
        today = datetime.now().strftime("%Y-%m-%d")

        # Check if there's already a session for today
        existing_sessions = self.list_sessions()
        today_sessions = [s for s in existing_sessions if s.startswith(today)]

        if today_sessions:
            # Return the most recent session from today
            return sorted(today_sessions)[-1]

        # Create new session for today
        return f"{today}_session"

    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        return self._get_session_path(session_id).exists()

    def create_session(self, session_id: Optional[str] = None) -> str:
        """
        Create a new conversation session.

        Args:
            session_id: Optional session ID. If not provided, generates one.

        Returns:
            The session ID that was created
        """
        if session_id is None:
            session_id = self._generate_session_id()

        session_data = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "messages": [],
            "metadata": {
                "coins_discussed": [],
                "message_count": 0,
            }
        }

        session_path = self._get_session_path(session_id)
        with open(session_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)

        return session_id

    def load_session(self, session_id: str) -> Dict[str, Any]:
        """
        Load a conversation session.

        Args:
            session_id: The session ID to load

        Returns:
            The session data dictionary

        Raises:
            FileNotFoundError: If session doesn't exist
        """
        session_path = self._get_session_path(session_id)

        if not session_path.exists():
            raise FileNotFoundError(f"Session '{session_id}' not found")

        with open(session_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_session(self, session_data: Dict[str, Any]) -> None:
        """
        Save a conversation session.

        Args:
            session_data: The session data to save
        """
        session_id = session_data["session_id"]
        session_data["updated_at"] = datetime.now().isoformat()

        session_path = self._get_session_path(session_id)
        with open(session_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a message to a conversation session.

        Args:
            session_id: The session ID
            role: Message role ("user" or "assistant")
            content: Message content
            metadata: Optional metadata for the message
        """
        # Load or create session
        if self.session_exists(session_id):
            session_data = self.load_session(session_id)
        else:
            session_data = {
                "session_id": session_id,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "messages": [],
                "metadata": {
                    "coins_discussed": [],
                    "message_count": 0,
                }
            }

        # Create message
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }

        if metadata:
            message["metadata"] = metadata

        # Add message to session
        session_data["messages"].append(message)
        session_data["metadata"]["message_count"] = len(session_data["messages"])

        # Save session
        self.save_session(session_data)

    def get_messages(
        self,
        session_id: str,
        limit: Optional[int] = None,
        include_system: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get messages from a conversation session.

        Args:
            session_id: The session ID
            limit: Optional limit on number of recent messages to return
            include_system: Whether to include system messages

        Returns:
            List of messages in LangChain format
        """
        if not self.session_exists(session_id):
            return []

        session_data = self.load_session(session_id)
        messages = session_data["messages"]

        # Filter out system messages if requested
        if not include_system:
            messages = [m for m in messages if m["role"] != "system"]

        # Apply limit (keep most recent messages)
        if limit is not None and len(messages) > limit:
            messages = messages[-limit:]

        # Convert to LangChain format (role and content)
        return [
            {
                "role": msg["role"],
                "content": msg["content"]
            }
            for msg in messages
        ]

    def list_sessions(self) -> List[str]:
        """
        List all available sessions.

        Returns:
            List of session IDs
        """
        session_files = sorted(self.storage_dir.glob("*.json"))
        return [f.stem for f in session_files]

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a conversation session.

        Args:
            session_id: The session ID to delete

        Returns:
            True if deleted, False if session didn't exist
        """
        session_path = self._get_session_path(session_id)

        if session_path.exists():
            session_path.unlink()
            return True

        return False

    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """
        Get information about a session.

        Args:
            session_id: The session ID

        Returns:
            Dictionary with session metadata
        """
        session_data = self.load_session(session_id)

        return {
            "session_id": session_data["session_id"],
            "created_at": session_data["created_at"],
            "updated_at": session_data["updated_at"],
            "message_count": len(session_data["messages"]),
            "metadata": session_data.get("metadata", {}),
        }
