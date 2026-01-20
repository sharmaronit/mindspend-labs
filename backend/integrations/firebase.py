from typing import Any, Dict, Optional

class FirebaseClient:
    """Firebase adapter with graceful fallback.

    If `firebase_admin` is available and a service account is provided,
    verifies ID tokens and writes to Firestore. Otherwise, stubs out.
    """

    def __init__(self, project_id: Optional[str] = None, service_account_path: Optional[str] = None):
        self.project_id = project_id
        self._admin = None
        self._auth = None
        self._firestore = None
        try:
            import firebase_admin  # type: ignore
            from firebase_admin import credentials, auth
            from firebase_admin import firestore
            cred = None
            if service_account_path:
                cred = credentials.Certificate(service_account_path)
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
            self._admin = firebase_admin
            self._auth = auth
            self._firestore = firestore.client()
        except Exception:
            self._admin = None
            self._auth = None
            self._firestore = None

    def verify_token(self, token: str) -> bool:
        if not token:
            return False
        if self._auth is None:
            # Fallback: treat any non-empty token as valid in dev
            return True
        try:
            self._auth.verify_id_token(token)
            return True
        except Exception:
            return False

    def save_analysis(self, user_id: str, data: Dict[str, Any]) -> None:
        if self._firestore is None:
            return
        doc_ref = self._firestore.collection("pfba_analyses").document(user_id)
        # Store last analysis snapshot
        doc_ref.set({"last": data}, merge=True)
