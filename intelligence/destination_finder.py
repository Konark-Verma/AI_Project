import requests

def get_places(city):

    try:

        url = "https://en.wikipedia.org/w/api.php"

        params = {
            "action":"query",
            "list":"search",
            "srsearch":f"tourist attractions in {city}",
            "format":"json"
        }

        response = requests.get(url, params=params)

        data = response.json()

        places = []

        for item in data["query"]["search"][:5]:
            places.append(item["title"])

        return places

    except:
        return ["City Tour", "Local Sightseeing"]