"""Init and utils."""

from zope.i18nmessageid import MessageFactory

_ = MessageFactory('genweb6.organs')
_GW = MessageFactory('genweb')


def initialize(context):
    """Initializer called when used as a Zope 2 product."""
    pass
