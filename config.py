import os
import sys

import yaml
import praw
import prawcore

import ai
from lib import AlertLevel

_CONFIG_PATH = os.getenv("RPN_CONFIG", "config.yaml")

YAML_KEY_APPRISE = "apprise"

YAML_KEY_AI = "openai"
YAML_KEY_CLIENT = "client"
YAML_KEY_SECRET = "secret"
YAML_KEY_AGENT = "agent"

YAML_KEY_REDDIT = "reddit"
YAML_KEY_SUBREDDITS = "subreddits"
YAML_KEY_SUBREDDITS_INCLUDE = "include"
YAML_KEY_SUBREDDITS_EXCLUDE = "exclude"

class AIConfig:
    def __init__(self, ai_config: dict[str, str]):
        self._url = ai_config[YAML_KEY_CLIENT]
        self._model = ai_config[YAML_KEY_AGENT]

        self._client = ai.Client(
            url=self._url,
            api_key=ai_config[YAML_KEY_SECRET],
            model=self._model,
        )

    @property
    def client(self):
        return self._client
    
    def __str__(self):
        return f"""
            AIConfig:
            Url: {self._url}
            Model: {self._model}
        """

class SubredditConfig:
    def __init__(self, subreddit_config):
        self._subreddit_config = {k.lower(): v for k, v in subreddit_config.items()}
    
    @property
    def subreddits(self) -> set[str]:
        return self._subreddit_config.keys()
    
    def include_terms(self, subreddit: str) -> list[str]:
        return self._subreddit_config[subreddit.lower()].get(YAML_KEY_SUBREDDITS_INCLUDE, [])
    
    def exclude_terms(self, subreddit: str) -> list[str]:
        return self._subreddit_config[subreddit.lower()].get(YAML_KEY_SUBREDDITS_EXCLUDE, [])
    
    def __str__(self):
        sub_str = """
            {subreddit}: 
                Include Terms: {include_terms}, 
                Exclude Terms: {exclude_terms}
        """
        return f"""
            Subreddit Config: 
            {[sub_str.format(subreddit = sub, include_terms = self.include_terms(sub), exclude_terms = self.exclude_terms(sub)) for sub in self.subreddits]}
        """
        

class RedditConfig:
    def __init__(self, reddit_config: dict[str, str]):
        self._cid = reddit_config[YAML_KEY_CLIENT]
        secret = reddit_config[YAML_KEY_SECRET]
        self._agent = reddit_config[YAML_KEY_AGENT]

        self._client = praw.Reddit(client_id=self._cid, client_secret=secret, user_agent=self._agent)
        self._subreddits = SubredditConfig(reddit_config[YAML_KEY_SUBREDDITS])
        self._validate_subreddits()

    @property
    def client(self) -> praw.Reddit:
        return self._client
    
    @property
    def sub_config(self) -> SubredditConfig:
        return self._subreddits
    
    def __str__(self):
        return f"""
            Reddit Config
            Client ID: {self._cid}
            Agent: {self._agent}

            Client: {self._client}
            
            Subreddits
            {self.sub_config}
        """
    
    def _validate_subreddits(self):
        """Validate subreddits."""
        for sub in self.sub_config.subreddits:
            try:
                self._client.subreddit(sub).id

            except prawcore.exceptions.Redirect:
                sys.exit("Invalid Subreddit: " + sub)

            except (praw.exceptions.PRAWException,
                    prawcore.exceptions.PrawcoreException) as exception:
                print("Reddit API Error: ")
                print(exception)


class AlertConfig:
    def __init__(self, alert_config: dict[str, list[str]]):
        self._alert_config = alert_config

    def get(self, alert_level: AlertLevel) -> list[str]:
        match alert_level:
            case AlertLevel.NOTIFY:
                return self.notify
            case AlertLevel.FILTER:
                return self.filter
            case AlertLevel.ERROR:
                return self.error
            case _:
                raise ValueError(f"Received unsupported alert level: {alert_level}")

    @property
    def notify(self) -> list[str]:
        return self._alert_config.get(AlertLevel.NOTIFY, [])
    
    @property
    def filter(self) -> list[str]:
        return self._alert_config.get(AlertLevel.FILTER, [])
    
    @property
    def error(self) -> list[str]:
        return self._alert_config.get(AlertLevel.ERROR, [])
    
    def __str__(self):
        return f"AlertConfig(notify={self.notify}, filter={self.filter}, error={self.error})"

def load_config() -> tuple[RedditConfig, AIConfig, AlertConfig]:
    """Returns application configuration."""

    # Check if config file exists
    if not os.path.exists(_CONFIG_PATH):
        sys.exit("Missing config file: " + _CONFIG_PATH)
    print("Using config file: " + _CONFIG_PATH)

    config = _get_config()
    reddit = RedditConfig(config[YAML_KEY_REDDIT])
    ai = AIConfig(config[YAML_KEY_AI])
    alert = AlertConfig(config[YAML_KEY_APPRISE])

    _print_config(reddit, ai, alert)
    return reddit, ai, alert


def _get_config():
    # Load config into memory
    with open(_CONFIG_PATH, "r", encoding="utf-8") as config_yaml:
        config = None

        try:
            config = yaml.safe_load(config_yaml)

        except yaml.YAMLError as exception:
            if hasattr(exception, "problem_mark"):
                mark = exception.problem_mark # pylint: disable=no-member
                print(f"Invalid yaml, line {mark.line + 1}, column {mark.column + 1}")

            sys.exit("Invalid config: failed to parse yaml")

        if not config:
            sys.exit("Invalid config: empty file")

        return config


def _print_config(reddit: RedditConfig, ai: AIConfig, alert: AlertConfig):
    """Print the loaded configuration"""

    print("Monitoring Reddit for:")
    print(reddit)
    
    print("Using AI Model:")
    print(ai)

    print("Sending Alerts to:")
    print(alert)