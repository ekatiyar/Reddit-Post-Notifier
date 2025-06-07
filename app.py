"""Stream new Reddit posts and notify for matching posts."""
import datetime
import os
import sys
import time

import apprise
import praw
import prawcore
import yaml

import ai

CONFIG_PATH = os.getenv("RPN_CONFIG", "config.yaml")
LOGGING = os.getenv("RPN_LOGGING", "FALSE")

YAML_KEY_APPRISE = "apprise"
YAML_KEY_REDDIT = "reddit"
YAML_KEY_AI = "openai"
YAML_KEY_SUBREDDITS = "subreddits"
YAML_KEY_SUBREDDITS_INCLUDE = "include"
YAML_KEY_SUBREDDITS_EXCLUDE = "exclude"
YAML_KEY_CLIENT = "client"
YAML_KEY_SECRET = "secret"
YAML_KEY_AGENT = "agent"


def main():
    """Run application."""
    print("Starting Reddit Post Notifier")
    config = get_config()
    reddit_config = config[YAML_KEY_REDDIT]
    ai_config = config[YAML_KEY_AI]

    subreddits = reddit_config[YAML_KEY_SUBREDDITS]
    apprise_client = apprise.Apprise()
    reddit_client = get_reddit_client(
        reddit_config[YAML_KEY_CLIENT],
        reddit_config[YAML_KEY_SECRET],
        reddit_config[YAML_KEY_AGENT]
    )
    ai_client = ai.Client(
        url=ai_config[YAML_KEY_CLIENT],
        api_key=ai_config[YAML_KEY_SECRET],
        model=ai_config[YAML_KEY_AGENT],
    )

    validate_subreddits(reddit_client, subreddits)

    print("Testing notification system: ")
    title = "[USA-DC] [H] NVIDIA RTX 3090 Ti Founders Edition (FE) [W] Local Cash or PayPal"
    body = "I am selling one NVIDIA GeForce 3090 Ti Founders Edition (FE) GPU. Original owner. Used for AI/ML side projects here and there.\n\nAsking for $1,200 shipped to CONUS, $1150 local.\n\n[Timestamp Video](https://imgur.com/a/o3OXWUi)\n\n*Replacing an earlier post with a mistake in the title.*"
    notify(apprise_client, ai_client.generate_title(title, body, ["3090"]), title, "")
    print("Notification sent.")

    print("going to stream submissions")
    stream_submissions(reddit_client, subreddits, apprise_client, ai_client)


def stream_submissions(reddit, subreddits, apprise_client, ai_client):
    """Monitor and process new Reddit submissions in given subreddits."""
    subs = subreddits.keys()
    subs_joined = "+".join(subs)
    subreddit = reddit.subreddit(subs_joined)

    print("Monitoring begin")
    while True:
        try:
            for submission in subreddit.stream.submissions(pause_after=None, skip_existing=True):
                process_submission(submission, subreddits, apprise_client, ai_client)

        except KeyboardInterrupt:
            sys.exit("\tStopping application, bye bye")

        except (praw.exceptions.PRAWException,
                prawcore.exceptions.PrawcoreException) as exception:
            print("Reddit API Error: ")
            print(exception)
            alert_error(apprise_client, exception)
            print("Pausing for 30 seconds...")
            time.sleep(30)

def alert_error(apprise_client, exception):
    """Send an alert to the apprise client."""
    configure_apprise_notifications(apprise_client, "")
    apprise_client.notify(title="[ERROR]", body=str(exception))
    apprise_client.clear()

