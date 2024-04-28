<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="es_ES">
<context>
    <name>flash</name>
    <message>
        <location filename="../src/flash_model.py" line="363"/>
        <source>Error while generating the partitions image.</source>
        <translation type="unfinished">Error al generar la imagen de las particiones.</translation>
    </message>
    <message>
        <location filename="../src/flash_model.py" line="378"/>
        <source>Error while generating LittleFS image:</source>
        <translation type="unfinished">Error al generar la imagen LittleFS:</translation>
    </message>
    <message>
        <location filename="../src/flash_model.py" line="385"/>
        <source>Firmware image could not be found. Please refresh the cached files.</source>
        <translation type="unfinished">No se pudo encontrar la imagen del firmware. Actualice los archivos en caché.</translation>
    </message>
    <message>
        <location filename="../src/flash_model.py" line="392"/>
        <source>Bootloader image could not be found. Please refresh the cached files.</source>
        <translation type="unfinished">No se pudo encontrar la imagen del cargador de arranque. Actualice los archivos en caché.</translation>
    </message>
    <message>
        <location filename="../src/flash_model.py" line="407"/>
        <source>Flashing failed
1. Check that the microcontroller is plugged in
2. For Snaps (Ubuntu Store) enable serial port access
 - Run in a terminal: snap connect inamata-flasher:raw-usb
 - Restart the app
3. Open a bug report or ask for support in the forum.

https://github.com/InamataIO/Flasher
https://www.inamata.io/forum/</source>
        <translation type="unfinished">Falló el flasheo del microcontrolador
1. Compruebe que el microcontrolador esté enchufado.
2. Para Snaps (Ubuntu Store), habilite el acceso al puerto serie
  - Ejecutar en una terminal: snap connect inamata-flasher:raw-usb
  - Reinicia la aplicación
3. Abra un informe de error o solicite ayuda en el foro.

https://github.com/InamataIO/Flasher
https://www.inamata.io/forum/</translation>
    </message>
    <message>
        <location filename="../src/flash_model.py" line="419"/>
        <source>Flashing failed
1. Check that the microcontroller is plugged in
2. Open a bug report or ask for support in the forum.

https://github.com/InamataIO/Flasher
https://www.inamata.io/forum/</source>
        <translatorcomment>Falló el flasheo del microcontrolador
1. Compruebe que el microcontrolador esté enchufado.
2. Abra un informe de error o solicite ayuda en el foro.

https://github.com/InamataIO/Flasher
https://www.inamata.io/forum/</translatorcomment>
        <translation type="unfinished">Falló el flasheo del microcontrolador
1. Compruebe que el microcontrolador esté enchufado.
2. Abra un informe de error o solicite ayuda en el foro.

https://github.com/InamataIO/Flasher
https://www.inamata.io/forum/</translation>
    </message>
    <message>
        <location filename="../src/flash_model.py" line="429"/>
        <source>User is missing permissions
1. Add the user to the dialout group (access serial ports)
  - Run in a terminal: sudo usermod -a -G dialout $USER
2. Log out and back in again</source>
        <translation type="unfinished">Al usuario le faltan permisos
1. Agregue el usuario al grupo &apos;dialout&apos; (acceda a los puertos serie)
   - Ejecutar en una terminal: sudo usermod -a -G dialout $USER
2. Cerrar sesión y volver a iniciarla</translation>
    </message>
    <message>
        <location filename="../src/flash_model.py" line="439"/>
        <source>Listing COM / serial ports failed
For Snap installations:
 - Run in a terminal: snap connect inamata-flasher:raw-usb
 - Restart the app</source>
        <translation type="unfinished">Error al enumerar los puertos COM/serie
Para instalaciones Snap:
  - Ejecutar en una terminal: snap connect inamata-flasher:raw-usb
  - Reinicia la aplicación</translation>
    </message>
    <message>
        <location filename="../src/flash_model.py" line="442"/>
        <source>Error when listing COM ports:</source>
        <translation type="unfinished">Error al enumerar los puertos COM:</translation>
    </message>
</context>
<context>
    <name>help</name>
    <message>
        <location filename="../src/controller.py" line="1573"/>
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
 - https://github.com/InamataIO/Flasher
 - https://www.inamata.io/forum/</source>
        <translation type="unfinished">1. Habilite el acceso al puerto serie (parte 1)
   - Ejecutar en una terminal: sudo usermod -a -G dialout $USER

2. Cerrar sesión y volver a iniciarla (o reiniciar)

3. Habilite el acceso al puerto serie (parte 2)
  - Ejecutar en una terminal: snap connect inamata-flasher:raw-usb
  - Reinicia la aplicación

