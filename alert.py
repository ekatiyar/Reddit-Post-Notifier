import apprise

from lib import AlertLevel
from config import AlertConfig

class Client:
    def __init__(self, config: AlertConfig):
        self.apprise_client = apprise.Apprise()
        self.config = config

        self._startup()

    def _startup(self):
        """Test All Alert Destinations"""
        for dest in AlertLevel:
            self._send_message("Test", f"This is a startup message at {dest.value} level", dest)

    def _send_message(self, title: str, body: str, dest: AlertLevel):
        apprise_config = self.config.get(dest)
        for conf in apprise_config:
            service = conf.split(":")[0]
            match service:
                case "ntfy":
                    raise RuntimeError("ntfy not supported")
                    # self.apprise_client.add(f"{conf}?click={self.config['reddit_url']}")
                case _:
                    self.apprise_client.add(conf)

        self.apprise_client.notify(
            title=title,
            body=body
        )
        self.apprise_client.clear()

    def notify(self, title, body):
        print(f"Sending regular notification: {title} <- {body}")
        self._send_message(title, body, AlertLevel.NOTIFY)

    def alert_error(self, exception):
        print("Sending error alert")
        self._send_message(
            title="[ERROR]",
            body=str(exception),
            dest=AlertLevel.ERROR
        )
    def notify_filtered(self, title, body):
        print(f"Sending filtered notification: {title} <- {body}")
        self._send_message(title=title, body=body, dest=AlertLevel.FILTER)
