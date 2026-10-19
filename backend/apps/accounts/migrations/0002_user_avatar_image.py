from django.db import migrations, models

import apps.accounts.avatar


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='avatar_image',
            field=models.ImageField(blank=True, null=True, upload_to=apps.accounts.avatar.avatar_upload_path),
        ),
    ]
