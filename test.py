import queue

import requests

import pprint;pp = pprint.PrettyPrinter(indent=4)

class Crawler:

    def __init__(self,hostname):
        self.hostname = hostname
        self.q = queue.Queue()
        self.q.put("")

    def q_ids(self,links):
        for id in links:
            self.q.put(id)

    def processpage(self,id):
        print(f"Checking {id}...")
        url = self.hostname+(id if id else "test/cpu")
        print(url)
        max_retries = 20
        while max_retries:
            try:
                max_retries -= 1
                resp = requests.get(url)
                data = resp.json()
                break
            except:
                print(resp)
        try:
            if "links" in data:
                self.q_ids(data["links"])
        except:
            pp.pprint(data)
            exit(1)

    def crawl(self):
        while not self.q.empty():
            id = self.q.get()
            self.processpage(id)

def main(rootid=None):
    crawler = Crawler("http://localhost:5000/api/")
    crawler.crawl()

if __name__=="__main__":
    main()