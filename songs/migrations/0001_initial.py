# Generated by Django 5.0.6 on 2024-05-23 11:37

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Song',
            fields=[
                ('id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('artist', models.CharField(max_length=255)),
                ('lyrics', models.TextField()),
                ('summary', models.TextField()),
                ('hash_key', models.CharField(max_length=255)),
            ],
            options={
                'db_table': 'songs',
            },
        ),
    ]
