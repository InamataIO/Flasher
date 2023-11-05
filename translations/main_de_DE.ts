<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="de_DE">
<context>
    <name>flash</name>
    <message>
        <location filename="../src/flash_model.py" line="363"/>
        <source>Error while generating the partitions image.</source>
        <translation>Fehler beim Erzeugen des Partitions-Images.</translation>
    </message>
    <message>
        <location filename="../src/flash_model.py" line="378"/>
        <source>Error while generating LittleFS image:</source>
        <translation>Fehler bei der Erzeugung des LittleFS-Image:</translation>
    </message>
    <message>
        <location filename="../src/flash_model.py" line="385"/>
        <source>Firmware image could not be found. Please refresh the cached files.</source>
        <translation>Das Firmware-Image konnte nicht gefunden werden. Bitte aktualisieren Sie die gecachten Daten.</translation>
    </message>
    <message>
        <location filename="../src/flash_model.py" line="392"/>
        <source>Bootloader image could not be found. Please refresh the cached files.</source>
        <translation>Das Bootloader-Image konnte nicht gefunden werden. Bitte aktualisieren Sie die gecachten Daten.</translation>
    </message>
    <message>
        <location filename="../src/flash_model.py" line="407"/>
        <source>Flashing failed
1. Check that the microcontroller is plugged in
2. For Snaps (Ubuntu Store) enable serial port access
 - Run in a terminal: snap connect inamata-flasher:raw-usb
 - Restart the app
3. Open a bug report or ask for support in the forum.

https://github.com/InamataCo/Flasher
https://inamata.co/forum/</source>
        <translation>Flaschen fehlgeschlagen
1. Prüfen Sie, ob der Mikrocontroller eingesteckt ist.
2. Für Snaps (Ubuntu Store) den Zugriff auf die serielle Schnittstelle aktivieren
 - In einem Terminal ausführen: snap connect inamata-flasher:raw-usb
 - Starten Sie die Anwendung neu
3. Öffnen Sie einen Fehlerbericht oder bitten Sie im Forum um Unterstützung.

https://github.com/InamataCo/Flasher
https://inamata.co/forum/</translation>
    </message>
    <message>
        <location filename="../src/flash_model.py" line="419"/>
        <source>Flashing failed
1. Check that the microcontroller is plugged in
2. Open a bug report or ask for support in the forum.

https://github.com/InamataCo/Flasher
https://inamata.co/forum/</source>
        <translation>Flaschen fehlgeschlagen
1. Prüfen Sie, ob der Mikrocontroller eingesteckt ist.
2. Öffnen Sie einen Fehlerbericht oder bitten Sie im Forum um Unterstützung.

https://github.com/InamataCo/Flasher
https://inamata.co/forum/</translation>
    </message>
    <message>
        <location filename="../src/flash_model.py" line="429"/>
        <source>User is missing permissions
1. Add the user to the dialout group (access serial ports)
  - Run in a terminal: sudo usermod -a -G dialout $USER
2. Log out and back in again</source>
        <translation>Benutzer fehlen Berechtigungen
1. Fügen Sie den Benutzer zur Dialout-Gruppe hinzu (Zugriff auf serielle Schnittstellen)
  - In einem Terminal ausführen: sudo usermod -a -G dialout $USER
2. Melden Sie sich ab und wieder an</translation>
    </message>
    <message>
        <location filename="../src/flash_model.py" line="439"/>
        <source>Listing COM / serial ports failed
For Snap installations:
 - Run in a terminal: snap connect inamata-flasher:raw-usb
 - Restart the app</source>
        <translation>Auflistung der COM / seriellen Schnittstellen fehlgeschlagen
Für Snap-Installationen:
 - In einem Terminal ausführen: snap connect inamata-flasher:raw-usb
 - Starten Sie die Anwendung neu</translation>
    </message>
    <message>
        <location filename="../src/flash_model.py" line="442"/>
        <source>Error when listing COM ports:</source>
        <translation>Fehler beim Auflisten der COM-Ports:</translation>
    </message>
