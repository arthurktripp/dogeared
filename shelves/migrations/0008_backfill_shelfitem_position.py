from django.db import migrations


def backfill_positions(apps, schema_editor):
    Shelf = apps.get_model("shelves", "Shelf")
    ShelfItem = apps.get_model("shelves", "ShelfItem")

    for shelf in Shelf.objects.all():
        items = list(
            ShelfItem.objects.filter(shelf=shelf).order_by("added_at", "id")
        )
        for index, item in enumerate(items):
            item.position = index
        if items:
            ShelfItem.objects.bulk_update(items, ["position"])


class Migration(migrations.Migration):

    dependencies = [
        ("shelves", "0007_alter_userbook_finished_at"),
    ]

    operations = [
        migrations.RunPython(backfill_positions, migrations.RunPython.noop),
    ]
