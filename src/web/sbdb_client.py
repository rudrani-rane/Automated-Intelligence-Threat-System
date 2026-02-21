import requests

SBDB_API = "https://ssd-api.jpl.nasa.gov/sbdb_query.api"


def fetch_live_asteroids():

    params = {
        "fields": "spkid,neo,pha,H,e,a,q,i,om,w,ad,n,per,moid",
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