</context>
<context>
    <name>help</name>
    <message>
        <source>Help</source>
        <translation type="vanished">Hilfe</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1307"/>
        <source>1. Enable serial port access (part 1)
  - Run in a terminal: sudo usermod -a -G dialout $USER

2. Log out and back in again (or restart)

3. Enable serial port access (part 2)
 - Run in a terminal: snap connect inamata-flasher:raw-usb
 - Restart the app

4. (Optional) Allow saving login
 - Run in a terminal: snap connect inamata-flasher:password-manager-service
 - Restart the app

5. (Optional) Verify permissions
 - Run in a terminal: snap connections inamata-flasher
 - Run in a terminal: groups

6. Additional information and support
 - https://github.com/InamataCo/Flasher
 - https://inamata.co/forum/</source>
        <translation>1. Zugriff zur seriellen Schnittstelle erlauben (Teil 1)
  - In einem Terminal ausführen: sudo usermod -a -G dialout $USER

2. Loggen Sie sich aus und wieder ein (oder starten Sie neu)

3. Zugriff zur seriellen Schnittstelle erlauben (Teil 2)
 - In einem Terminal ausführen: snap connect inamata-flasher:raw-usb
 - Starten sie die App neu

4. (Optional) Speichern der Anmeldung zulassen
 - In einem Terminal ausführen: snap connect inamata-flasher:password-manager-service
 - Starten sie die App neu

5. (Optional) Berechtigungen überprüfen
 - In einem Terminal ausführen: snap connections inamata-flasher
 - In einem Terminal ausführen: groups

6. Zusätliche Informationen und Support (EN)
 - https://github.com/InamataCo/Flasher
 - https://inamata.co/forum/</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1324"/>
        <source>1. Enable serial port access
  - Run in a terminal: sudo usermod -a -G dialout $USER

2. Log out and back in again (or restart)

3. (Optional) Verify permissions
 - Run in a terminal: groups

4. Additional information and support
 - https://github.com/InamataCo/Flasher
 - https://inamata.co/forum/</source>
        <translation>1. Zugriff zur seriellen Schnittstelle erlauben
  - In einem Terminal ausführen: sudo usermod -a -G dialout $USER

2. Loggen Sie sich aus und wieder ein (oder starten Sie neu)

3. (Optional) Berechtigungen überprüfen
 - In einem Terminal ausführen: groups

4. Zusätliche Informationen und Support (EN)
 - https://github.com/InamataCo/Flasher
 - https://inamata.co/forum/</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1336"/>
        <source>1. Install the serial driver (CP210x)
  - https://www.silabs.com/documents/public/software/CP210x_Windows_Drivers.zip
  - https://github.com/InamataCo/Flasher#driver-setup-instructions

2. Additional information and support
 - https://github.com/InamataCo/Flasher
 - https://inamata.co/forum/</source>
        <translation>1. Den seriellen Schnittstellentreiber installieren (CP210x)
  - https://www.silabs.com/documents/public/software/CP210x_Windows_Drivers.zip
  - https://github.com/InamataCo/Flasher#driver-setup-instructions

2. Zusätliche Informationen und Support (EN)
 - https://github.com/InamataCo/Flasher
 - https://inamata.co/forum/</translation>
    </message>
