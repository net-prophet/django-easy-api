# Generated by Django 3.0.2 on 2020-01-10 07:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('widgets', '0003_auto_20180804_0143'),
        ('customers', '0003_auto_20180804_0143'),
        ('purchases', '0003_auto_20180804_0143'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='purchase',
            name='items',
        ),
        migrations.AlterField(
            model_name='purchase',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='purchases', to='customers.Customer'),
        ),
        migrations.CreateModel(
            name='PurchaseItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('purchase', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='purchases.Purchase')),
                ('widget', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='widgets.Widget')),
            ],
        ),
    ]
