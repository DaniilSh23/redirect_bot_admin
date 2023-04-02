# Generated by Django 4.1.7 on 2023-03-28 17:43

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('redirect_admin', '0009_alter_links_redirect_links_alter_links_short_links_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='payments',
            name='archived',
            field=models.BooleanField(default=False, verbose_name='В архиве'),
        ),
        migrations.AddField(
            model_name='payments',
            name='bill_expire_at',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Дата истекания счёта на оплату'),
            preserve_default=False,
        ),
    ]