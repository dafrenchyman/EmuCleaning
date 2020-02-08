import urllib.request

import requests

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) "
    + "Chrome/35.0.1916.47 Safari/537.36"
)


def download_binary_with_user_agent(url: str, file_location: str):
    # Create a request with a custom user-agent (Contivio won't let you download if it's not a "real" user-agent)
    req = urllib.request.Request(url, data=None, headers={"User-Agent": USER_AGENT})
    f = urllib.request.urlopen(req).read()

    with open(file_location, "wb") as outfile:
        outfile.write(f)
    return


def check_url_exists(url: str):
    status_code = requests.get(url, headers={"User-Agent": USER_AGENT}).status_code
    if status_code == 200:
        return True
    else:
        return False
