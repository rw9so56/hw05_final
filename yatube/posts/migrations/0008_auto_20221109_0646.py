# Generated by Django 2.2.16 on 2022-11-09 03:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0007_auto_20221107_0154'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='image',
            field=models.ImageField(blank=True, help_text='Изображение', null=True, upload_to='posts/', verbose_name='Картинка'),
        ),
    ]
