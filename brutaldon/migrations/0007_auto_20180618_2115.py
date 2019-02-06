# Generated by Django 2.0.6 on 2018-06-19 01:03

from django.db import migrations

def set_up_default_themes(apps, schema_editor):
    Theme = apps.get_model('brutaldon', 'Theme')
    default = Theme(name="default",
                    main_css="css/bulma.min.css",
                    tweaks_css="css/brutaldon.css",
                    is_brutalist=False)
    default.save()
    dark = Theme(name="default dark",
                 main_css="css/bulmaswatch-darkly.min.css",
                 tweaks_css="css/brutaldon-dark.css",
                 is_brutalist=False)
    dark.save()
    lux = Theme(name="Lux",
                    main_css="css/bulmaswatch-lux.min.css",
                    tweaks_css="css/brutaldon.css",
                    is_brutalist=False)
    lux.save()
    brutalism = Theme(name="FULLBRUTALISM",
                      main_css="css/fullbrutalism.css",
                      is_brutalist=True)
    brutalism.save()
    brutstrap = Theme(name="Brutstrap",
                      main_css="css/brutstrap.css",
                      is_brutalist=True,
                      tweaks_css="css/brutstrap-tweaks.css")
    brutstrap.save()
    large = Theme(name="Minimalist Large", main_css="css/minimal-large.css",
                  is_brutalist=True)
    large.save()
    vt240 = Theme(name="vt240 amber", main_css="css/vt240don-amber.css",
                  is_brutalist=True)
    vt240.save()
    vt240_green = Theme(name="vt240 green", main_css="css/vt240don-green.css",
                        is_brutalist=True)
    vt240_green.save()
    minimal = Theme(name="No styling at all", main_css=None, is_brutalist=True)
    minimal.save()

def delete_themes(apps, schema_editor):
    Theme = apps.get_model('brutaldon' 'Theme')
    for theme in Theme.objects.all():
        theme.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('brutaldon', '0006_auto_20180618_2112'),
    ]

    operations = [
        migrations.RunPython(set_up_default_themes, delete_themes)
    ]
