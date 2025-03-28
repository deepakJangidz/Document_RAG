# Generated by Django 5.1.7 on 2025-03-24 13:30

import django.contrib.postgres.indexes
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0002_rename_created_by_document_uploaded_by'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='document',
            name='title',
            field=models.CharField(db_index=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='document',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='documentchunk',
            name='chunk_id',
            field=models.CharField(db_index=True, max_length=200),
        ),
        migrations.AddIndex(
            model_name='document',
            index=models.Index(fields=['created_at'], name='documents_d_created_3b0a51_idx'),
        ),
        migrations.AddIndex(
            model_name='document',
            index=models.Index(fields=['updated_at'], name='documents_d_updated_00a831_idx'),
        ),
        migrations.AddIndex(
            model_name='document',
            index=models.Index(fields=['uploaded_by'], name='documents_d_uploade_6455fb_idx'),
        ),
        migrations.AddIndex(
            model_name='documentchunk',
            index=models.Index(fields=['chunk_id'], name='documents_d_chunk_i_9a08ac_idx'),
        ),
        migrations.AddIndex(
            model_name='documentchunk',
            index=django.contrib.postgres.indexes.GinIndex(fields=['embeddings'], name='documents_d_embeddi_ee1f1c_gin'),
        ),
    ]
