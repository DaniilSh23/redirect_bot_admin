# Generated by Django 4.1.7 on 2023-04-20 07:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('redirect_admin', '0013_alter_links_short_link_service'),
    ]

    operations = [
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_type', models.CharField(choices=[('replenishment', 'пополнение'), ('write-off', 'списание')], max_length=13, verbose_name='Тип транзакции')),
                ('transaction_datetime', models.DateTimeField(auto_now_add=True, verbose_name='Дата и время транзакции')),
                ('amount', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Сумма')),
                ('description', models.TextField(max_length=250, null=True, verbose_name='Описание')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='redirect_admin.tlguser', verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Транзакция',
                'verbose_name_plural': 'Транзакции',
                'ordering': ['-id'],
            },
        ),
    ]