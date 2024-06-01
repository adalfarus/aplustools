# myne __init__

# Expected consent string
REQUIRED_CONSENT = """
I, the user, acknowledge that this software is provided "as is" without any warranties or guarantees of any kind, either express or implied.
By using this software, I assume all risks associated with its use and understand that I am solely responsible for any damage or loss that may occur.
I hereby release the developer, the distributor, and all affiliated parties from any and all liability for any claims, damages, or other legal actions, whether foreseeable or unforeseeable,
that may arise from the use or misuse of this software. I understand and accept these terms unconditionally.
"""

# Variable to store consent status
_user_consented = False


def set_consent(consent):
    global _user_consented
    if consent == REQUIRED_CONSENT:
        _user_consented = True
    else:
        raise ValueError("Consent not accepted. You must set the CONSENT variable to the required legal string to use this package.")


def check_consent():
    if not _user_consented:
        raise ValueError("Access denied. You must call set_consent with the required legal string before using this package.")


from aplustools.package import LazyModuleLoader as _LazyModuleLoader

# Lazy loading modules
hasher = _LazyModuleLoader('aplustools.myne.hasher')
crypt = _LazyModuleLoader('aplustools.myne.crypt')



