from django.apps import AppConfig


class BookclubConfig(AppConfig):
    name = 'bookclub'
    
    def ready(self):
        import bookclub.signals
