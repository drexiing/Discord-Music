import wavelink
import sys
import os

from dotenv import load_dotenv

load_dotenv(".env")
wavelink_uri = os.getenv("WAVELINK_URI")
wavelink_password = os.getenv("WAVELINK_PASSWORD")

if not wavelink_uri:
    print("\033[1;31m[Dotenv] La URI de Wavelink no está configurada como una variable de entorno")
    sys.exit(1)

if not wavelink_password:
    print("\033[1;31m[Dotenv] La contraseña de Wavelink no está configurada como una variable de entorno")
    sys.exit(1)

async def node_connect(bot):
    await bot.wait_until_ready()
   
    node = wavelink.Node(
       uri=wavelink_uri,
       password=wavelink_password
    )
    
    try:
        await wavelink.Pool.connect(client=bot, nodes=[node])
    except wavelink.AuthorizationFailedException:
        print("\033[1;31m[Lavalink] La contraseña del nodo es incorrecta")
    except wavelink.InvalidClientException:
        print("\033[1;31m[Lavalink] El cliente no es válido")
    except wavelink.NodeException:
        print("\033[1;31m[Lavalink] Error al conectarse al nodo")