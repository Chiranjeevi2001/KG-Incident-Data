import os
from dotenv import load_dotenv

# Load environment variables from .env file in the project root
# Assuming config.py is in src/ and .env is in incident_kg_project/
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"), override=True)

# Neo4j Configuration
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE") or "neo4j"

# -----------------------------------------------------------------------------
# OCI Configuration
# Goal: Pick up config from ~/.oci/config using the DEFAULT profile
# - Uses OCI SDK to parse the profile and expose useful fields
# - Derives GenAI service endpoint from the region in the OCI profile
# - compartment_id is not standard in OCI config; will read from env first, then
#   fall back to a nonstandard "compartment_id" key in ~/.oci/config if present.
# -----------------------------------------------------------------------------

OCI_CONFIG_PROFILE = os.getenv("OCI_CONFIG_PROFILE", "DEFAULT")
# Default to the user's standard OCI config path; resolves to /Users/chirabs/.oci/config on this machine
OCI_CONFIG_FILE = os.getenv("OCI_CONFIG_FILE", os.path.expanduser("~/.oci/config"))

# Defaults
OCI_CONFIG = {}
OCI_REGION = None
OCI_TENANCY = None
OCI_USER = None
OCI_FINGERPRINT = None
OCI_KEY_FILE = None

try:
    import oci  # type: ignore

    # Load from ~/.oci/config (DEFAULT profile by default)
    OCI_CONFIG = oci.config.from_file(
        file_location=OCI_CONFIG_FILE, profile_name=OCI_CONFIG_PROFILE
    )

    # Commonly used fields
    OCI_REGION = OCI_CONFIG.get("region")
    OCI_TENANCY = OCI_CONFIG.get("tenancy")
    OCI_USER = OCI_CONFIG.get("user")
    OCI_FINGERPRINT = OCI_CONFIG.get("fingerprint")
    OCI_KEY_FILE = OCI_CONFIG.get("key_file")
except Exception:
    # Leave OCI_* defaults as None if loading fails; LangChain/OCI clients may still
    # work with alt auth methods or explicit env vars.
    pass


def _genai_endpoint_from_region(region: str | None) -> str | None:
    if not region:
        return None
    # OCI GenAI inference endpoint pattern
    return f"https://inference.generativeai.us-chicago-1.oci.oraclecloud.com"


# Compartment OCID: prefer env, else optional nonstandard key in ~/.oci/config
OCI_COMPARTMENT_ID = os.getenv("OCI_COMPARTMENT_ID") or OCI_CONFIG.get("compartment_id")

# GenAI endpoint: prefer env override, else derive from region in OCI profile
OCI_GENAI_ENDPOINT = os.getenv("OCI_GENAI_ENDPOINT") or _genai_endpoint_from_region(OCI_REGION)

# Paths
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DATA_FILE = os.path.join(DATA_DIR, "incidents.json")
