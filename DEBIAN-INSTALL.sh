
set -eou pipefail

if [ "$EUID" -ne 0 ]
  then echo "Please run using sudo or as root."
  exit
fi

MQTT_PASSWORD="$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 13 ; echo '')"

echo 'Installing prerequisites...'

mkdir -p /tmp/thor

cd /tmp/thor

# Install prerequisites (Python, Python VENV, an MQTT broker [Might wright my own; Using mosquitto for now] and everything needed to pull the project from github)
apt-get update
apt-get install mosquitto mosquitto-clients -y

echo 'Creating user for thor'
useradd --shell /usr/sbin/nologin -M -r thor

# Create configuration folder
echo 'Creating configuration folder at /etc/thor'
mkdir /etc/thor -p
touch /etc/thor/mosquitto_pwd
chown mosquitto:mosquitto /etc/thor/mosquitto_pwd

# Configure mosquitto
echo 'Copied mqtt configuration to /etc/mqtt/conf.d'
cp ./preconfigured/thor-mosquitto.conf /etc/thor/

echo 'Set password for mosquitto'
mosquitto_passwd -b /etc/thor/mosquitto_pwd thor "$MQTT_PASSWORD"
echo "$MQTT_PASSWORD"

echo 'Restart mosquitto'
systemctl restart mosquitto
