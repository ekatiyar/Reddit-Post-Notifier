"""Test module for reddit post processing."""
from app import process_submission

class DummySubConfig:
    """Mock subreddit configuration for testing."""
    def __init__(self, include, exclude):
        self._include = include
        self._exclude = exclude
        
    def include_terms(self, sub):
        return self._include
        
    def exclude_terms(self, sub):
        return self._exclude

class DummySubmission:
    """Mock Reddit submission object for testing."""
    def __init__(self, title, body, sub_name, permalink):
        self.title = title
        self.selftext = body
        self.subreddit = self.DummySubreddit(sub_name)
        self.permalink = permalink
        
    class DummySubreddit:
        """Mock subreddit object."""
        def __init__(self, display_name):
            self.display_name = display_name

def run_tests(alert_client, ai_client):
    """Run test cases using dummy objects."""
    print("\n=== Running notification test ===")
    title = "[USA-DC] [H] NVIDIA RTX 3090 Ti Founders Edition (FE) [W] Local Cash or 5090"
    body = "I am selling one NVIDIA GeForce 3090 Ti Founders Edition (FE) GPU. Original owner. Used for AI/ML side projects here and there.\n\nAsking for $1,200 shipped to CONUS, $1150 local, or a 5090.\n\n[Timestamp Video](https://imgur.com/a/o3OXWUi)\n\n*Replacing an earlier post with a mistake in the title.*"
    
    # Create test submission and config
    test_submission = DummySubmission(title, body, "testsub", "/r/testsub/permalink")
    test_config = DummySubConfig(include=["3090"], exclude=[])
    
    # Process as real submission
    process_submission(test_submission, test_config, alert_client, ai_client)
    
    print("\n=== Running filter test ===")
    test_config = DummySubConfig(include=["5090"], exclude=[])
    process_submission(test_submission, test_config, alert_client, ai_client)