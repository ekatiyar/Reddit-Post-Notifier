import requests

class Client:
    def __init__(self, url: str, api_key: str, model: str):
        self.url = url
        self.api_key = api_key
        self.model = model

    def generate_title(self, title: str, body: str, include_terms: list[str]) -> str:
        """Generate a title for the post that only contains relevant info (item, price, etc.)."""
        url = f'{self.url}/api/chat/completions'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": f"""
                        Create a summary title for a reddit post. I only care about relevant info
                        (price and other item details) for the specified Include Terms: 

                        Here's an example:
                        Include Terms: [5080, ssd]
                        Title: [USA-CA] [H] Z690I Strix, 16GB DDR4, 1 TB 990 Evo+, RTX 5080 FE, Nouvolo Aquanaut, N150, Samsung Tablet [W] Paypal, Cash
                        Body: Timestamps: https://imgur.com/a/pBYiR3O\n\n&amp;nbsp;\n\n|Item|Condition|Price|\n|:-|:-|:-|\n|Asus Z690I Strix - only includes what is visible in the pictures, specifically missing the SATA add on card|Used|$140 shipped|\n|Samsung 990 Evo Plus 1TB Gen 4 M.2 NVME SSD|Brand new sealed|$60 shipped |\n|Corsair DDR4 2x8GB (16GB) 3000MHz [Amazon link](https://www.amazon.com/dp/B0134EW7G8)|Brand new sealed|$25 shipped |\n|Corsair XG7 waterblock + backplate for Asus 3090TI cards - this block has been modified to fit on the 4090 TUF OG as well. Just had to dremel out a few bits. The modifications are invisible once the block is installed. See: https://imgur.com/a/I9QltNV |Used|$60 shipped|\n|Hanjiang 240mm radiator (17mm thick for SFF builds)|Used|$50 shipped|\n|Nouvolo Aquanaut Extreme w/ DDC pump|Used|$80 shipped|\n|Samsung S7 FE Tablet 128GB SM-T733 - like new condition, this thing has mostly just been sitting around unused|Used|$140 shipped |\n|N150 mini pc w/ 512GB/16GB -  [BAPCS link](https://www.reddit.com/r/buildapcsales/comments/1kvzrof/prebuilt_e3_mini_pc_intel_n150_16gb_ddr4_ram/) - I bought this because it was a steal but didn't end up having a good use for it. Opened it to make sure I was actually getting a PC, but never powered on. Just offering to pass on a deal before I return it.|New open box|$80 cash only|\n|RTX 5080 FE - will not ship, local sales only|Brand new sealed|$1200 cash only |\n\n&amp;nbsp;\n\nLocal is 94587. I'm happy to discount shipping for local sales.\n\n&amp;nbsp;\n\nPlease send a PM and not a chat request.
                        
                        Desired Model Response: 
                        RTX 5080 FE (Local Only) - $1200, Samsung 1TB NVME SSD - $60

                        ---

                        Following the example above, generate a title for the following information:
                        Include Terms: {include_terms}
                        Title: {title}
                        Body: {body}

                        Your response should contain only the generated title, and nothing else.
                    """
                }
            ]
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return title