def process_submission(submission, subreddits, apprise_client, ai_client):
    """Notify if given submission matches search."""

    print("checking submission: ")
    title = submission.title
    body = submission.selftext
    sub = submission.subreddit.display_name
    search_terms = subreddits[sub.lower()]

    include_terms = []
    exclude_terms = []

    if search_terms is not None:
        include_terms = search_terms.get(YAML_KEY_SUBREDDITS_INCLUDE) or []
        exclude_terms = search_terms.get(YAML_KEY_SUBREDDITS_EXCLUDE) or []

    contains_included_term_title = not include_terms or any(term.lower() in title.lower() for term in include_terms)
    contains_excluded_term_title = exclude_terms and any(term.lower() in title.lower() for term in exclude_terms)

    contains_included_term_text = not include_terms or any(term.lower() in body.lower() for term in include_terms)
    contains_excluded_term_text = exclude_terms and any(term.lower() in body.lower() for term in exclude_terms)

    print("include terms: ", include_terms)
    print("exclude terms: ", exclude_terms)
    print("submission : ", submission, title)

    if (contains_included_term_title or contains_included_term_text) and not (contains_excluded_term_title or contains_excluded_term_text):
        print("submission match")

        summarized_title = ai_client.generate_title(title, body, include_terms)
        print(f"summarized title: {summarized_title}")

        notify(apprise_client, summarized_title, title, body, submission.permalink)
        if LOGGING != "FALSE":
            print(datetime.datetime.fromtimestamp(submission.created_utc), " " + "r/" + sub + ": " + title + "\n" + submission.permalink)
    else:
        print("Submission non match")

def notify(apprise_client, gen_title, orig_title, submission_id):
    """Send apprise notification."""
    print(f"Sending apprise notification {gen_title} <- {orig_title}")
    reddit_url = "https://www.reddit.com" + submission_id
    configure_apprise_notifications(apprise_client, reddit_url)
    apprise_client.notify(
        title=gen_title,
        body=f'[{orig_title}]({reddit_url})',
    )
    apprise_client.clear()
    if gen_title == orig_title:
        alert_error(apprise_client, "Title Generation Failed. Check logs")


def get_reddit_client(cid, secret, agent):
    """Return PRAW Reddit instance."""
    return praw.Reddit(
        client_id=cid,
        client_secret=secret,
        user_agent=agent
    )


def configure_apprise_notifications(apprise_client, reddit_url):
    """Return Apprise instance."""
    config = get_config()
    apprise_config = config[YAML_KEY_APPRISE]
    for conf in apprise_config:
        service = conf.split(":")[0]
        match service:
            case "ntfy":
                apprise_client.add(f"{conf}?click={reddit_url}")
            case _:
                apprise_client.add(conf)

    return apprise_client


def get_config():
    """Returns application configuration."""
    check_config_file()
    config = load_config()
    return validate_config(config)


def check_config_file():
    """Check if config file exists."""
    if not os.path.exists(CONFIG_PATH):
        sys.exit("Missing config file: " + CONFIG_PATH)

    print("Using config file: " + CONFIG_PATH)


def load_config():
    """Load config into memory."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as config_yaml:
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


def validate_config(config):
    """Validate required config keys."""
    if YAML_KEY_REDDIT not in config or not isinstance(config[YAML_KEY_REDDIT], dict):
        sys.exit("Invalid config: missing reddit config")

    reddit = config[YAML_KEY_REDDIT]

    if YAML_KEY_CLIENT not in reddit or not isinstance(reddit[YAML_KEY_CLIENT], str):
        sys.exit("Invalid config: missing reddit -> client config")

    if YAML_KEY_SECRET not in reddit or not isinstance(reddit[YAML_KEY_SECRET], str):
        sys.exit("Invalid config: missing reddit -> secret config")

    if YAML_KEY_AGENT not in reddit or not isinstance(reddit[YAML_KEY_AGENT], str):
        sys.exit("Invalid config: missing reddit -> agent config")

    if YAML_KEY_SUBREDDITS not in reddit or not isinstance(reddit[YAML_KEY_SUBREDDITS], dict):
        sys.exit("Invalid config: missing reddit -> subreddits config")

    if YAML_KEY_APPRISE not in config or not isinstance(config[YAML_KEY_APPRISE], list):
        sys.exit("Invalid config: missing apprise config")

    print("Monitoring Reddit for:")

    subreddits = reddit[YAML_KEY_SUBREDDITS]
    print("")
    reddit[YAML_KEY_SUBREDDITS] = {k.lower(): v for k, v in subreddits.items()}
    print(config)
    return config


def validate_subreddits(reddit, subreddits):
    """Validate subreddits."""
    for sub in subreddits:
        try:
            reddit.subreddit(sub).id

        except prawcore.exceptions.Redirect:
            sys.exit("Invalid Subreddit: " + sub)

        except (praw.exceptions.PRAWException,
                prawcore.exceptions.PrawcoreException) as exception:
            print("Reddit API Error: ")
            print(exception)


if __name__ == "__main__":
    main()
