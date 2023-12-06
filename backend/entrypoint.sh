#!/bin/bash
ln -snf /usr/share/zoneinfo/$TZ /etc/localtime
echo $TZ > /etc/timezone

if [ "$INSTALL_FW_CERTIFICATE" = "onprem" ];
then
   echo " ===> INSTALLING CERTIFICATE"
   update-ca-certificates
else
   echo " ===> NO EXTERNAL CERTIFICATE INSTALLED"
fi

exec "$@"