4. (Opcional) Permitir guardar el inicio de sesión
  - Ejecutar en una terminal: snap connect inamata-flasher:password-manager-service
  - Reinicia la aplicación

5. (Opcional) Verificar permisos
  - Ejecutar en una terminal: snap connections inamata-flasher
  - Ejecutar en una terminal: groups

6. Información adicional y soporte
  - https://github.com/InamataIO/Flasher
  - https://www.inamata.io/forum/</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1590"/>
        <source>1. Enable serial port access
  - Run in a terminal: sudo usermod -a -G dialout $USER

2. Log out and back in again (or restart)

3. (Optional) Verify permissions
 - Run in a terminal: groups

4. Additional information and support
 - https://github.com/InamataIO/Flasher
 - https://www.inamata.io/forum/</source>
        <translation type="unfinished">1. Habilite el acceso al puerto serie
   - Ejecutar en una terminal: sudo usermod -a -G dialout $USER

2. Cerrar sesión y volver a iniciarla (o reiniciar)

3. (Opcional) Verificar permisos
  - Ejecutar en una terminal: groups

4. Información adicional y soporte
  - https://github.com/InamataIO/Flasher
  - https://www.inamata.io/forum/</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1602"/>
        <source>1. Install the serial driver (CP210x)
  - https://www.silabs.com/documents/public/software/CP210x_Windows_Drivers.zip
  - https://github.com/InamataIO/Flasher#driver-setup-instructions

2. Additional information and support
 - https://github.com/InamataIO/Flasher
 - https://www.inamata.io/forum/</source>
        <translation type="unfinished">1. Instale el controlador serie (CP210x)
   - https://www.silabs.com/documents/public/software/CP210x_Windows_Drivers.zip
   - https://github.com/InamataIO/Flasher#driver-setup-instructions

2. Información adicional y soporte
  - https://github.com/InamataIO/Flasher
  - https://www.inamata.io/forum/</translation>
    </message>
