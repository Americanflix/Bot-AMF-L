# leech_bot.py - MODO MAGNET ONLY OTIMIZADO (Pella)
import os
import re
import subprocess
import shutil
from pyrogram import Client, filters
from pyrogram.types import Message

print("🚀 Leech Bot iniciado (modo MAGNET ONLY otimizado)...")

# Telegram API
api_id = 29878022
api_hash = "4d008189bd4b0ef6e3f6d2d38a03cd6b"
bot_token = "8156217296:AAF6AgqinY9mafzc4P1LNQ4FlllaWUWbRZ8"

# Limite de upload seguro (em MB e bytes)
UPLOAD_LIMIT_MB = 1536  # 1.5GB
UPLOAD_LIMIT = UPLOAD_LIMIT_MB * 1024 * 1024

# Extensões permitidas
EXTENSOES_VALIDAS = [".mp4", ".mkv"]

app = Client("leech_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

def human_readable(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024

@app.on_message(filters.command("leech") & filters.private)
def leech_file(client, message: Message):
    if len(message.command) < 2:
        return message.reply("❌ Use: /leech <magnet link>")

    url = message.command[1]
    if not url.startswith("magnet:?"):
        return message.reply("❌ Isso só aceita links *magnet:* por enquanto.")

    status = message.reply("📥 Iniciando o download...")

    download_path = "./downloads"
    shutil.rmtree(download_path, ignore_errors=True)  # limpa antes
    os.makedirs(download_path, exist_ok=True)

    try:
        process = subprocess.Popen(
            [
                "aria2c",
                f"--dir={download_path}",
                "--seed-time=0",
                "--bt-max-peers=4",
                "--enable-dht=false",
                "--disable-ipv6",
                "--summary-interval=1",
                "--console-log-level=notice",
                "--max-connection-per-server=2",
                "--disk-cache=2M",
                url
            ],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )

        for line in iter(process.stdout.readline, ''):
            if "DL:" in line and "ETA" in line:
                try:
                    match = re.search(r"(\d+)%", line)
                    if match:
                        percent = match.group(1)
                        status.edit_text(f"📥 {percent}%")
                except:
                    pass

        process.wait()
        if process.returncode != 0:
            return status.edit("❌ Falha ao baixar o magnet.")
    except Exception as e:
        return status.edit(f"❌ Erro ao baixar: {e}")

    arquivos = []
    for root, _, files in os.walk(download_path):
        for nome in files:
            caminho = os.path.join(root, nome)
            tamanho = os.path.getsize(caminho)
            if tamanho == 0:
                continue
            if os.path.splitext(nome)[1].lower() not in EXTENSOES_VALIDAS:
                continue
            if tamanho <= UPLOAD_LIMIT:
                arquivos.append((caminho, nome, tamanho))

    if not arquivos:
        shutil.rmtree(download_path, ignore_errors=True)
        return status.edit(f"❌ Nenhum arquivo `.mp4` ou `.mkv` válido encontrado dentro do limite de {UPLOAD_LIMIT_MB}MB.")

    # Seleciona o maior dentro do limite
    arquivo_final = max(arquivos, key=lambda x: x[2])  # (path, nome, tamanho)
    caminho, nome, tamanho = arquivo_final

    try:
        with open(caminho, "rb") as f:
            message.reply_document(
                document=f,
                caption=f"📁 {nome} ({human_readable(tamanho)}) enviado com sucesso!"
            )
        status.delete()
    except Exception as e:
        status.edit(f"❌ Erro ao enviar: {e}")
    finally:
        shutil.rmtree(download_path, ignore_errors=True)  # limpeza final

@app.on_message(filters.command("start"))
def start_command(client, message):
    message.reply("🤖 Bot online! Envie um link `/leech <magnet>` para começar.")

app.run()
