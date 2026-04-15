import requests as req

def healthcheck():
    try:
        response = req.get('https://google.com/', timeout=5)
        if response.status_code == 200:
            return True
        else:
            return False
    except req.exceptions.RequestException:
        return False