from playhouse.migrate import migrate, SqliteMigrator
from playhouse.reflection import Introspector

import models

migrator = SqliteMigrator(models.database)
introspector = Introspector.from_database(models.database)

generated_models = introspector.generate_models()

if 'image' in generated_models:
    if 'colors' not in generated_models['image']._meta.fields.keys():
        with models.database.transaction():
            migrate(
                migrator.add_column('image', 'colors', models.Image.colors)
            )
