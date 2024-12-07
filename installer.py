
# Run after prerequisites are installed.
# Intended to be installed on Unix-based systems.

import argparse # Argument parsing
import os
import platform
import sys

# Detect Python version and don't allow anything older than Python 3.10.
if int(sys.version.split('.')[1]) <= 10:
    raise Exception('Python version {0} is not supported. Please update to Python 3.10 or newer.'.format(sys.version))

try:
    from rich.console import Console # Styling
    from rich.prompt import Prompt
except ModuleNotFoundError:
    raise ModuleNotFoundError('Rich is required for the installer to function. Please install it using \'pip install rich\'')

console = Console()

OS_SUPPORTED = False

# Argument parser
parser = argparse.ArgumentParser(
    prog='ThorInstaller',
    description='Helper script for installing the Hub portion of THOR',
)
parser.add_argument('-d', '--dry-run', action='store_true')
parser.add_argument('--ignore-os-check', action='store_true')
args = parser.parse_args()

DRY_RUN = args.dry_run
IGNORE_OS_CHECK = args.ignore_os_check

console.print('[bold]-*- THOR Installer -*-')
if DRY_RUN: console.print('[dim][cyan][~][/cyan] --dry-run passed. No changes will be made.')

# Attempt to detect the operating system
operating_system = {
    'system': platform.system(), # System is something like 'Linux', 'macOS' or 'Windows'.
    'friendly_name': platform.system(), # Something like 'Arch Linux' or 'Ubuntu', make sure to fall back on `system`
    'release': None, # Release is something like 'XP' (Windows XP) or '12' (Debian 12). MUST BE A STRING.
    'version': None # Something like 'SP1' (Windows 7 Service Pack 1)
}

distro_info = {}
try:
    # Try to get Linux distro information using the FreeDesktop specifications
    distro_info = platform.freedesktop_os_release()
    operating_system['friendly_name'] = distro_info.get('NAME', operating_system.get('system'))
    operating_system['release'] = distro_info.get('VERSION')
except Exception:
    # Otherwise just pull from the OS directly
    operating_system['release'] = platform.release()
    operating_system['version'] = platform.version()

architecture = platform.machine()

os_string = operating_system.get('friendly_name')
if operating_system.get('release'):
    os_string += ' ' + operating_system.get('release')

# Check if the OS is actually supported
if operating_system['system'] == 'Windows':
    # Windows 10 and newer is supported.
    # if int(operating_system['version'].split('.')[0]) >= 10:
    #     # Windows 10 and 11 are both NT version 10.
    #     OS_SUPPORTED = True
    OS_SUPPORTED = False
elif operating_system['system'] == 'Linux':
    # Supported Linux distros are Debian, Arch Linux and Ubuntu.
    supported_distros = ['ubuntu', 'debian', 'arch']
    distro_id = distro_info.get('ID')
    distro_id_like = distro_info.get('ID_LIKE', distro_id) # Give distro one last chance in case it's a fork or something
    version_id = distro_info.get('VERSION_ID')

    if (distro_id or distro_id_like) in supported_distros:
        # Ubuntu LTS 20.04 and newer is supported
        if (distro_id or distro_id_like) == 'ubuntu':
            if int(version_id.split('.')[0]) >= 20:
                OS_SUPPORTED = True
        elif (distro_id or distro_id_like) == 'debian':
            # Debian 11 and newer is supported.
            if int(version_id) >= 11:
                OS_SUPPORTED = True
        elif (distro_id or distro_id_like) == 'arch':
            OS_SUPPORTED = True

console.print(f'[ ] Running on {architecture} architecture.')
console.print(f'[{(OS_SUPPORTED and 'green') or 'red'}][{(OS_SUPPORTED and '✔') or '!'}] Detected operating system as {os_string}.[/{(OS_SUPPORTED and 'green') or 'red'}]')

if not OS_SUPPORTED:
    if not IGNORE_OS_CHECK:
        console.print('    [>] Your OS isn\'t supported. If you\'d like to continue anyway, please re-run this script with the [bold]--ignore-os-check[/bold] argument.')
        sys.exit(10)
    else:
        console.print('    [>] Your OS isn\'t supported, but you\'ve opted to ignore the OS check. Carrying on...')

# Check for existing configuration
PREVIOUS_CONFIG_EXISTS = False
console.print('[ ] Checking for existing configuration...')
if os.path.exists('/etc/thor/.env'): # Thor's configuration file (really environment variables but SHUSH
    PREVIOUS_CONFIG_EXISTS = True
    console.print('    [red][!] Found existing configuration!!')
else:
    console.print('    [ ] No existing config found. Creating...')

if not PREVIOUS_CONFIG_EXISTS:
    print()
    console.print('[!] If you\'re on this installer from the Debian Install Script, please leave all of these at their defaults.')
    MQTT_BROKER = Prompt.ask('[?] MQTT Broker', default='localhost')