</context>
<context>
    <name>main</name>
    <message>
        <location filename="../src/controller.py" line="66"/>
        <source>Clear local data</source>
        <translation>Lokale Daten löschen</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="68"/>
        <source>Open system settings</source>
        <translation>Systemeinstellungen öffnen</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1158"/>
        <source>Setup</source>
        <translation>Einrichtung</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1164"/>
        <source>Open the following web page if it does not automatically open.</source>
        <translation>Öffnen Sie die folgende Webseite, falls sie nicht automatisch geöffnet wird.</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1168"/>
        <source>Cleared local data</source>
        <translation>Lokale Daten wurden gelöscht</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1178"/>
        <source>Enable Flash Mode</source>
        <translation>Flash-Modus aktivieren</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1185"/>
        <source>After closing this message, please press and hold the boot button on the ESP32 until the flash process starts.</source>
        <translation>Nachdem Sie diese Meldung geschlossen haben, halten Sie bitte die Boot-Taste am ESP32 gedrückt, bis der Flash-Vorgang beginnt.</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1189"/>
        <source>Finished Flashing</source>
        <translation>Fertig geflascht</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1195"/>
        <source>Successfully flashed the microcontroller</source>
        <translation>Erfolgreich den Mikrocontroller geflascht</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1199"/>
        <source>No Sites Found</source>
        <translation>Keine Standorte gefunden</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1205"/>
        <source>No sites found. Use the web app to create new sites.</source>
        <translation>Keine Standorte gefunden. Verwenden Sie die Web-App, um neue Standorte zu erstellen.</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1209"/>
        <source>No controllers found</source>
        <translation>Keine Controller gefunden</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1213"/>
        <source>Missing cached data</source>
        <translation>Fehlende gecachte Daten</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1220"/>
        <source>Controller not found in cache. Please clear cached data and try again.</source>
        <translation>Controller nicht im Cache gefunden. Bitte löschen Sie die Daten im Cache und versuchen Sie es erneut.</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1224"/>
        <source>Get Firmware</source>
        <translation>Firmware herunterladen</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1228"/>
        <source>Get Bootloader</source>
        <translation>Bootloader herunterladen</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1232"/>
        <source>Registering</source>
        <translation>Registrierung</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1236"/>
        <source>Flashing</source>
        <translation>Flaschen</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1240"/>
        <source>Missing Input</source>
        <translation>Fehlende Eingaben</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1248"/>
        <source>Please select a site or reload if none are available. If the problem persists please update the Inamata Flasher or contact your administrator.</source>
        <translation>Bitte wählen Sie einen Standort aus oder laden Sie sie neu, falls keine verfügbar sind. Wenn das Problem weiterhin besteht, aktualisieren Sie bitte den Inamata Flasher oder kontaktieren Sie Ihren Administrator.</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1270"/>
        <source>Please select a firmware version or reload if none are available. If the problem persists please update the Inamata Flasher or contact your administrator.</source>
        <translation>Bitte wählen Sie eine Firmware-Version aus oder laden Sie sie neu, falls keine verfügbar ist. Wenn das Problem weiterhin besteht, aktualisieren Sie bitte den Inamata Flasher oder kontaktieren Sie Ihren Administrator.</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1254"/>
        <source>Please enter a name for the new controller.</source>
        <translation>Bitte geben Sie einen Namen für den neuen Controller ein.</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1262"/>
        <source>Please select one or more WiFi connections to be used by the controller. To add or change entries, go to the &apos;Manage WiFi&apos; page.</source>
        <translation>Bitte wählen Sie eine oder mehrere WiFi-Verbindungen aus, die vom Controller verwendet werden sollen. Um Einträge hinzuzufügen oder zu ändern, gehen Sie auf die Seite &quot;WiFi verwalten&quot;.</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1274"/>
        <source>Permission error</source>
        <translation>Berechtigungsfehler</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1277"/>
        <source>No serial ports found</source>
        <translation>Keine serielle Schnittstellen gefunden</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1279"/>
        <source>Found 1 serial port:</source>
        <translation>Eine serielle Schnittstelle gefunden:</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1281"/>
        <source>Found %n serial ports:</source>
        <translation>%n serielle Schnittstellen gefunden:</translation>
    </message>
    <message>
        <location filename="../src/about_view.py" line="37"/>
        <location filename="../src/controller.py" line="1154"/>
        <source>About</source>
        <translation>Über</translation>
    </message>
