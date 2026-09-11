import requests
import datetime

import os



from config import get_redis_client, get_tender_config

REDIRECTS_KEY = "wiki:ru:redirects"
REDIRECTS_TTL = 3 * 24 * 3600
RELOAD_THRESHOLD = 3 * 3600

# Script config
script_config = get_tender_config()

# Redis fun
red_con = get_redis_client()



def get_all_redirects(redis):
    
    if os.path.exists("redirects.txt"):
        os.replace("redirects.txt", "redirects.old.txt")
    if os.path.exists("redirects.raw.txt"):
        os.replace("redirects.raw.txt", "redirects.raw.old.txt")
    
    redis.delete(REDIRECTS_KEY)
    
    API_URL = "https://ru.wikipedia.org/w/api.php"

    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "list": "allredirects",
        "arnamespace": 0,
        "arlimit": "max",
        "arprop": "ids|title|fragment",
    }
    
    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "generator": "allredirects",
        "garnamespace": 0,
        "garlimit": "max",
    }

    redirects = []

    i = 0
    print(datetime.datetime.now())
    while True:
        i += 1
        print("Updating redirects cache, iteration", i, ", have", len(redirects), "at start")
        
        response = requests.get(API_URL, params=params, headers=script_config["headers"], timeout=30)
        response.raise_for_status()
        data = response.json()
        
        redirects.extend(data["query"]["pages"])
        
        batch = data["query"]["pages"]
        titles = list(dict.fromkeys(item["title"] for item in batch))
        
        
        # Emergency copy
        with open("redirects.txt", "a", encoding="utf-8") as f:
            for title in titles:
                f.write(title + "\n")

        with open("redirects.raw.txt", "a", encoding="utf-8") as f:
            for redirect in batch:
                f.write(redirect["title"] + "\n")

        # Main Redis fun
        redis.sadd(REDIRECTS_KEY, *titles)

        if "continue" not in data:
            break

        params["garcontinue"] = data["continue"]["garcontinue"]


    redis.expire(REDIRECTS_KEY, REDIRECTS_TTL)

    print(datetime.datetime.now())
    print(f"Всего редиректов: {len(redirects)}")
    print(f"Redir type: {type(redirects)}")

    return redirects

def ensure_redirects_cache(redis):
    ttl = redis.ttl(REDIRECTS_KEY)
    print("Hours till redirect cache expires:", round(ttl/3600, 2))

    if ttl >= RELOAD_THRESHOLD:
        return

    redirects = get_all_redirects(redis)


ensure_redirects_cache(red_con)