</context>
<context>
    <name>main</name>
    <message>
        <location filename="../src/about_view.py" line="44"/>
        <location filename="../src/controller.py" line="1323"/>
        <source>About</source>
        <translation type="unfinished">Sobre</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="84"/>
        <source>Clear local data</source>
        <translation type="unfinished">Borrar datos locales</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="86"/>
        <source>Open system settings</source>
        <translation type="unfinished">Abrir la configuración del sistema</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1327"/>
        <source>Setup</source>
        <translation type="unfinished">Configurar</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1333"/>
        <source>Open the following web page if it does not automatically open.</source>
        <translation type="unfinished">Abra la siguiente página web si no se abre automáticamente.</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1337"/>
        <source>Cleared local data</source>
        <translation type="unfinished">Datos locales borrados</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1343"/>
        <source>Cleared secrets, configurations and cached data.</source>
        <translation type="unfinished">Se borraron los secretos, las configuraciones y los datos almacenados en caché.</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1347"/>
        <source>Invalid WiFi connection</source>
        <translation type="unfinished">Conexión WiFi no válida</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1353"/>
        <source>The WiFi name (SSID) is blank. Please enter a WiFi name.</source>
        <translation type="unfinished">El nombre de WiFi (SSID) está en blanco. Por favor ingresa un nombre de WiFi.</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1360"/>
        <source>The WiFi name (SSID) is too long. Please enter a WiFi name with 32 characters or fewer.</source>
        <translation type="unfinished">El nombre de WiFi (SSID) es demasiado largo. Ingrese un nombre de WiFi con 32 caracteres o menos.</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1366"/>
        <source>Latest</source>
        <comment>Label for latest firmware image</comment>
        <translation type="unfinished">El último</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1373"/>
        <source>No firmware images found on the server. Check that you have permissions to view firmware images or contact support.</source>
        <translation type="unfinished">No se encontraron imágenes de firmware en el servidor. Verifique que tenga permisos para ver imágenes de firmware o comuníquese con el soporte.</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1377"/>
        <location filename="../src/controller.py" line="1381"/>
        <source>No firmware images found</source>
        <translation type="unfinished">No se encontraron imágenes de firmware</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1385"/>
        <source>Enable Flash Mode</source>
        <translation type="unfinished">Habilitar el modo flash</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1392"/>
        <source>After closing this message, please press and hold the boot button on the ESP32 until the flash process starts.</source>
        <translation type="unfinished">Después de cerrar este mensaje, presione y mantenga presionado el botón de inicio en el ESP32 hasta que comience el proceso de actualización.</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1396"/>
        <source>Finished Flashing</source>
        <translation type="unfinished">Flasheo terminado</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1402"/>
        <source>Successfully flashed the microcontroller</source>
        <translation type="unfinished">Flasheó exitosamente el microcontrolador</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1406"/>
        <source>No Sites Found</source>
        <translation type="unfinished">No se encontraron lugares</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1412"/>
        <source>No sites found. Use the web app to create new sites.</source>
        <translation type="unfinished">No se encontraron lugares. Utilice la aplicación web para crear nuevos lugares.</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1416"/>
        <source>No controllers found</source>
        <translation type="unfinished">No se encontraron controladores</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1420"/>
        <source>Missing cached data</source>
        <translation type="unfinished">Faltan datos en caché</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1427"/>
        <source>Controller not found in cache. Please clear cached data and try again.</source>
        <translation type="unfinished">Controlador no encontrado en la caché. Borre los datos almacenados en caché y vuelva a intentarlo.</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1431"/>
        <source>Get Firmware</source>
        <translation type="unfinished">Obtener firmware</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1435"/>
        <source>Get Bootloader</source>
        <translation type="unfinished">Obtener gestor de arranque</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1439"/>
        <source>Registering</source>
        <translation type="unfinished">Registrarse</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1443"/>
        <source>Flashing</source>
        <translation type="unfinished">Flashear</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1447"/>
        <source>Missing Input</source>
        <translation type="unfinished">Entrada faltante</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1455"/>
        <source>Please select a site or reload if none are available. If the problem persists please update the Inamata Flasher or contact your administrator.</source>
        <translation type="unfinished">Seleccione un lugar o vuelva a cargarlo si no hay ninguno disponible. Si el problema persiste, actualice Inamata Flasher o comuníquese con su administrador.</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1461"/>
        <source>Please enter a name for the new controller.</source>
        <translation type="unfinished">Introduzca un nombre para el nuevo controlador.</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1469"/>
        <source>Please select one or more WiFi connections to be used by the controller. To add or change entries, go to the &apos;Manage WiFi&apos; page.</source>
        <translation type="unfinished">Seleccione una o más conexiones WiFi para que las utilice el controlador. Para agregar o cambiar entradas, vaya a la página &apos;Administrar WiFi&apos;.</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1477"/>
        <source>Please select a firmware version or reload if none are available. If the problem persists please update the Inamata Flasher or contact your administrator.</source>
        <translation type="unfinished">Seleccione una versión de firmware o vuelva a cargarla si no hay ninguna disponible. Si el problema persiste, actualice Inamata Flasher o comuníquese con su administrador.</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1481"/>
        <source>Permission error</source>
        <translation type="unfinished">Error de permiso</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1484"/>
        <source>No serial ports found</source>
        <translation type="unfinished">No se encontraron puertos serie</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1486"/>
        <source>Found 1 serial port:</source>
        <translation type="unfinished">Encontrado 1 puerto serie:</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1488"/>
        <source>Found %n serial ports:</source>
        <translation type="unfinished">Encontré %n puertos serie:</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1492"/>
        <source>available</source>
        <translation type="unfinished">disponible</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1496"/>
        <source>up to date</source>
        <translation type="unfinished">A hoy</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1500"/>
        <source>New version avaiable</source>
        <translation type="unfinished">Nueva versión disponible</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1507"/>
        <source>A newer version of the Flasher is available. Update to avoid inconsistent behavior and receive bug fixes. Download the installer directly or view the release notes first.</source>
        <translation type="unfinished">Hay disponible una versión más nueva de Flasher. Actualice para evitar comportamientos inconsistentes y recibir correcciones de errores. Descargue el instalador directamente o consulte primero las notas de la versión.</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1511"/>
        <source>Flasher is up-to-date</source>
        <translation type="unfinished">Flasher está actualizado</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1517"/>
        <source>You already have the latest version of the Flasher.</source>
        <translation type="unfinished">Ya tienes la última versión de Flasher.</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1521"/>
        <source>Fetching newest version failed</source>
        <translation type="unfinished">Falló la obtención de la versión más reciente</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1528"/>
        <source>There was a connection error trying to fetch the latest version details.</source>
        <translation type="unfinished">Se produjo un error de conexión al intentar obtener los detalles de la última versión.</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1532"/>
        <source>Download</source>
        <translation type="unfinished">Descargar</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1536"/>
        <source>Show release</source>
        <translation type="unfinished">Mostrar notas</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1540"/>
        <source>Automatic updates</source>
        <translation type="unfinished">Actualizaciones automáticas</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1547"/>
        <source>The Flasher is installed as a Snap and will automatically be updated in a few days.</source>
        <translation type="unfinished">Flasher se instala como Snap y se actualizará automáticamente en unos días.</translation>
    </message>
</context>
<context>
    <name>serial</name>
    <message>
        <location filename="../src/serial_monitor_controller.py" line="154"/>
        <source>No COM ports found</source>
        <translation type="unfinished">No se encontraron puertos COM</translation>
    </message>
    <message>
        <location filename="../src/serial_monitor_controller.py" line="166"/>
        <source>No connected serial devices were found. Check if

