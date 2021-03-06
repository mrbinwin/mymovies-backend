# Generated by Django 2.2.1 on 2019-11-17 18:49

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SearchRequest',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('ip', models.CharField(blank=True, max_length=255)),
                ('user_agent', models.CharField(blank=True, max_length=255)),
                ('create_date', models.DateTimeField(auto_now_add=True, verbose_name='create datetime')),
            ],
            options={
                'db_table': 'search_request',
            },
        ),
    ]
