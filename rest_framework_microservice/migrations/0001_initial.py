# Generated by Django 4.0.3 on 2022-04-04 00:00

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Idp',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField()),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='idp', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddIndex(
            model_name='idp',
            index=models.Index(fields=['uuid'], name='rest_framew_uuid_a01bb5_idx'),
        ),
    ]