1. the device is connected
2. the USB cable is too long
3. another port on your computer works
4. unplugging it and plugging it in again helps</source>
        <translation type="unfinished">No se encontraron dispositivos seriales conectados. Comprobar si

1. el dispositivo está conectado
2. el cable USB es demasiado largo
3. otro puerto en tu computadora funciona
4. Desenchufarlo y volver a enchufarlo ayuda</translation>
    </message>
    <message>
        <location filename="../src/serial_monitor_controller.py" line="170"/>
        <source>Serial port disconnected</source>
        <translation type="unfinished">Puerto serie desconectado</translation>
    </message>
    <message>
        <location filename="../src/serial_monitor_controller.py" line="173"/>
        <source>Unknown connection error</source>
        <translation type="unfinished">Error de conexión desconocido</translation>
    </message>
    <message>
        <location filename="../src/serial_monitor_view.py" line="67"/>
        <source>Serial Monitor</source>
        <translation type="unfinished">Monitor serie</translation>
    </message>
</context>
<context>
    <name>server</name>
    <message>
        <location filename="../src/server_model.py" line="972"/>
        <source>Error while getting site and firmware data.</source>
        <translation type="unfinished">Error al obtener datos del lugar y del firmware.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="978"/>
        <source>Error while getting controller data.</source>
        <translation type="unfinished">Error al obtener datos del controlador.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="985"/>
        <source>Not all controllers for this site could be fetched. Please upgrade the Inamata Flasher.</source>
        <translation type="unfinished">No se pudieron recuperar todos los controladores de este lugar. Actualice el Inamata Flasher.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="991"/>
        <source>Error while getting default partition table data.</source>
        <translation type="unfinished">Error al obtener los datos de la tabla de particiones predeterminada.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="997"/>
        <source>Could not find default partition table</source>
        <translation type="unfinished">No se pudo encontrar la tabla de particiones predeterminada</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="1003"/>
        <source>Error while getting partition table data.</source>
        <translation type="unfinished">Error al obtener datos de la tabla de particiones.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="1009"/>
        <source>Could not find partition table on server.</source>
        <translation type="unfinished">No se pudo encontrar la tabla de particiones en el servidor.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="1016"/>
        <source>Could not find the controller. Please reload the controller data.</source>
        <translation type="unfinished">No se pudo encontrar el controlador. Vuelva a cargar los datos del controlador.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="1023"/>
        <source>Failed deleting controller. Check your permissions or contact your administrator.</source>
        <translation type="unfinished">No se pudo eliminar el controlador. Verifique sus permisos o comuníquese con su administrador.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="1030"/>
        <source>Failed connecting to the authentication server. Check your internet connection or contact Inamata.</source>
        <translation type="unfinished">No se pudo conectar con el servidor de autenticación. Comprueba tu conexión a Internet o contacta con Inamata.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="1037"/>
        <source>Error downloading firmware. Not all required metadata found:</source>
        <translation type="unfinished">Error al descargar el firmware. No se encontraron todos los metadatos requeridos:</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="1044"/>
        <source>Error downloading bootloader. Not all required metadata found:</source>
        <translation type="unfinished">Error al descargar el gestor de arranque. No se encontraron todos los metadatos requeridos:</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="1051"/>
        <source>Failed downloading the file. Try refreshing, check your internet connection or contact support.</source>
        <translation type="unfinished">No se pudo descargar el archivo. Intente actualizar, verifique su conexión a Internet o comuníquese con el soporte.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="1058"/>
        <source>Checksum of downloaded file did not match. Please try another version or contact support.</source>
        <translation type="unfinished">La suma de comprobación del archivo descargado no coincide. Pruebe con otra versión o comuníquese con el soporte.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="1064"/>
        <source>Error while refreshing the firmware URL. Please reload data.</source>
        <translation type="unfinished">Error al actualizar la URL del firmware. Por favor recargar datos.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="1070"/>
        <source>Error while refreshing the bootloader URL. Please reload data.</source>
        <translation type="unfinished">Error al actualizar la URL del gestor de arranque. Por favor recargar datos.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="1076"/>
        <source>Access has expired. Please log in again.</source>
        <translation type="unfinished">El acceso ha caducado. Por favor inicia sesión nuevamente.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="1083"/>
        <source>An error occurred while requesting data from the server API. Check that you&apos;re using an up-to-date version of the Inamata Flasher.</source>
        <translation type="unfinished">Se produjo un error al solicitar datos de la API del servidor. Comprueba que estás utilizando una versión actualizada de Inamata Flasher.</translation>
    </message>
</context>
</TS>
