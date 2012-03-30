from django.db.models.fields.files import FileField

from easy_thumbnails import signals
from easy_thumbnails.alias import aliases


def find_uncommitted_filefields(sender, instance, **kwargs):
    """
    A pre_save signal handler which attaches an attribute to the model instance
    containing all uncommitted ``FileField``s, which can then be used by the
    :func:`signal_committed_filefields` post_save handler.
    """
    uncommitted = instance._uncommitted_filefields = []
    for field in sender._meta.fields:
        if isinstance(field, FileField):
            if not getattr(instance, field.name)._committed:
                uncommitted.append(field.name)


def signal_committed_filefields(sender, instance, **kwargs):
    """
    A post_save signal handler which sends a signal for each ``FileField`` that
    was committed this save.
    """
    for field_name in getattr(instance, '_uncommitted_filefields', ()):
        fieldfile = getattr(instance, field_name)
        # Don't send the signal for deleted files.
        if fieldfile:
            signals.saved_file.send_robust(sender=sender, fieldfile=fieldfile)


def save_aliases(fieldfile, **kwargs):
    """
    A saved_file signal handler which generates thumbnails for all non-global
    aliases matching the saved file.

    Only creates thumbnail sfor non-global
    """
    from easy_thumbnails.files import get_thumbnailer
    options = aliases.all(fieldfile, include_global=False)
    if options:
        thumbnailer = get_thumbnailer(fieldfile)
        for options in options.values():
            thumbnailer.get_thumbnail(options)
        return len(options)