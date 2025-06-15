import requests

def filter_thinking(response: str, thinking_tag = "thinking") -> str:
    return response.split(f"</{thinking_tag}>")[-1]

class Client:
    def __init__(self, url: str, api_key: str, model: str):
        self.url = url
        self.api_key = api_key
        self.model = model

    def _send_request(self, prompt: str) -> str:
        """Common method to handle the URL, headers, and processing the response."""
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
                        You are part of a notification system that messages users about new items for sale on reddit.
                        The user has opted-in to receive notifications about a set of specified "Include Terms" -
                        essentially a list of keywords corresponding to items they are interested in.

                        {prompt}
                    """
                }
            ]
        }
        print(f'Sending API Request: ')
        response = requests.post(url, headers=headers, json=data)
        print(f"Response from OpenAI API: {response.text}")
        if response.status_code == 200:
            return filter_thinking(response.json()['choices'][0]['message']['content'])
        else:
            return f"Error: {response.status_code} - {response.text}"

    def check_post_valid(self, title:str, body: str, include_terms: list[str]) -> bool:
        """Check if the user should be messaged about this post."""
        # This method is not implemented yet, but we can create a prompt for it
        prompt = f"""
            Determine if the user should be messaged about this post based on the include terms.

            Here's an example:
            Include Terms: [5080, ssd]
            Title: [USA-CA] [H] Z690I Strix, 16GB DDR4, 1 TB 990 Evo+, RTX 5080 FE, Nouvolo Aquanaut, N150, Samsung Tablet [W] Paypal, Cash
            Body: |Item|Condition|Price|\n|:-|:-|:-|\n|Asus Z690I Strix - only includes what is visible in the pictures, specifically missing the SATA add on card|Used|$140 shipped|\n|Samsung 990 Evo Plus 1TB Gen 4 M.2 NVME SSD|Brand new sealed|$60 shipped |\n|Corsair DDR4 2x8GB (16GB) 3000MHz [Amazon link](https://www.amazon.com/dp/B0134EW7G8)|Brand new sealed|$25 shipped |\n|Corsair XG7 waterblock + backplate for Asus 3090TI cards - this block has been modified to fit on the 4090 TUF OG as well. Just had to dremel out a few bits. The modifications are invisible once the block is installed. See: https://imgur.com/a/I9QltNV |Used|$60 shipped|\n|Hanjiang 240mm radiator (17mm thick for SFF builds)|Used|$50 shipped|\n|Nouvolo Aquanaut Extreme w/ DDC pump|Used|$80 shipped|\n|Samsung S7 FE Tablet 128GB SM-T733 - like new condition, this thing has mostly just been sitting around unused|Used|$140 shipped |\n|N150 mini pc w/ 512GB/16GB -  [BAPCS link](https://www.reddit.com/r/buildapcsales/comments/1kvzrof/prebuilt_e3_mini_pc_intel_n150_16gb_ddr4_ram/) - I bought this because it was a steal but didn't end up having a good use for it. Opened it to make sure I was actually getting a PC, but never powered on. Just offering to pass on a deal before I return it.|New open box|$80 cash only|\n|RTX 5080 FE - will not ship, local sales only|Brand new sealed|$1200 cash only |\n\n&amp;nbsp;\n\nLocal is 94587. I'm happy to discount shipping for local sales.\n\n&amp;nbsp;\n\nPlease send a PM and not a chat request.

            Desired Model Response:
            True

            Second Example:
            Include Terms: [iphone 14]
            (Same title, body as first example)

            Desired Model Response:
            False

            You should not notify the user if the post is for buying the referenced item, as the
            user is only interested in posts that are selling the "include terms"

            Third Example:
            Include Terms: [5080]
            Title: [USA-IN][H] Paypal, Cash [W] 5080 FE
            Body: Looking for a 5080 FE for local pickup near 47906. Willing to drive up to an hour and a half. Thanks!\n\n  \nBOUGHT from u/TWISM1977

            Desired Model Response:
            False

            ---

            Following the example above, return either True or False based on whether the post should be filtered out:
            Include Terms: {include_terms}
            Title: {title}
            Body: {body}

            Your response should contain only True or False, and nothing else.
        """
        return 'true' in self._send_request(prompt).lower()

    def generate_title(self, title: str, body: str, include_terms: list[str]) -> str:
        """Generate a title for the post that only contains relevant info (item, price, etc.)."""
        prompt = f"""
            Create a summary alert title for the given reddit post and "Include Terms". The user only
            cares about relevant info (price, location, local vs shipping price) for the Include Terms:

            Here's an example:
            Include Terms: [5080, ssd]
            Title: [USA-CA] [H] Z690I Strix, 16GB DDR4, 1 TB 990 Evo+, RTX 5080 FE, Nouvolo Aquanaut, N150, Samsung Tablet [W] Paypal, Cash
            Body: Timestamps: |Item|Condition|Price|\n|:-|:-|:-|\n|Asus Z690I Strix - only includes what is visible in the pictures, specifically missing the SATA add on card|Used|$140 shipped|\n|Samsung 990 Evo Plus 1TB Gen 4 M.2 NVME SSD|Brand new sealed|$60 shipped |\n|Corsair DDR4 2x8GB (16GB) 3000MHz [Amazon link](https://www.amazon.com/dp/B0134EW7G8)|Brand new sealed|$25 shipped |\n|Corsair XG7 waterblock + backplate for Asus 3090TI cards - this block has been modified to fit on the 4090 TUF OG as well. Just had to dremel out a few bits. The modifications are invisible once the block is installed. See: https://imgur.com/a/I9QltNV |Used|$60 shipped|\n|Hanjiang 240mm radiator (17mm thick for SFF builds)|Used|$50 shipped|\n|Nouvolo Aquanaut Extreme w/ DDC pump|Used|$80 shipped|\n|Samsung S7 FE Tablet 128GB SM-T733 - like new condition, this thing has mostly just been sitting around unused|Used|$140 shipped |\n|N150 mini pc w/ 512GB/16GB -  [BAPCS link](https://www.reddit.com/r/buildapcsales/comments/1kvzrof/prebuilt_e3_mini_pc_intel_n150_16gb_ddr4_ram/) - I bought this because it was a steal but didn't end up having a good use for it. Opened it to make sure I was actually getting a PC, but never powered on. Just offering to pass on a deal before I return it.|New open box|$80 cash only|\n|RTX 5080 FE - will not ship, local sales only|Brand new sealed|$1200 cash only |\n\n&amp;nbsp;\n\nLocal is 94587. I'm happy to discount shipping for local sales.\n\n&amp;nbsp;\n\nPlease send a PM and not a chat request.

            Desired Model Response:
            RTX 5080 FE (Local Only) - $1200, Samsung 1TB NVME SSD - $60

            ---

            Following the example above, generate a title for the following information:
            Include Terms: {include_terms}
            Title: {title}
            Body: {body}

            Your response should contain only the generated title, and nothing else.
        """
        return self._send_request(prompt)
