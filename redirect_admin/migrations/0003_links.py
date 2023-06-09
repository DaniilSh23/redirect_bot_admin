# Generated by Django 4.1.7 on 2023-03-25 17:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('redirect_admin', '0002_rename_vpnbotsettings_redirectbotsettings'),
    ]

    operations = [
        migrations.CreateModel(
            name='Links',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('link', models.CharField(max_length=1000, verbose_name='Ссылка')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('tlg_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='redirect_admin.tlguser', verbose_name='Автор')),
            ],
            options={
                'verbose_name': 'Ссылка',
                'verbose_name_plural': 'Ссылки',
                'ordering': ['-id'],
            },
        ),
    ]
