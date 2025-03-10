# Discord-Music

## Acerca de

**Discord-Music** es un bot simple de Discord creado con las librerías de [discord.py](https://github.com/Rapptz/discord.py) y [Wavelink](https://github.com/PythonistaGuild/Wavelink) que permite reproducir música de YouTube/YouTubeMusic.

## Instalación

> [!IMPORTANT]
> **Se requiere Python 3.8 o superior**

### Instalación de dependencias
```bash
pip install -r requirements.txt
```

### Crea y configura el archivo .env
```env
# Configuración del bot de Discord
TOKEN=tu_token_del_bot_de_discord

# Configuración de Wavelink
WAVELINK_URI=tu_uri_de_wavelink_aquí
WAVELINK_PASSWORD=tu_contraseña_de_wavelink_aquí
```

> [!IMPORTANT]
> **El nodo de Lavalink debe tener activada la búsqueda de YouTube/YouTubeMusic. Recomiendo el uso de [youtube-source](https://github.com/lavalink-devs/youtube-source) y [LavaSrc](https://github.com/topi314/LavaSrc) como plugins para que funcione correctamente todo.**

## Creditos

- [discord.py](https://github.com/Rapptz/discord.py)
- [Wavelink](https://github.com/PythonistaGuild/Wavelink)