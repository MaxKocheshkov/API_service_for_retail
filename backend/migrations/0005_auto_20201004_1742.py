# Generated by Django 2.2.3 on 2020-10-04 14:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0004_auto_20201004_1716'),
    ]

    operations = [
        migrations.AddField(
            model_name='shop',
            name='filename',
            field=models.FileField(null=True, upload_to='data/'),
        ),
        migrations.AlterField(
            model_name='shop',
            name='url',
            field=models.CharField(blank=True, max_length=120, null=True),
        ),
    ]
