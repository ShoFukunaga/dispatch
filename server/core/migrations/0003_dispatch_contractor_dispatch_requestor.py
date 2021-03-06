# Generated by Django 4.0 on 2022-06-05 08:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_dispatch'),
    ]

    operations = [
        migrations.AddField(
            model_name='dispatch',
            name='contractor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='contractors', to='core.user'),
        ),
        migrations.AddField(
            model_name='dispatch',
            name='requestor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='requestors', to='core.user'),
        ),
    ]
