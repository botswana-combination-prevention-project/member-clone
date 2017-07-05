from django.apps import AppConfig as DjangoApponfig
from django.conf import settings


class AppConfig(DjangoApponfig):
    name = 'member_clone'


if settings.APP_NAME == 'member_clone':

    from edc_map.apps import AppConfig as BaseEdcMapAppConfig

    class EdcMapAppConfig(BaseEdcMapAppConfig):
        verbose_name = 'Test Mappers'
        mapper_model = 'plot.plot'
        landmark_model = []
        verify_point_on_save = False
        zoom_levels = ['14', '15', '16', '17', '18']
        identifier_field_attr = 'plot_identifier'
        extra_filter_field_attr = 'enrolled'
