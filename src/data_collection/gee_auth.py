"""
Robust Google Earth Engine authentication and initialization.
Auto-authenticates only if initialization fails.
"""

import ee


PROJECT_ID = "hackathon-484205"


class GEEAuthenticator:
    """Handles reliable Google Earth Engine authentication."""

    def __init__(self):
        self.authenticated = False

    def authenticate(self, force_reauth: bool = False) -> bool:
        try:
            if force_reauth:
                print("Forcing authentication...")
                ee.Authenticate()

            ee.Initialize(project=PROJECT_ID)
            self.authenticated = True
            print("✓ Google Earth Engine initialized")
            return True

        except Exception:
            try:
                print("Initialization failed, running authentication flow...")
                ee.Authenticate()
                ee.Initialize(project=PROJECT_ID)
                self.authenticated = True
                print("✓ Google Earth Engine authenticated and initialized")
                return True

            except Exception as e:
                print("✗ Google Earth Engine authentication failed")
                print(f"Reason: {e}")
                print("\nManual fix:")
                print("  earthengine authenticate")
                self.authenticated = False
                return False

    def is_authenticated(self) -> bool:
        return self.authenticated


def init_earth_engine(force_reauth: bool = False) -> bool:
    auth = GEEAuthenticator()
    return auth.authenticate(force_reauth)


if __name__ == "__main__":
    print("Testing Google Earth Engine authentication...")
    if init_earth_engine():
        print("✓ Earth Engine ready for use")
    else:
        print("✗ Earth Engine not ready")
