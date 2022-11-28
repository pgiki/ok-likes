from django.dispatch import Signal

__all__ = (
    'object_liked',
    'object_unliked'
)


object_liked = Signal()
object_unliked = Signal()
