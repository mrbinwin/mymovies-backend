from django.db import models


class SearchRequest(models.Model):
    """
    The model represents search requests from mobile app

    """

    id = models.AutoField(primary_key=True)
    ip = models.CharField(max_length=255, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    create_date = models.DateTimeField('create datetime', auto_now_add=True)
    search_query = models.TextField(blank=True)

    class Meta:
        db_table = "search_request"
        ordering = ('-id',)
