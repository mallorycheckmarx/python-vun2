class AnalyticsProvider(object):
    """Provider for sending events to an analytics platform

    """

    def init(self):
        """
        Does overall provider initialization

        No return value
        """
        raise NotImplementedError

    def new_event(self):
        """Creates a new event to send to the analytics provider

        Returns an Event object
        """
        raise NotImplementedError

    def close(self):
        """Finishes sending any in-flight events to the analytics provider

        No return value
        """
        raise NotImplementedError


class AnalyticsEvent(object):
    """An individual event to be sent to the analytics provider

    """

    def add_field(self, key, value):
        """Adds a key/value pair to the event.

        No return value
        """
        raise NotImplementedError

    def send(self):
        """Sends the event to the provider

        No return value
        """
        raise NotImplementedError


class AnalyticsSendError(Exception):
    """SendError exception gets raised when an event fails to send to the
    provider

    """
