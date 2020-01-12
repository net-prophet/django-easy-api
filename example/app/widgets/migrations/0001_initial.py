# Generated by Django 2.2.9 on 2020-01-12 09:44

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import example.app.widgets.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=30)),
                ('state', models.CharField(blank=True, max_length=30)),
                ('gender', models.CharField(blank=True, max_length=1)),
                ('age', models.IntegerField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Purchase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sale_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('sale_price', models.FloatField(blank=True, default=0)),
                ('profit', models.FloatField(blank=True, default=0)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='purchases', to='widgets.Customer')),
            ],
        ),
        migrations.CreateModel(
            name='Store',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=30)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Widget',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(blank=True, max_length=30)),
                ('color', models.CharField(choices=[('black', 'Black'), ('blue', 'Blue'), ('brown', 'Brown'), ('green', 'Green'), ('orange', 'Orange'), ('red', 'Red'), ('red_orange', 'Red Orange'), ('sky_blue', 'Sky Blue'), ('violet', 'Violet'), ('white', 'White'), ('yellow', 'Yellow'), ('yellow_green', 'Yellow Green')], max_length=30)),
                ('size', models.CharField(choices=[('small', 'Small'), ('medium', 'Medium'), ('large', 'Large'), ('extra_large', 'Extra Large')], max_length=30)),
                ('shape', models.CharField(choices=[('rectangle', 'Rectangle'), ('ellipse', 'Ellipse'), ('diamond', 'Diamond'), ('trapezoid', 'Trapezoid'), ('parallelogram', 'Parallelogram'), ('triangle', 'Triangle'), ('circle', 'Circle')], max_length=30)),
                ('cost', models.FloatField(blank=True, default=0)),
                ('store', models.ForeignKey(default=example.app.widgets.models.default_store_id, on_delete=django.db.models.deletion.CASCADE, related_name='widgets', to='widgets.Store')),
            ],
        ),
        migrations.CreateModel(
            name='PurchaseItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('purchase', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='widgets.Purchase')),
                ('widget', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='widgets.Widget')),
            ],
        ),
    ]
