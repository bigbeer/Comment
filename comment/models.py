from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class CommentManager(models.Manager):
    def all_parent_comments(self):
        return super(CommentManager, self).all().filter(parent=None)

    def filter_by_object(self, obj):
        content_type = ContentType.objects.get_for_model(obj.__class__)
        object_id = obj.id
        qs = super(CommentManager, self).filter(content_type=content_type, object_id=object_id).filter(parent=None)
        return qs

    def all_comments(self, obj):
        content_type = ContentType.objects.get_for_model(obj.__class__)
        object_id = obj.id
        qs = super(CommentManager, self).filter(content_type=content_type, object_id=object_id)
        return qs


class Comment(models.Model):
    user           = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
    parent         = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    content_type   = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id      = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    content        = models.TextField()
    posted_date    = models.DateTimeField(auto_now_add=True)
    edit_date      = models.DateTimeField(auto_now=True)

    objects = CommentManager()

    class Meta:
        ordering = ['-posted_date', ]

    def __str__(self):
        if self.parent is None:
            return f"comment by {self.user}: {self.content[:20]}"
        else:
            return f"reply by {self.user}: {self.content[:20]}"

    @property
    def replies(self):
        return Comment.objects.filter(parent=self).order_by('posted_date')

    @property
    def is_edited(self):
        return self.posted_date.timestamp()+1 < self.edit_date.timestamp()