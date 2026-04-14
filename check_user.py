from django_tenants.utils import schema_context
with schema_context('public'):
    from django.contrib.auth import get_user_model
    U = get_user_model()
    u = U.objects.get(username='root')
    print('locked_until:', u.locked_until)
    print('failed_attempts:', u.failed_login_attempts)
    for pw in ['Admin123!', 'Admin@2026!']:
        print('check', pw, ':', u.check_password(pw))
    # Reset to Admin123! regardless
    u.set_password('Admin123!')
    u.failed_login_attempts = 0
    u.locked_until = None
    u.save()
    print('Reset to Admin123!. Check:', u.check_password('Admin123!'))
