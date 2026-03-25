# TP0: Docker + Comunicaciones + Concurrencia

Nicolas Pablo Severini - 111255

## Parte 1: Introducción a Docker

### Ejercicio N°1:

Se implementó un script `generar-compose.sh` para generar automáticamente el archivo de Docker Compose con la cantidad de clientes que se quiera.

El script recibe el nombre del archivo de salida y la cantidad de clientes, y llama a un script auxiliar en Python `generador.py` que arma el docker-compose en base a eso. De esta forma, se generan servicios client1, client2, ..., clientN sin tener que editar el YAML a mano cada vez.

Para ejecutarlo:

`./generar-compose.sh <archivo_de_salida> N`

Ejemplo:

`./generar-compose.sh docker-compose-dev.yaml 5`

Luego se puede levantar con:

`make docker-compose-up`

### Ejercicio N°2:

Para este ejercicio se modificó la configuración del cliente y del servidor para que no sea necesario reconstruir las imágenes al hacer cambios.

Se montan los archivos de configuración dentro de los containers usando volúmenes de Docker, de forma que los cambios en config.ini o config.yaml impactan directamente en la ejecución. Además, se eliminaron copias en el Dockerfile o variables de entorno que las sobrescriban.

### Ejercicio N°3:

Se implementó el script `validar-echo-server.sh` para verificar el correcto funcionamiento del servidor.

El script levanta un contenedor efímero dentro de la red de Docker y utiliza `netcat` para conectarse al servidor. Se envía un mensaje y se espera recibir exactamente el mismo (comportamiento de echo). Si la respuesta coincide, se imprime success; en caso contrario, fail.

De esta forma, se valida tanto la comunicación como el correcto funcionamiento del servidor sin exponer puertos ni depender del host.

Para ejecutarlo:

`./validar-echo-server.sh`

### Ejercicio N°4:

Se agregó manejo de la señal SIGTERM tanto en el cliente como en el servidor para permitir un cierre graceful de las aplicaciones.

En el cliente, se captura la señal y se interrumpe el loop principal, permitiendo finalizar la ejecución de forma controlada.
En el servidor, se implementó una función de shutdown que deja de aceptar nuevas conexiones y cierra el socket principal junto con las conexiones activas, manejando posibles errores.

De esta forma, se asegura que todos los recursos (sockets, conexiones, etc.) se liberen correctamente antes de terminar el proceso.

Para probarlo, se puede detener el sistema enviando la señal:

`make docker-compose-down`

## Parte 2: Repaso de Comunicaciones

### Ejercicio N°5:

El cliente construye una apuesta a partir de variables de entorno y la envía al servidor. El servidor recibe la apuesta, la deserializa y la persiste utilizando `store_bet(...)`, respondiendo luego con un ACK.

El protocolo implementado es basado en texto, donde cada apuesta se envía como una línea terminada en `\n`, con los campos separados por comas:

`agency,first_name,last_name,document,birthdate,number\n`

Del lado del servidor, se lee el mensaje hasta encontrar el salto de línea, se parsea y se valida la cantidad de campos. Luego de procesar correctamente la apuesta, se responde con:

`OK\n`

Para evitar problemas de comunicación sobre TCP:

Se implementó `writeFull` para asegurar el envío completo de los mensajes (evitando short write)
Se lee hasta `\n` para delimitar correctamente los mensajes en el stream (evitando lecturas incompletas)

Además, se mantuvo separada la capa de comunicación de la lógica de negocio, facilitando la extensión del protocolo en los siguientes ejercicios.

Se levanta igual que en los ejercicios anteriores:

`make docker-compose-up`

### Ejercicio N°6:

Para esto se implementó un iterador (`CSVBetIterator`) que lee las apuestas desde archivo y una función `NextBatch` que agrupa las apuestas en bloques de tamaño configurable (`batch.maxAmount`). Cada batch se envía en una única conexión, reduciendo la cantidad de mensajes enviados.

El protocolo se extendió respecto al ejercicio anterior: ahora el cliente envía múltiples apuestas (una por línea, en formato CSV) y utiliza una marca especial `END\n` para indicar el final del batch.

Ejemplo:
```
agency,first_name,last_name,document,birthdate,number
...
agency,first_name,last_name,document,birthdate,number
END
```
Del lado del servidor, se implementó un lector con buffer (`SocketReader`) que permite procesar correctamente el stream de TCP y reconstruir las líneas. Se leen apuestas hasta encontrar `END`, momento en el cual se procesa el batch completo.

Si todas las apuestas son válidas, el servidor responde con `OK\n`; en caso contrario, responde con `ERROR\n`.

Se reutiliza `writeFull` para asegurar envíos completos (short write) y se mantiene la delimitación por `\n` para evitar problemas de lectura sobre TCP.

Se levanta igual que en los ejercicios anteriores:

`make docker-compose-up`

### Ejercicio N°7:

Se extendió el protocolo para permitir la finalización del envío de apuestas y la consulta de ganadores, incorporando nuevos tipos de mensajes y lógica de coordinación en el servidor.

Una vez que el cliente termina de enviar todos los batches, envía un mensaje:

`DONE,<agency>\n`

Luego, abre una nueva conexión para consultar los ganadores mediante:

`GET_WINNERS,<agency>\n`

El servidor ahora distingue dinámicamente el tipo de mensaje recibido (`BATCH`, `DONE` o `GET_WINNERS`) y ejecuta la lógica correspondiente.

Para coordinar el sorteo, el servidor mantiene un conjunto de agencias que ya enviaron `DONE`. Cuando recibe la notificación de todas las agencias esperadas, ejecuta el sorteo utilizando `load_bets(...)` y `has_won(...)`, y guarda los resultados por agencia.

Si un cliente consulta los ganadores antes de que el sorteo haya finalizado, la conexión queda en espera (se almacena en una lista de pendientes). Una vez realizado el sorteo, el servidor responde a todas las consultas pendientes.

La respuesta del servidor tiene el formato:

`WINS,<cantidad>\n`

indicando la cantidad de ganadores para esa agencia.

De esta forma, se introduce una sincronización tipo barrera: el sorteo solo ocurre cuando todas las agencias finalizaron, y las consultas se responden únicamente cuando hay resultados completos.

Se levanta igual que en los ejercicios anteriores:

`make docker-compose-up`

## Parte 3: Repaso de Concurrencia

### Ejercicio N°8:

Se modificó el servidor para manejar múltiples conexiones en paralelo utilizando multithreading, creando un thread por cada cliente.

Para evitar problemas de concurrencia:

Se utiliza un `Lock` para proteger el acceso a recursos compartidos, evitando condiciones de carrera al almacenar apuestas (`store_bets`) y al actualizar el estado del sorteo.
Se utiliza un `Event` (`draw_done_event`) para coordinar la ejecución del sorteo. Los threads que reciben consultas de ganadores (`GET_WINNERS`) esperan sobre este evento hasta que el sorteo haya finalizado.

De esta forma, el servidor puede procesar múltiples clientes simultáneamente sin inconsistencias en los datos.

Se levanta igual que en los ejercicios anteriores:

`make docker-compose-up`
