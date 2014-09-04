from django.core.urlresolvers import reverse
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.utils import timezone
from django.dispatch import receiver

from .managers import ThreadManager, MessageManager
from .utils import cached_attribute


class Thread(models.Model):
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="UserThread",
        )
    created = models.DateTimeField(
        auto_now_add=True,
        )
    latest_message_at = models.DateTimeField(
        auto_now_add=True,
        null=True, blank=True
        )

    objects = ThreadManager()

    class Meta:
        ordering = ("-latest_message_at",)

    def get_absolute_url(self):
        return reverse("messages_thread_detail", kwargs={"thread_id": self.pk})

    @property
    @cached_attribute
    def first_message(self):
        try:
            return self.messages.all()[0]
        except IndexError:
            return None

    @property
    @cached_attribute
    def latest_message(self):
        try:
            return self.messages.order_by("-sent_at")[0]
        except IndexError:
            return None

    @classmethod
    def ordered(cls, objs):
        """
        Returns the iterable ordered the correct way, this is a class method
        because we don"t know what the type of the iterable will be.
        """
        objs = list(objs)
        objs.sort(key=lambda o: o.latest_message.sent_at, reverse=True)
        return objs

    @property
    @cached_attribute
    def user_usernames(self):
        return self.users.values_list("username", flat=True)


class UserThread(models.Model):
    thread = models.ForeignKey(Thread)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)

    unread = models.BooleanField()
    deleted = models.BooleanField(default=False)


class Message(models.Model):
    thread = models.ForeignKey(
        Thread,
        related_name="messages",
        )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="sent_messages",
        )
    sent_at = models.DateTimeField(auto_now_add=True)
    content = models.TextField()

    objects = MessageManager()

    class Meta:
        ordering = ("sent_at",)

    def get_absolute_url(self):
        return self.thread.get_absolute_url()


@receiver(post_save, sender=Message)
def message_post_save_handler(instance, created, **kwargs):
    if created:
        thread = instance.thread
        instance.thread.latest_message_at = instance.sent_at
        thread.save()


@receiver(post_delete, sender=Message)
def message_post_delete_handler(instance, **kwargs):
    thread = instance.thread
    if (thread.latest_message_at is not None and
        instance.sent_at >= thread.latest_message_at):
        latest_message = thread.latest_message
        latest_message_at = None
        if latest_message is not None:
            latest_message_at = latest_message.sent_at
        thread.latest_message_at = latest_message_at
        thread.save()

