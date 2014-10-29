from django.db.models import Manager

from .signals import message_sent
from .utils import get_m2m_exact_match


class ThreadManager(Manager):

    def inbox(self, user):
        return self.filter(
            userthread__user=user,
            userthread__deleted=False,
            )

    def unread(self, user):
        return self.inbox(user).filter(
            userthread__unread=True,
            )


class MessageManager(Manager):

    def new_reply(self, thread, user, content):
        msg = self.create(thread=thread, sender=user, content=content)
        thread.userthread_set.exclude(user=user).update(deleted=False, unread=True)
        message_sent.send(sender=self.model, message=msg, thread=thread, reply=True)
        return msg

    def new_message(self, from_user, to_users, content):
        from user_messages.models import Thread

        # remove duplicates if any
        to_users = set(to_users)
        if from_user in to_users:
            to_users.remove(from_user)

        try:
            # XXX performance
            user_ids = [u.id for u in to_users]
            user_ids.append(from_user.id)
            thread = get_m2m_exact_match(Thread, "users", user_ids)[0]
            reply = False
        except IndexError as e:
            thread = None
            reply = True

        if thread is None:
            # new thread
            thread = Thread.objects.create()
            for user in to_users:
                thread.userthread_set.create(user=user, deleted=False, unread=True)
            thread.userthread_set.create(user=from_user, deleted=False, unread=False)

        # create the message
        msg = self.create(thread=thread, sender=from_user, content=content)

        # send signal
        message_sent.send(sender=self.model, message=msg, thread=thread, reply=reply)

        return msg
