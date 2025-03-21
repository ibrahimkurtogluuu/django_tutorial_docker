# Generated by Django 5.1.6 on 2025-03-17 11:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grc', '0003_remove_customer_first_name_remove_customer_last_name_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Sector',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
            ],
        ),
        migrations.RenameField(
            model_name='standard',
            old_name='standard_description',
            new_name='description',
        ),
        migrations.RenameField(
            model_name='standard',
            old_name='standard_name',
            new_name='name',
        ),
    ]
