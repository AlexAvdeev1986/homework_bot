logger_config = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'formatter': {
            'format': (
                '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
            )
        }
    },

    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'formatter'
        },

        'file': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'formatter',
            'filename': 'debug.log',
            'mode': 'w'
        },
    },

    'loggers': {
        'bot': {
            'level': 'DEBUG',
            'handlers': ['console', 'file'],
            'propagate': False
        }
    },
}
