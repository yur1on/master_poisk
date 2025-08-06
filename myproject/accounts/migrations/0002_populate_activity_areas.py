# accounts/migrations/0002_populate_activity_areas.py

from django.db import migrations

def create_areas(apps, schema_editor):
    ActivityArea = apps.get_model('accounts', 'ActivityArea')
    data = [
        # 1. Hair
        ('hair_hairdresser', 'Парикмахер-стилист', 'hair'),
        ('hair_colorist', 'Колорист', 'hair'),
        ('hair_care', 'Мастер по уходу за волосами', 'hair'),
        ('hair_extensions', 'Наращивание волос', 'hair'),
        ('hair_braider', 'Мастер по плетению', 'hair'),
        ('barber', 'Барбер', 'hair'),
        # 2. Nails
        ('manicure', 'Мастер маникюра', 'nails'),
        ('pedicure', 'Мастер педикюра', 'nails'),
        ('nail_designer', 'Нейл-дизайнер', 'nails'),
        ('nail_extensions', 'Наращивание ногтей', 'nails'),
        ('hand_foot_care', 'Уход за руками и ногами', 'nails'),
        # 3. Cosmetology
        ('esthetician', 'Эстетический косметолог', 'cosmetology'),
        ('device_cosmetologist', 'Аппаратный косметолог', 'cosmetology'),
        ('injection_cosmetologist', 'Инъекционный', 'cosmetology'),
        ('medical_cosmetologist', 'Медицинский косметолог', 'cosmetology'),
        # 4. Makeup
        ('makeup_artist', 'Визажист', 'makeup'),
        ('permanent_makeup', 'Перманентный макияж', 'makeup'),
        # 5. Brows & Lashes
        ('brow_master', 'Мастер-бровист', 'brows_lashes'),
        ('lash_master', 'Лашмейкер', 'brows_lashes'),
        ('lash_tint', 'Окрашивание ресниц', 'brows_lashes'),
        # 6. Epilation
        ('sugaring', 'Шугаринг', 'epilation'),
        ('waxing', 'Восковая депиляция', 'epilation'),
        ('laser_epilation', 'Лазерная эпиляция', 'epilation'),
        ('electroepilation', 'Электроэпиляция', 'epilation'),
        # 7. Body care
        ('massage', 'Массаж', 'body'),
        ('spa_specialist', 'SPA-процедуры', 'body'),
        ('body_contouring', 'Аппаратная коррекция фигуры', 'body'),
        # 8. Tattoo & Piercing
        ('tattoo_artist', 'Тату-мастер', 'tattoo_piercing'),
        ('piercer', 'Мастер пирсинга', 'tattoo_piercing'),
        # 9. Styling & Image
        ('stylist_imagemaker', 'Стилист-имиджмейкер', 'styling'),
        ('style_consultant', 'Консультант по стилю', 'styling'),
        # 10. Kids
        ('kids_hairdresser', 'Детский парикмахер', 'kids'),
        ('kids_manicure', 'Мастер детского маникюра', 'kids'),
        ('face_painter', 'Мастер аквагрима', 'kids'),
        # 11. Alternative
        ('aromatherapist', 'Ароматерапевт', 'alternative'),
        ('face_yoga', 'Йога для лица', 'alternative'),
        ('taping', 'Тейпирование лица и тела', 'alternative'),
        ('nutricosmetologist', 'Нутрикосметолог', 'alternative'),
        # 12. Education
        ('beauty_teacher', 'Преподаватель beauty-курсов', 'education'),
        ('beauty_coach', 'Бьюти-коуч', 'education'),
    ]
    for code, name, cat in data:
        ActivityArea.objects.update_or_create(code=code, defaults={'name': name, 'category': cat})

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(create_areas),
    ]