</context>
<context>
    <name>server</name>
    <message>
        <location filename="../src/server_model.py" line="953"/>
        <source>Error while getting site and firmware data.</source>
        <translation>Fehler beim Abrufen von Standort- und Firmware-Daten.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="959"/>
        <source>Error while getting controller data.</source>
        <translation>Fehler beim Abrufen von Controller-Daten.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="966"/>
        <source>Not all controllers for this site could be fetched. Please upgrade the Inamata Flasher.</source>
        <translation>Es konnten nicht alle Controller für diesen Standort abgerufen werden. Bitte aktualisieren Sie den Inamata Flasher.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="972"/>
        <source>Error while getting default partition table data.</source>
        <translation>Fehler beim Abrufen von Standard-Partitionstabellendaten.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="978"/>
        <source>Could not find default partition table</source>
        <translation>Standard-Partitionstabelle konnte nicht gefunden werden</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="984"/>
        <source>Error while getting partition table data.</source>
        <translation>Fehler beim Abrufen von Partitionstabellendaten.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="990"/>
        <source>Could not find partition table on server.</source>
        <translation>Die Partitionstabelle auf dem Server konnte nicht gefunden werden.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="997"/>
        <source>Could not find the controller. Please reload the controller data.</source>
        <translation>Der Controller konnte nicht gefunden werden. Bitte laden Sie die Controllerdaten neu.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="1004"/>
        <source>Failed deleting controller. Check your permissions or contact your administrator.</source>
        <translation>Das Löschen des Controllers ist fehlgeschlagen. Überprüfen Sie Ihre Berechtigungen oder wenden Sie sich an Ihren Administrator.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="1011"/>
        <source>Failed connecting to the authentication server. Check your internet connection or contact Inamata.</source>
        <translation>Die Verbindung zum Authentifizierungsserver ist fehlgeschlagen. Überprüfen Sie Ihre Internetverbindung oder kontaktieren Sie Inamata.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="1018"/>
        <source>Error downloading firmware. Not all required metadata found:</source>
        <translation>Fehler beim Herunterladen der Firmware. Nicht alle erforderlichen Metadaten wurden gefunden:</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="1025"/>
        <source>Error downloading bootloader. Not all required metadata found:</source>
        <translation>Fehler beim Herunterladen des Bootloaders. Nicht alle erforderlichen Metadaten wurden gefunden:</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="1032"/>
        <source>Failed downloading the file. Try refreshing, check your internet connection or contact support.</source>
        <translation>Das Herunterladen der Datei ist fehlgeschlagen. Versuchen Sie zu aktualisieren, überprüfen Sie Ihre Internetverbindung oder kontaktieren Sie den Support.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="1039"/>
        <source>Checksum of downloaded file did not match. Please try another version or contact support.</source>
        <translation>Die Prüfsumme der heruntergeladenen Datei stimmt nicht überein. Bitte versuchen Sie eine andere Version oder kontaktieren Sie den Support.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="1045"/>
        <source>Error while refreshing the firmware URL. Please reload data.</source>
        <translation>Fehler beim Aktualisieren der Firmware-URL. Aktualisieren Sie bitte die Daten.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="1051"/>
        <source>Error while refreshing the bootloader URL. Please reload data.</source>
        <translation>Fehler beim Aktualisieren der Bootloader-URL. Aktualisieren Sie bitte die Daten.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="1057"/>
        <source>Access has expired. Please log in again.</source>
        <translation>Der Zugang ist abgelaufen. Bitte melden Sie sich erneut an.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="1064"/>
        <source>An error occured while requesting data from the server API. Check that you&apos;re using an up-to-date version of the Inamata Flasher.</source>
        <translation>Bei der Abfrage von Daten von der Server-API ist ein Fehler aufgetreten. Überprüfen Sie, ob Sie eine aktuelle Version des Inamata Flashers verwenden.</translation>
    </message>
</context>
</TS>
