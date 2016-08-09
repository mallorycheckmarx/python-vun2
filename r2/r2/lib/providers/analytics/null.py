from r2.lib.providers.analytics import AnalyticsProvider
from r2.lib.providers.analytics import AnalyticsEvent


class NullAnalyticsProvider(AnalyticsProvider):
    """Provider for sending events to an analytics platform

    """

    def init(self):
        pass

    def new_event(self):
        return None

    def close(self):
        pass


class NullAnalyticsEvent(AnalyticsEvent):
    """An individual event to be sent to the analytics provider

    """

    def add_field(self, key, value):
        pass

    def send(self):
        pass
