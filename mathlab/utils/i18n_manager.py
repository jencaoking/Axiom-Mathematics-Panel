import json
import os

DEFAULT_LANGUAGE = 'en'
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'zh': '中文'
}

class I18nManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(I18nManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self.current_language = DEFAULT_LANGUAGE
        self.translations = {}
        self._load_translations()
    
    def _load_translations(self):
        locale_dir = os.path.join(os.path.dirname(__file__), '..', 'locale')
        
        for lang_code in SUPPORTED_LANGUAGES.keys():
            file_path = os.path.join(locale_dir, f'{lang_code}.json')
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.translations[lang_code] = json.load(f)
                except Exception as e:
                    print(f'Error loading translation file {file_path}: {e}')
    
    def set_language(self, lang_code):
        if lang_code in SUPPORTED_LANGUAGES:
            self.current_language = lang_code
            return True
        return False
    
    def get_language(self):
        return self.current_language
    
    def get_supported_languages(self):
        return SUPPORTED_LANGUAGES
    
    def t(self, key, *args, **kwargs):
        keys = key.split('.')
        value = self.translations.get(self.current_language, {})
        
        for k in keys:
            value = value.get(k, None)
            if value is None:
                return key
        
        if args:
            value = value.format(*args)
        elif kwargs:
            value = value.format(**kwargs)
        
        return value

_i18n = None

def get_i18n():
    global _i18n
    if _i18n is None:
        _i18n = I18nManager()
    return _i18n

def t(key, *args, **kwargs):
    return get_i18n().t(key, *args, **kwargs)