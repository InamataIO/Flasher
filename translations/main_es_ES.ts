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

https://github.com/InamataCo/Flasher
https://inamata.co/forum/</source>
        <translation type="unfinished">Falló el flasheo del microcontrolador
1. Compruebe que el microcontrolador esté enchufado.
2. Para Snaps (Ubuntu Store), habilite el acceso al puerto serie
  - Ejecutar en una terminal: snap connect inamata-flasher:raw-usb
  - Reinicia la aplicación
3. Abra un informe de error o solicite ayuda en el foro.

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
        <translation type="unfinished">Falló el flasheo del microcontrolador
1. Compruebe que el microcontrolador esté enchufado.
2. Abra un informe de error o solicite ayuda en el foro.

https://github.com/InamataCo/Flasher
https://inamata.co/forum/</translation>
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
        <translation type="unfinished">1. Habilite el acceso al puerto serie
   - Ejecutar en una terminal: sudo usermod -a -G dialout $USER

2. Cerrar sesión y volver a iniciarla (o reiniciar)

3. (Opcional) Verificar permisos
  - Ejecutar en una terminal: groups

4. Información adicional y soporte
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
        <translation type="unfinished">1. Instale el controlador serie (CP210x)
   - https://www.silabs.com/documents/public/software/CP210x_Windows_Drivers.zip
   - https://github.com/InamataCo/Flasher#driver-setup-instructions

2. Información adicional y soporte
  - https://github.com/InamataCo/Flasher
  - https://inamata.co/forum/</translation>
    </message>
</context>
<context>
    <name>main</name>
    <message>
        <location filename="../src/about_view.py" line="37"/>
        <location filename="../src/controller.py" line="1154"/>
        <source>About</source>
        <translation type="unfinished">Sobre</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="66"/>
        <source>Clear local data</source>
        <translation type="unfinished">Borrar datos locales</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="68"/>
        <source>Open system settings</source>
        <translation type="unfinished">Abrir la configuración del sistema</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1158"/>
        <source>Setup</source>
        <translation type="unfinished">Configurar</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1164"/>
        <source>Open the following web page if it does not automatically open.</source>
        <translation type="unfinished">Abra la siguiente página web si no se abre automáticamente.</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1168"/>
        <source>Cleared local data</source>
        <translation type="unfinished">Datos locales borrados</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1174"/>
        <source>Cleared secrets, configurations and cached data.</source>
        <translation type="unfinished">Se borraron los secretos, las configuraciones y los datos almacenados en caché.</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1178"/>
        <source>Enable Flash Mode</source>
        <translation type="unfinished">Habilitar el modo flash</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1185"/>
        <source>After closing this message, please press and hold the boot button on the ESP32 until the flash process starts.</source>
        <translation type="unfinished">Después de cerrar este mensaje, presione y mantenga presionado el botón de inicio en el ESP32 hasta que comience el proceso de actualización.</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1189"/>
        <source>Finished Flashing</source>
        <translation type="unfinished">Flasheo terminado</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1195"/>
        <source>Successfully flashed the microcontroller</source>
        <translation type="unfinished">Flasheó exitosamente el microcontrolador</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1199"/>
        <source>No Sites Found</source>
        <translation type="unfinished">No se encontraron lugares</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1205"/>
        <source>No sites found. Use the web app to create new sites.</source>
        <translation type="unfinished">No se encontraron lugares. Utilice la aplicación web para crear nuevos lugares.</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1209"/>
        <source>No controllers found</source>
        <translation type="unfinished">No se encontraron controladores</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1213"/>
        <source>Missing cached data</source>
        <translation type="unfinished">Faltan datos en caché</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1220"/>
        <source>Controller not found in cache. Please clear cached data and try again.</source>
        <translation type="unfinished">Controlador no encontrado en la caché. Borre los datos almacenados en caché y vuelva a intentarlo.</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1224"/>
        <source>Get Firmware</source>
        <translation type="unfinished">Obtener firmware</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1228"/>
        <source>Get Bootloader</source>
        <translation type="unfinished">Obtener gestor de arranque</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1232"/>
        <source>Registering</source>
        <translation type="unfinished">Registrarse</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1236"/>
        <source>Flashing</source>
        <translation type="unfinished">Flashear</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1240"/>
        <source>Missing Input</source>
        <translation type="unfinished">Entrada faltante</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1248"/>
        <source>Please select a site or reload if none are available. If the problem persists please update the Inamata Flasher or contact your administrator.</source>
        <translation type="unfinished">Seleccione un lugar o vuelva a cargarlo si no hay ninguno disponible. Si el problema persiste, actualice Inamata Flasher o comuníquese con su administrador.</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1254"/>
        <source>Please enter a name for the new controller.</source>
        <translation type="unfinished">Introduzca un nombre para el nuevo controlador.</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1262"/>
        <source>Please select one or more WiFi connections to be used by the controller. To add or change entries, go to the &apos;Manage WiFi&apos; page.</source>
        <translation type="unfinished">Seleccione una o más conexiones WiFi para que las utilice el controlador. Para agregar o cambiar entradas, vaya a la página &apos;Administrar WiFi&apos;.</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1270"/>
        <source>Please select a firmware version or reload if none are available. If the problem persists please update the Inamata Flasher or contact your administrator.</source>
        <translation type="unfinished">Seleccione una versión de firmware o vuelva a cargarla si no hay ninguna disponible. Si el problema persiste, actualice Inamata Flasher o comuníquese con su administrador.</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1274"/>
        <source>Permission error</source>
        <translation type="unfinished">Error de permiso</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1277"/>
        <source>No serial ports found</source>
        <translation type="unfinished">No se encontraron puertos serie</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1279"/>
        <source>Found 1 serial port:</source>
        <translation type="unfinished">Encontrado 1 puerto serie:</translation>
    </message>
    <message>
        <location filename="../src/controller.py" line="1281"/>
        <source>Found %n serial ports:</source>
        <translation type="unfinished">Encontré %n puertos serie:</translation>
    </message>
