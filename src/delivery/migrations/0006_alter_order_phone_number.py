# Generated by Django 4.2.11 on 2024-09-09 11:26

import phonenumber_field.modelfields
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("delivery", "0005_order_phone_number"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="phone_number",
            field=phonenumber_field.modelfields.PhoneNumberField(
                max_length=128, region=None
            ),
        ),
    ]
