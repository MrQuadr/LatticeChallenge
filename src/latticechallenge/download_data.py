#

import requests
from pathlib import Path
from time import sleep

class ExportData:
    info_challenge_data = {
        "Lattice_Challenge": {
            "link": ["https://www.latticechallenge.org/challenges/", "challenge-", ".bz2"],
            "range": [200, 2025, 25]
        },
        "SVP_Challenge": {
            "link": ["https://www.latticechallenge.org/svp-challenge/download/challenges/", "svpchallengedim", "seed0.txt"],
            "range": [140, 302, 2]
        },
        "Ideal_Lattice_Challenge": {
            "link": ["https://www.latticechallenge.org/ideallattice-challenge/download/challenges/", "ideallatticedim", ".zip"],
            "range": [52, 1026, 2],
            "ignore": "5d55275a5495d66d47d07d475b5c54d55526d27555d945d6d65d265d4dd4d45c5f9a71f55e65c45579675e5d56974d775865f5d765d7d35de57f55e6df"
        },
        "LWE_Challenge": {
            "link": ["https://www.latticechallenge.org/lwe_challenge/challenges/", "LWE_", ".txt"],
            "range": [40, 125, 5],
            "subrange": [5, 75, 5],
            "ignore": "1e1e232323414b4b4b4b4b4b4b4b4b4b4b"
        }
    }

    def __init__(self, workspace: str|Path, proxies: list = None):
        self.workspace = (Path(workspace) if isinstance(workspace, str) else workspace) / "data"
        for key in self.info_challenge_data.keys():
            folder = self.workspace / key
            folder.mkdir(parents=True, exist_ok=True)
        self.proxy = None if proxies is None else self.get_proxy(proxies)
        pass

    def get_proxy(self, proxies: list):
        size = len(proxies)
        i = -1
        while True:
            i = (i + 1) % size
            yield proxies[i]
    
    def download_file(self, url: str, dest: Path):
        proxy = None if self.proxy is None else next(self.proxy)
        proxies = {"http": proxy, "https": proxy}

        response = requests.get(url, timeout=10, proxies=proxies)
        response.raise_for_status()

        dest.write_bytes(response.content)
        return response.status_code

    def iterator_info_challenge_data(self, challenge: str = None) -> str:
        for chall in (self.info_challenge_data.keys() if challenge is None else [challenge]):
            if chall in ("Lattice_Challenge", "SVP_Challenge"):
                for i in range(*self.info_challenge_data[chall]["range"]):
                    yield chall, str(i)
            else:
                ignore_index = int(self.info_challenge_data[chall]["ignore"], 16)
                if chall == "Ideal_Lattice_Challenge":
                    for i in range(*self.info_challenge_data[chall]["range"]):
                        if ignore_index & 1:
                            yield chall, str(i)
                        ignore_index >>= 1
                else:
                    for i in range(*self.info_challenge_data[chall]["range"]):
                        subrange = self.info_challenge_data[chall]["subrange"]
                        subrange[1] = ignore_index & 0xFF
                        ignore_index >>= 8
                        for j in range(*subrange):
                            yield chall, f"{i}_{j:03}"
    
    def get_files_from_folder(self, folder: Path):
        files = []
        for f in folder.iterdir():
            if f.is_file():
                files.append(f)
            else:
                files += self.get_files_from_folder(f)
        return files

    def manager_download(self, challenge: str = None):
        get_link = self.iterator_info_challenge_data(challenge)
        files = self.get_files_from_folder(self.workspace)

        for i, j in get_link:
            filename = j.join(self.info_challenge_data[i]["link"][1:])
            link = self.info_challenge_data[i]["link"][0] + filename
            file = self.workspace / i / filename

            if file in files:
                print(f"Pass\t{filename}")
            else:
                sleep(1)
                status = self.download_file(link, file)

                if status == 200:
                    print(f"Ready\t{filename}")
                else:
                    print()
                    print(f"Error: {filename}")
                    print()