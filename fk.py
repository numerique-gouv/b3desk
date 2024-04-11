import subprocess

from libfaketime import fake_time
from libfaketime import reexec_if_needed

reexec_if_needed(remove_vars=False)


with fake_time("2020-01-01 01:00:00"):
    process = subprocess.run("date", capture_output=True)
    print(process.stdout.decode())