</context>
<context>
    <name>server</name>
    <message>
        <location filename="../src/server_model.py" line="953"/>
        <source>Error while getting site and firmware data.</source>
        <translation type="unfinished">Error al obtener datos del lugar y del firmware.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="959"/>
        <source>Error while getting controller data.</source>
        <translation type="unfinished">Error al obtener datos del controlador.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="966"/>
        <source>Not all controllers for this site could be fetched. Please upgrade the Inamata Flasher.</source>
        <translation type="unfinished">No se pudieron recuperar todos los controladores de este lugar. Actualice el Inamata Flasher.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="972"/>
        <source>Error while getting default partition table data.</source>
        <translation type="unfinished">Error al obtener los datos de la tabla de particiones predeterminada.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="978"/>
        <source>Could not find default partition table</source>
        <translation type="unfinished">No se pudo encontrar la tabla de particiones predeterminada</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="984"/>
        <source>Error while getting partition table data.</source>
        <translation type="unfinished">Error al obtener datos de la tabla de particiones.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="990"/>
        <source>Could not find partition table on server.</source>
        <translation type="unfinished">No se pudo encontrar la tabla de particiones en el servidor.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="997"/>
        <source>Could not find the controller. Please reload the controller data.</source>
        <translation type="unfinished">No se pudo encontrar el controlador. Vuelva a cargar los datos del controlador.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="1004"/>
        <source>Failed deleting controller. Check your permissions or contact your administrator.</source>
        <translation type="unfinished">No se pudo eliminar el controlador. Verifique sus permisos o comuníquese con su administrador.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="1011"/>
        <source>Failed connecting to the authentication server. Check your internet connection or contact Inamata.</source>
        <translation type="unfinished">No se pudo conectar con el servidor de autenticación. Comprueba tu conexión a Internet o contacta con Inamata.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="1018"/>
        <source>Error downloading firmware. Not all required metadata found:</source>
        <translation type="unfinished">Error al descargar el firmware. No se encontraron todos los metadatos requeridos:</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="1025"/>
        <source>Error downloading bootloader. Not all required metadata found:</source>
        <translation type="unfinished">Error al descargar el gestor de arranque. No se encontraron todos los metadatos requeridos:</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="1032"/>
        <source>Failed downloading the file. Try refreshing, check your internet connection or contact support.</source>
        <translation type="unfinished">No se pudo descargar el archivo. Intente actualizar, verifique su conexión a Internet o comuníquese con el soporte.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="1039"/>
        <source>Checksum of downloaded file did not match. Please try another version or contact support.</source>
        <translation type="unfinished">La suma de comprobación del archivo descargado no coincide. Pruebe con otra versión o comuníquese con el soporte.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="1045"/>
        <source>Error while refreshing the firmware URL. Please reload data.</source>
        <translation type="unfinished">Error al actualizar la URL del firmware. Por favor recargar datos.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="1051"/>
        <source>Error while refreshing the bootloader URL. Please reload data.</source>
        <translation type="unfinished">Error al actualizar la URL del gestor de arranque. Por favor recargar datos.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="1057"/>
        <source>Access has expired. Please log in again.</source>
        <translation type="unfinished">El acceso ha caducado. Por favor inicia sesión nuevamente.</translation>
    </message>
    <message>
        <location filename="../src/server_model.py" line="1064"/>
        <source>An error occurred while requesting data from the server API. Check that you&apos;re using an up-to-date version of the Inamata Flasher.</source>
        <translation type="unfinished">Se produjo un error al solicitar datos de la API del servidor. Comprueba que estás utilizando una versión actualizada de Inamata Flasher.</translation>
    </message>
</context>
</TS>
