"""Stream new Reddit posts and notify for matching posts."""
import sys
import time

import praw
import prawcore

import config
import ai
from lib import AlertLevel
import alert

def main():
    """Run application."""
    print("Starting Reddit Post Notifier")
    reddit_config, ai_config, alert_config = config.load_config()
    
    reddit_client = reddit_config.client
    subreddits = reddit_config.sub_config

    ai_client = ai_config.client

    alert_client = alert.Client(alert_config)
    
    # Run tests using dummy objects
    print("Running tests...")
    from test import run_tests
    run_tests(alert_client, ai_client)
    print("Tests completed successfully\n")

    print("Going to stream submissions")
    stream_submissions(reddit_client, subreddits, alert_client, ai_client)


def stream_submissions(reddit: praw.Reddit, sub_config: config.SubredditConfig, alert_client: alert.Client, ai_client: ai.Client):
    """Monitor and process new Reddit submissions in given subreddits."""
    subs = sub_config.subreddits
    subs_joined = "+".join(subs)
    subreddits_group = reddit.subreddit(subs_joined)

    print("Monitoring begin")
    while True:
        try:
            for submission in subreddits_group.stream.submissions(pause_after=None, skip_existing=True):
                process_submission(submission, sub_config, alert_client, ai_client)

        except KeyboardInterrupt:
            sys.exit("\tStopping application, bye bye")

        except (praw.exceptions.PRAWException,
                prawcore.exceptions.PrawcoreException) as exception:
            print("Reddit API Error: ")
            print(exception)
            alert_client.alert_error(exception)            
            print("Pausing for 30 seconds...")
            time.sleep(30)

def process_submission(submission, sub_config: config.SubredditConfig, alert_client: alert.Client, ai_client: ai.Client):
    """Notify if given submission matches search."""

    print("checking submission: ")
    title = submission.title
    body = submission.selftext
    sub = submission.subreddit.display_name

    include_terms = sub_config.include_terms(sub)
    exclude_terms = sub_config.exclude_terms(sub)

    print("include terms: ", include_terms)
    print("exclude terms: ", exclude_terms)
    print("submission : ", submission, title)


    contains_included_term_title = not include_terms or any(term.lower() in title.lower() for term in include_terms)
    contains_excluded_term_title = exclude_terms and any(term.lower() in title.lower() for term in exclude_terms)

    contains_included_term_text = not include_terms or any(term.lower() in body.lower() for term in include_terms)
    contains_excluded_term_text = exclude_terms and any(term.lower() in body.lower() for term in exclude_terms)

    if not ((contains_included_term_title or contains_included_term_text) and not (contains_excluded_term_title or contains_excluded_term_text)):
        print("Submission non match")
    elif not ai_client.check_post_valid(title, body, include_terms):
        print("ai filtered")
        notify(title, alert_client, submission.permalink, AlertLevel.FILTER)
    else:
        print("submission match")

        summarized_title = ai_client.generate_title(title, body, include_terms)        
        if summarized_title == title:
            alert_client.alert_error("Title Generation Failed. Check logs")    
        else:
            print(f"summarized title: {summarized_title}")

        notify(summarized_title, alert_client, submission.permalink, AlertLevel.NOTIFY)

def notify(title: str, alert_client: alert.Client, submission_id: str, alert_level: AlertLevel):
    print(f"Sending apprise notification")

    reddit_url = "https://www.reddit.com" + submission_id
    body=f'\n---\nLink to Post: [{title}]({reddit_url})'
    
    match alert_level:
        case AlertLevel.NOTIFY:
            alert_client.notify(title, body)
        case AlertLevel.FILTER:
            alert_client.notify_filtered(title, body)
        case _:
            raise ValueError(f"Only send posts to {AlertLevel.NOTIFY} and {AlertLevel.FILTER}")
        


if __name__ == "__main__":
    main()
