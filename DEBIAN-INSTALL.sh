
set -eou pipefail

if [ "$EUID" -ne 0 ]
  then echo "! Please run using sudo or as root."
  exit
fi

MQTT_PASSWORD="$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 13 ; echo '')"
DL_SERVER='http://192.168.1.1:8000'
TMPDIR="/tmp/thor"
INSTALLDIR="/opt/thor"
SERVICE_USER="thor"

echo '- Installing prerequisites...'

mkdir -p $TMPDIR
cd $TMPDIR

# Install prerequisites (Python, Python VENV, git, an MQTT broker [Might wright my own; Using mosquitto for now] and everything needed to pull the project from github)
apt-get update
apt-get install python3 python3-venv mosquitto mosquitto-clients git -y

echo '- Creating user '$SERVICE_USER' for thor'
if id "$SERVICE_USER" >/dev/null 2>&1; then
    echo "  ! User '$SERVICE_USER' already exists"
else
    useradd --shell /usr/sbin/nologin -M -r thor
fi

# Create configuration folder
echo '- Creating configuration folder at /etc/thor'
mkdir /etc/thor -p
touch /etc/thor/mosquitto_pwd
chown mosquitto:mosquitto /etc/thor/mosquitto_pwd

# Download mosquitto configuration
echo '  > Download mqtt configuration to /etc/mosquitto/conf.d/thor-mosquitto.conf'
wget -O /etc/mosquitto/conf.d/thor-mosquitto.conf "$DL_SERVER/preconfigured/thor-mosquitto.conf"

echo '  > Set password for mosquitto'
mosquitto_passwd -b /etc/thor/mosquitto_pwd thor "$MQTT_PASSWORD"
echo "$MQTT_PASSWORD"

echo '  > Restart mosquitto'
systemctl restart mosquitto

echo '- Downloading thor...'
if [[ ! -d "$INSTALLDIR" ]]; then
    git clone git@github.com:sisterbones/thor.git $INSTALLDIR
    cd $INSTALLDIR
    git submodule update --init --recursive
  else
    echo '  ! Git repo for thor already found. Updating repo...'
    cd $INSTALLDIR
    git pull --recurse-submodules
    cd ..
fi

echo '  > Create a virtual environment'
python3 -m venv $INSTALLDIR/.venv
source $INSTALLDIR/.venv/bin/activate

echo '  > Download dependencies'
pip install -r $INSTALLDIR/requirements.txt

echo '- Install systemd service'
echo '  > Download service'
wget -O /etc/systemd/system/thor.service $DL_SERVER/preconfigured/thor.service

echo '  > Reload daemon and start service'
systemctl daemon-reload
systemctl start thor.service
