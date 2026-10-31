def normalize_merchant(merchant):
    return ' '.join((merchant or '').lower().split())
