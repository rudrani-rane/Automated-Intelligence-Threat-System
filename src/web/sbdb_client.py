import requests
import pandas as pd

SBDB_API = "https://ssd-api.jpl.nasa.gov/sbdb_query.api"

# Load asteroid names from raw data
ASTEROID_NAMES = {}
try:
    df = pd.read_csv("data/raw/sbdb_query_results.csv")
    ASTEROID_NAMES = dict(zip(df["spkid"].astype(str), df["full_name"]))
    print(f"Loaded {len(ASTEROID_NAMES)} asteroid names from database")
except Exception as e:
    print(f"Warning: Could not load asteroid names: {e}")


def get_asteroid_name(spkid):
    """Get asteroid name from spkid"""
    spkid_str = str(spkid)
    return ASTEROID_NAMES.get(spkid_str, f"Asteroid {spkid}")


def get_jpl_url(spkid):
    """Get JPL Small-Body Database Browser URL for asteroid"""
    return f"https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#/?sstr={spkid}"


def fetch_live_asteroids():

    params = {
        "fields": "spkid,full_name,neo,pha,H,e,a,q,i,om,w,ad,n,per,moid",
        "sb-kind": "a",
        "neo": "true"
    }

    try:
        res = requests.get(SBDB_API, params=params, timeout=10)
        data = res.json()

        if "data" not in data:
            return []

        return data["data"]

    except Exception as e:
        print("SBDB fetch error:", e)
        return []