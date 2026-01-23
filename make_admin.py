
from backend.app.services.auth_service import make_admin, init_db
import os

if __name__ == "__main__":
    if not os.path.exists("irresistible_app.db"):
        init_db()
    make_admin("testuser")
    print("Promoted testuser to admin")
