# Telegram Bot and Channel settings  [EN]

For the Keylogger send the information using the Telegram Bot, it is necessary 
to make some preliminary preparations that i will summarize below.

1. Create a private Telegram channel where the data will be received.
2. Create a Telegram bot with the [BoFather](https://telegram.me/botfather) tool.
    [Here](https://core.telegram.org/bots) you have everything you need to know 
    about the [Telegram Bots](https://core.telegram.org/bots).
3. Once the bot is created you will have an **API key**. This key is necessary for the
    Bot is identified when sending messages.
4. Next you must obtain a user ID by calling the url
    https://api.telegram.org/bot_TU_API_KEY_/getUpdates
5. Then you must obtain the channel ID. And for this you must make public (momentarily)
    the channel and call the next url
    https://api.telegram.org/bot_ID_USUARIO:_TU_API_KEY_/sendMessage?chat_id=@_NAME_DEL_CANAL&text="message "
    Then you can return the Channel as private.
6. You can now send data to the Bot from the Keylogger and it will publish it on the channel.

You have detailed information about this process
[here] (http://www.bernaerts-nicolas.fr/linux/75-debian/351-debian-send-telegram-notification)

# Configuración del Bot de Telegram y el Canal  [ES]

Para que el Keylogger envie la informacion usando el Bot de Telegram se 
requiere hacer unos preparativos previos que resumiré a continuación.

1.  Crear un canal privado de Telegram donde se recibiran los datos.
2.  Crear un bot de Telegram con la herramienta [BoFather](https://telegram.me/botfather).
    [Aquí](https://core.telegram.org/bots) tienes todo lo necesario que debes saber sobre 
    los [Bots de Telegram](https://core.telegram.org/bots)
3.  Una vez creado el bot tendrás una **clave API**. Esta clave es necesaria para que el 
    Bot se indentifique al enviar los mensajes.
4.  A continuación debes obtener un identificador de usuario llamando a la url
    https://api.telegram.org/bot_TU_API_KEY_/getUpdates
5.  Luego debes obtener el ID del canal. Y para ello deberas hacer público (momentaneamente)
    el canal y llamar a la siguiente url
    https://api.telegram.org/bot_ID_USUARIO:_TU_API_KEY_/sendMessage?chat_id=@_NOMBRE_DEL_CANAL&text="mensaje"
    Después ya puedes volver a poner el Canal como privado.
6.  Ya puedes enviar datos al Bot desde el Keylogger y este los publicará en el canal.

Tienes información detallada sobre este proceso 
[aquí](http://www.bernaerts-nicolas.fr/linux/75-debian/351-debian-send-telegram-notification)

 

 
 