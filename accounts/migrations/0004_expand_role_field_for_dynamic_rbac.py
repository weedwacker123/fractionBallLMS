"""
Expand the role field to support dynamic roles from Firestore.
- Increases max_length from 20 to 50 for custom role keys
- Removes choices constraint so any role key from Firestore is accepted
- No data migration needed — existing role strings remain valid
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_update_roles_to_registered_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                default='REGISTERED_USER',
                help_text='Role key from Firestore roles collection',
                max_length=50,
            ),
        ),
    ]
