# Copyright 2016 The Android Open Source Project
#
# This software is licensed under the terms of the GNU General Public
# License version 2, as published by the Free Software Foundation, and
# may be copied, distributed, and modified under those terms.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

"""Site specific configuration to allow easy testing / site migration"""


import os
import os.path


GCLOUD_PROJECT_ID = 'GCLOUD_PROJECT_ID'
GCLOUD_BQ_DATASET_ID = 'GCLOUD_BQ_DATASET_ID'
GCLOUD_BQ_WORKSPACE_DATASET_ID = 'GCLOUD_BQ_WORKSPACE_DATASET_ID'
IS_PROD = 'IS_PROD'
def setup(root_dir):
    """Sets up various site-specific stuff.

    Sets defaults for developer machines. See comments below for specific things
    you need to provide at site-of-use.

    Args:
        root_dir: Root directory where these scripts live.
    Returns: dict.
    """
    config = {}

    # On developer machines, drop your personal gcloud credentials in the
    # current directory. See XXX on how to obtain these credentials.
    # On buildbot, this file should contain the credentials for the service
    # account in use.
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(
            root_dir, 'GOOGLE_APPLICATION_CREDENTIALS.json')

    # Create an empty file called 'PROD_TAG' in the current directory ON
    # BUILDBOT ONLY. This switches the scripts into prod mode, targetting real
    # buckets, etc.
    config[IS_PROD] = os.path.exists(os.path.join(root_dir, 'PROD_TAG'))

    if config[IS_PROD]:
        raise RuntimeError('TODO(pprabhu) Verify these.')
        config[GCLOUD_PROJECT_ID] = 'android-devtools-lldb-build'
        config[GCLOUD_BQ_DATASET_ID] = 'emu_build'
        config[GCLOUD_BQ_WORKSPACE_DATASET_ID] = 'emu_build_ws'
    else:
        config[GCLOUD_PROJECT_ID] = 'google.com:android-devtools-emulator-1307'
        config[GCLOUD_BQ_DATASET_ID] = 'developer_scratch'
        config[GCLOUD_BQ_WORKSPACE_DATASET_ID] = 'developer_scratch_ws'

    return config
