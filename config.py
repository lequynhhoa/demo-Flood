#!/usr/bin/env python
"""Required credentials configuration."""

import ee

# The service account email address authorized by your Google contact.
# The process to set up a service account is described in the README.
EE_ACCOUNT = 'forest-demo@banded-water-179809.iam.gserviceaccount.com'

# The private key associated with your service account in Privacy Enhanced
# Email format (.pem suffix).  To convert a private key from the RSA format
# (.p12 suffix) to .pem, run the openssl command like this:
# openssl pkcs12 -in downloaded-privatekey.p12 -nodes -nocerts > privatekey.pem
# You can find more detailed instructions in the README.
EE_PRIVATE_KEY_FILE = 'credentials/privatekey.pem'

EE_CREDENTIALS = ee.ServiceAccountCredentials(EE_ACCOUNT, EE_PRIVATE_KEY_FILE)
