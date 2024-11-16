
set -eou pipefail

if [ "$EUID" -ne 0 ]
  then echo "! Please run using sudo or as root."
  exit
fi

MQTT_PASSWORD="$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 13 ; echo '')"
DL_SERVER='http://192.168.1.1:3000'
TMPDIR="/tmp/thor"
INSTALLDIR="/opt/thor"
CONFIGDIR="/etc/thor"
VARDIR="/var/lib/thor"
SERVICE_USER="thor"

echo '- Installing prerequisites...'

mkdir -p $TMPDIR
cd $TMPDIR

# Install prerequisites (Python, Python VENV, git, an MQTT broker [Might wright my own; Using mosquitto for now] and everything needed to pull the project from github)
apt-get update
apt-get install python3 python3-venv python3-rich mosquitto mosquitto-clients redis-server git -y

echo '- Creating user '$SERVICE_USER' for thor'
if id "$SERVICE_USER" >/dev/null 2>&1; then
    echo "  ! User '$SERVICE_USER' already exists"
else
    useradd --shell /usr/sbin/nologin -M -r thor
fi

# Create configuration folder
echo "- Creating configuration folder at $CONFIGDIR"
mkdir $CONFIGDIR -p
touch $CONFIGDIR/mosquitto_pwd
chown mosquitto:mosquitto $CONFIGDIR/mosquitto_pwd

# Download mosquitto configuration
echo '  > Download mqtt configuration to /etc/mosquitto/conf.d/thor-mosquitto.conf'
wget -O /etc/mosquitto/conf.d/thor-mosquitto.conf "$DL_SERVER/preconfigured/thor-mosquitto.conf"

echo '  > Set password for mosquitto'
mosquitto_passwd -b /etc/thor/mosquitto_pwd thor "$MQTT_PASSWORD"

echo '  > Restart mosquitto'
systemctl restart mosquitto

echo '  > Create .env'
if [[ -f "$CONFIGDIR/.env" ]]; then
    # .env exists
    printf '    ! .env already exists. copying to %s/.env.backup' "$CONFIGDIR"
    mv $CONFIGDIR/.env $CONFIGDIR/.env.backup
fi

touch $CONFIGDIR/.env
{ printf "MQTT_BROKER=localhost\n"; printf "MQTT_USER=thor\n"; printf "MQTT_PASSWORD=%s\n" "$MQTT_PASSWORD"; } >> $CONFIGDIR/.env

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
echo '  > Download thor hub service'
wget -O /etc/systemd/system/thor.service $DL_SERVER/preconfigured/thor.service
echo '  > Download thor auto-discovery service'
wget -O /etc/systemd/system/thor-autodiscovery.service $DL_SERVER/preconfigured/thor-autodiscovery.service

echo '  > Reload daemon and start service'
systemctl daemon-reload
systemctl enable thor.service --now
systemctl enable thor-autodiscovery.service --now
