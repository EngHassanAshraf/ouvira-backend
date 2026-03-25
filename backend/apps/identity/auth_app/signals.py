"""
Auth app signals.

Defines the `password_changed` Django signal, which is fired after any
successful password change (via reset or authenticated change).
The signal is sent OUTSIDE and AFTER the atomic transaction using
transaction.on_commit() — never from inside the transaction block.
"""

from django.dispatch import Signal

# Signal arguments: sender, user, ip (str), user_agent (str), timestamp (str ISO-8601)
password_changed = Signal()
