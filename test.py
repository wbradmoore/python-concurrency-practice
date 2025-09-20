import hashlib
import queue

import requests

import pprint;pp = pprint.PrettyPrinter(indent=4)

class Crawler:

    def __init__(self,hostname):
        self.hostname = hostname
        self.q = queue.Queue()
        self.qd = set()
        self.q.put("")

    def q_hashseed(self,data):
        print(f"processing {len(data)} hashseed"+"s"*(len(data)!=1))
        for seed in data:
            print(f"processing hashseed: {seed}")
            for i in range(5000000):
                seed = hashlib.md5(f"{seed}_{i}".encode()).hexdigest()
            print(f"  got: {seed[:4]}")
            self.q.put(seed[:4])

    def q_quadseed(self,data):
        print(f"processing {len(data)} quadseed"+"s"*(len(data)!=1))
        for seed in data:
            print(f"processing quadseed: {seed}")
            finalseed=""
            for seedpart in seed:
                for i in range(1250000):
                    seedpart = hashlib.md5(f"{seedpart}_{i}".encode()).hexdigest()
                print(f"  got: {seedpart[:1]}")
                finalseed+=seedpart[:1]  # Only append the first character
                print(f"  finalseed so far: {finalseed}")
            print(f"  final 4-char result: {finalseed}")
            self.q.put(finalseed)

    def q_ids(self,data):
        for id in data:
            self.q.put(id)

    def processpage(self,id):
        print(f"Processing page id: {id}")
        url = self.hostname+(id if id else "test/core")
        while True:
            try:
                resp = requests.get(url)
                break
            except Exception as e:
                print(e)
        data = resp.json()
        print(data)
        if "links" in data:
            self.q_ids(data["links"])
        if "hashseeds" in data:
            self.q_hashseed(data["hashseeds"])
        if "quadseeds" in data:
            self.q_quadseed(data["quadseeds"])

    def crawl(self):
        while not self.q.empty():
            id = self.q.get()
            self.processpage(id)

def main(rootid=None):
    crawler = Crawler("http://localhost:5000/api/")
    crawler.crawl()

if __name__=="__main__":
    main()