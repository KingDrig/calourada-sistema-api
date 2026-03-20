from django.db import models
from django.utils import timezone


class TimestampedModel(models.Model):
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deletado_em__isnull=True)

    def all_with_deleted(self):
        return super().get_queryset()

    def deleted_only(self):
        return super().get_queryset().filter(deletado_em__isnull=False)


class SoftDeleteModel(models.Model):
    deletado_em = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.deletado_em = timezone.now()
        self.save()

    def hard_delete(self):
        super().delete()

    def restore(self):
        self.deletado_em = None
        self.save()
