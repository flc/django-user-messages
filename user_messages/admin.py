from django.contrib import admin

from . import models


def get_thread_display(thread):
    return u"ID: {} | {}".format(
        thread.id, ", ".join(thread.user_usernames)
        )


class MessageInline(admin.StackedInline):
    model = models.Message
    extra = 0
    max_num = 100
    raw_id_fields = ("sender",)


class MessageAdmin(admin.ModelAdmin):
    list_display = ("sent_at", "sender", "content", "thread_display")
    search_fields = ("=thread__id", "=sender__id", "=sender__username")
    raw_id_fields = ("sender", "thread")

    def thread_display(self, obj):
        return get_thread_display(obj.thread)
    thread_display.short_description = "Thread"
    thread_display.admin_order_field = "thread__id"


class ThreadAdmin(admin.ModelAdmin):
    list_display = ("created", "latest_message_at","user_usernames_display")
    search_fields = ("=id",)
    inlines = [
        MessageInline
    ]

    def user_usernames_display(self, obj):
        return ", ".join(obj.user_usernames)
    user_usernames_display.short_description = "Users"


class UserThreadAdmin(admin.ModelAdmin):
    list_display = ("user", "thread_display", "deleted", "unread")
    search_fields = ("=user__id", "=user__username", "=thread__id")
    list_filter = ("deleted", "unread")
    raw_id_fields = ("user", "thread")

    def thread_display(self, obj):
        return get_thread_display(obj.thread)
    thread_display.short_description = "Thread"
    thread_display.admin_order_field = "thread__id"


admin.site.register(models.Message, MessageAdmin)
admin.site.register(models.Thread, ThreadAdmin)
admin.site.register(models.UserThread, UserThreadAdmin)

