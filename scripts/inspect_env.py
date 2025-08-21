import os

def safe_display(s):
    if s is None:
        return 'None'
    # Build safe representation: replace non-printable/non-ascii with \xHH
    safe_chars = []
    for ch in s:
        try:
            o = ord(ch)
        except TypeError:
            # if not a character, show placeholder
            safe_chars.append('\\x??')
            continue
        if o < 128 and ch.isprintable():
            safe_chars.append(ch)
        else:
            safe_chars.append('\\x%02x' % o)
    safe_str = ''.join(safe_chars)
    # Provide masked preview
    if len(s) > 6:
        preview = s[:2] + '...' + s[-2:]
        preview_safe = ''.join([c if ord(c) < 128 and c.isprintable() else '\\x%02x' % ord(c) for c in preview])
        return f"{preview_safe} (len={len(s)})"
    return f"{safe_str} (len={len(s)})"

vars_to_check = ['DATABASE_URL','DB_HOST','DB_NAME','DB_USER','DB_PASSWORD','PGPASSWORD','PGCLIENTENCODING']
for name in vars_to_check:
    val = os.getenv(name)
    try:
        print(f"{name} -> {safe_display(val)}")
    except Exception as e:
        print(f"{name} -> ERROR reading value: {e}")

# Also print Django DATABASES setting file path if available
print('\nAdditional: attempting to show DATABASES setting from Django settings (masked)')
try:
    import django
    from django.conf import settings
    if not settings.configured:
        print('Django settings not configured in this environment')
    else:
        db = settings.DATABASES.get('default')
        if db:
            safe_db = {k: ('****' if k.lower() in ('password','passwd') else (db[k] if isinstance(db[k], str) else str(db[k]))) for k in db}
            print('DATABASES.default ->', safe_db)
        else:
            print('DATABASES.default not set')
except Exception as e:
    print('Could not import Django settings:', str(e))
