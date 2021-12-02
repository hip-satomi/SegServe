#!/bin/bash --login
# The --login ensures the bash configuration is loaded,
# enabling Conda.

conda init bash
source /home/appuser/.bashrc

# Enable strict mode.
set -euo pipefail
# ... Run whatever commands ...

# Temporarily disable strict mode and activate conda:
set +euo pipefail
conda activate serve

# Re-enable strict mode:
set -euo pipefail

# exec the final command:
if [[ $# -eq 0 ]] ; then
    echo 'No arguments specified. So we start the default uvicorn server...'
    uvicorn --host 0.0.0.0 main:app
else
    exec "$@"
fi


#exec uvicorn --host 0.0.0.0 main:app