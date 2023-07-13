# Onprem docker-compose pipeline-ból

## Koncepció

  - a pipline a build alapján kicseréli a compose fájlban az image taget
  - a pipeline lemásolja a hostra a megfelelő compose fájlt
  - restartolja/indítja a compose fájl alapján a docker image-t

## Előfeltételek

  - a hoston ott vannak a compose fájlhoz tartozó env fájlok!

## Azure Agent

Az agent containerbe fel van mountolva `/opt/meteo/mount`:

  - ebbe van a fifo fájl, amibe echo-zva van a parancs
  - ide másolódóik a docker-compose yml fájl

### Agent build

azdevops-agent mappában vannak a szükséges fájlok.

  - Dockerfile felhasználásával build
  - docker-compose.yml futtatható az agent
  - .agent_env fájl szükséges hozzá, melynek tartalmaznia kell:
```
AZP_URL=https://dev.azure.com/grapesolutions
AZP_TOKEN=<ide egy Personal Access Token kell>
AZP_POOL=<ide az agent pool neve>
```
## Host előkészítése

A hoston futó konténerek fifo-n (named pipe) keresztül vannak kezelve.
  - kell egy nem sudo (normál) user aki olvassa a fifo-t `sudo useradd azagent`
  - ne tudjon belépni az user `sudo usermod -L azagent`
  - a usernek benne kell lennie a "docker" csoportban, hogy sudo nélkül tudjon konténert kezelni `sudo usermod -aG docker azagent`
  - a docker login a user nevében (is) kell, emiatt kell home
  - fifo lognak fájl `sudo touch /opt/meteo/fifo_out.log && sudo chown azagent /opt/meteo/fifo_out.log`
  - az `/opt/meteo` mappában minen elemnek a group tulajdonosa "docker" legyen, különben sudo kell a docker parancsokhoz `sudo chgrp docker -R /opt/meteo`

## Fifo létrehozás

```
mkfifo /opt/meteo/mount/meteo-pipe
chown azagent /opt/meteo/listenpipe.sh
chmod +x /opt/meteo/listenpipe.sh
chown azagent /opt/meteo/listenpipe.sh
```
A listenpipe.sh tartalmazza a pipe kiolvasásást és futtatását. Hogy ez mindig fusson:
`sudo -u azagent crontab -e`

A crontab szerkesztőbe a következő kell:
`@reboot /opt/meteo/listenpipe.sh`

A sh script futtatása restart nélül a háttérben:
`sudo -u azagent nohup sh /opt/meteo/listenpipe.sh &`
