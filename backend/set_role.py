import firebase_admin
from firebase_admin import credentials, auth

cred = credentials.Certificate("firebase-admin-key.json")
firebase_admin.initialize_app(cred)

# Replace with real UID from Firebase Console
auth.set_custom_user_claims(
    uid="VMEasA5VdaTKZPIYVF39sEKAVXk1",
    custom_claims={"role": "admin"}
)

print("Role assigned")
