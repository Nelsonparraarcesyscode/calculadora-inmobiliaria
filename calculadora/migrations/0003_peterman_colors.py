from django.db import migrations


def aplicar_colores_peterman(apps, schema_editor):
    PdfConfig = apps.get_model('calculadora', 'PdfConfig')
    obj = PdfConfig.objects.filter(pk=1).first()
    if obj:
        # Solo migrar desde los colores antiguos por defecto, sin pisar cambios manuales.
        if obj.form_color_primario in ('#1e3a5f', ''):
            obj.form_color_primario = '#5D1314'
        if obj.form_color_secundario in ('#4a90d9', ''):
            obj.form_color_secundario = '#A2998F'
        if not obj.form_color_fondo:
            obj.form_color_fondo = '#FDEFD6'
        obj.save()


def revertir(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('calculadora', '0002_propiedad_alter_pdfconfig_options_and_more'),
    ]

    operations = [
        migrations.RunPython(aplicar_colores_peterman, revertir),
    ]
