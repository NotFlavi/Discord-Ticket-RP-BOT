from enum import member
import discord
from discord.ext import commands, tasks
from discord import File
from discord.ui import Button, View, Modal, TextInput
import json
import os
import datetime
import asyncio
import ffmpeg

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# Variabili di configurazione con ID anonimi o segnaposto
TICKETPANEL_CHANNEL_ID = 123456789012345678  # Sostituisci con il tuo ID reale
PANEL_MESSAGE_ID = 123456789012345678       # Sostituisci con il tuo ID reale
STAFF_ROLE_ID = 123456789012345678          # Sostituisci con il tuo ID reale
ARCHIVE_CHANNEL_ID = 123456789012345678     # Sostituisci con il tuo ID reale

# Carica il dizionario per i transcript dei ticket
if not os.path.isfile('transcripts.json'):
    with open('transcripts.json', 'w') as f:
        json.dump({}, f)

with open('transcripts.json', 'r') as f:
    transcripts = json.load(f)

CATEGORY_IDS = {
    "ticket_generale": 123456789012345678,   # Sostituisci con il tuo ID reale
    "ticket_donazione": 123456789012345678,  # Sostituisci con il tuo ID reale
    "ticket_unban": 123456789012345678,      # Sostituisci con il tuo ID reale
    "ticket_perm": 123456789012345678,       # Sostituisci con il tuo ID reale
    "ticket_vip": 123456789012345678,        # Sostituisci con il tuo ID reale
    "ticket_dev": 123456789012345678,        # Sostituisci con il tuo ID reale
    "ticket_mapper": 123456789012345678,     # Sostituisci con il tuo ID reale
    "ticket_ss": 123456789012345678,         # Sostituisci con il tuo ID reale
    "ticket_packunban": 123456789012345678,  # Sostituisci con il tuo ID reale
    "ticket_handler": 123456789012345678,    # Sostituisci con il tuo ID reale
}

# Funzione per aggiornare l'embed con il pulsante per la creazione dei ticket
async def update_ticket_embed():
    global PANEL_MESSAGE_ID
    channel = bot.get_channel(TICKETPANEL_CHANNEL_ID)
    archive_channel = bot.get_channel(ARCHIVE_CHANNEL_ID)

    if not channel:
        print(f"Canale con ID {TICKETPANEL_CHANNEL_ID} non trovato.")
        return
    
    try:
        # Prova a recuperare il messaggio esistente
        existing_message = await channel.fetch_message(PANEL_MESSAGE_ID)
    except discord.NotFound:
        existing_message = None

    if existing_message:
        print("Il messaggio del pannello ticket esiste già, nessuna azione necessaria.")
        return  # Esce dalla funzione se il messaggio esiste

    # Crea e invia un nuovo messaggio embed se il messaggio esistente non è stato trovato
    embed = discord.Embed(
        title="Alboz Tickets",
        description=(
            "📣 Ticket Generale: Crea un ticket per questioni generali.\n\n"
            "❌ Richiesta Unban: Richiedi unban se ritieni di essere stato bannato per errore.\n\n"
            "🎁 Donazione: Richiedi assistenza su donazioni e acquisti nello store.\n\n"
            "💀 Richiesta Permadeath: Richiedi il permadeath di un personaggio con motivazioni valide.\n\n"
            "💎 Vip: Supporto dedicato ai VIP che hanno acquistato il pack VIP.\n\n"
            "💻 Developer: Segnala bug o richiedi assistenza da uno sviluppatore.\n\n"
            "🏡 Mapper: Richiedi l'aggiunta di oggetti in gioco con l'aiuto di un mapper.\n\n"
            "🔍 SS Team: Contatta il SS Team per comunicazioni e assistenza.\n\n"
            "🎟 Pack Unban: Richiedi assistenza per i pack unban acquistati dal sito.\n\n"
            "🚗 Handler: Richiedi assistenza per questioni relative ai veicoli.\n\n"
        ),
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url="https://example.com/image.png")
    embed.set_footer(text="Usa i pulsanti sottostanti per aprire i ticket - Bot ideato da Barbara D'urso COL CUOREEEEE")

    view = View()
    buttons = [
        ("📣 Ticket Generale", "ticket_generale"),
        ("💸 Donazione", "ticket_donazione"),
        ("❌ Unban", "ticket_unban"),
        ("💀 PermaDeath", "ticket_perm"),
        ("💎 Vip", "ticket_vip"),
        ("💻 Developer", "ticket_dev"),
        ("🗺️ Mapper", "ticket_mapper"),
        ("🔍 SS Team", "ticket_ss"),
        ("🎫 Pack Unban", "ticket_packunban"),
        ("🚗 Handler", "ticket_handler"),
    ]
    for label, custom_id in buttons:
        button = Button(label=label, style=discord.ButtonStyle.primary, custom_id=custom_id)
        view.add_item(button)

    message = await channel.send(embed=embed, view=view)
    PANEL_MESSAGE_ID = message.id

    # Manda un avviso nel canale di archivio se è stato creato un nuovo messaggio
    if archive_channel:
        await archive_channel.send(f"Nuovo messaggio del pannello ticket creato con ID: {PANEL_MESSAGE_ID}")
    else:
        print(f"Canale di archivio con ID {ARCHIVE_CHANNEL_ID} non trovato.")

# Funzione per creare un ticket privato con un embed specifico nella categoria giusta
async def crea_ticket(interaction: discord.Interaction, category_name: str, embed_title: str, embed_desc: str, category_id: int):
    category = bot.get_channel(category_id)
    if not category:
        await interaction.response.send_message("Categoria dei ticket non trovata.", ephemeral=True)
        return

    # Crea un canale testuale privato per il ticket nella categoria specificata
    ticket_channel = await category.guild.create_text_channel(
        name=f"{category_name}-{interaction.user.name}",
        category=category,
        overwrites={
            interaction.user: discord.PermissionOverwrite(send_messages=True, read_messages=True),
            category.guild.default_role: discord.PermissionOverwrite(send_messages=False, read_messages=False),
            discord.utils.get(category.guild.roles, id=STAFF_ROLE_ID): discord.PermissionOverwrite(send_messages=True, read_messages=True)
        }
    )

    # Salva l'ID dell'utente nel file transcripts.json
    transcript_data = transcripts.get(str(ticket_channel.id), {})
    transcript_data["user_id"] = interaction.user.id
    transcripts[str(ticket_channel.id)] = transcript_data
    with open('transcripts.json', 'w') as f:
        json.dump(transcripts, f)

    embed = discord.Embed(
        title=embed_title,
        description=embed_desc,
        color=discord.Color.green()
    )
    embed.set_footer(text="Premi il pulsante qui sotto per chiudere il ticket.")

    button = Button(label="Chiudi Ticket", custom_id="chiudi_ticket")
    view = View()
    view.add_item(button)

    await ticket_channel.send(embed=embed, view=view)
    await interaction.response.send_message(f"Il tuo ticket è stato creato: {ticket_channel.mention}", ephemeral=True)

# Gestore dell'interazione con il pulsante
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component:
        custom_id = interaction.data['custom_id']

        if custom_id in CATEGORY_IDS:
            await crea_ticket(
                interaction,
                category_name=custom_id.replace("ticket_", ""),
                embed_title=f"{custom_id.replace('ticket_', '').capitalize()} Support",
                embed_desc=f"Un membro del supporto sarà con te a breve per assistenza riguardo a {custom_id.replace('ticket_', '').capitalize()}.",
                category_id=CATEGORY_IDS[custom_id]
            )
        elif custom_id == "chiudi_ticket":
            await chiudi_ticket(interaction)

# Funzione per chiudere il ticket
async def chiudi_ticket(interaction: discord.Interaction):
    try:
        if isinstance(interaction.channel, discord.TextChannel):
            print(f"Sto tentando di chiudere il ticket nel canale: {interaction.channel.name}")

            # Salva il transcript del canale
            transcript_file_path = await salva_transcript(interaction.channel)

            # Ottieni l'ID dell'utente che ha aperto il ticket
            ticket_id = interaction.channel.id
            user_id = transcripts.get(str(ticket_id), {}).get("user_id")
            user = interaction.channel.guild.get_member(user_id)
            user_dm = None
            
            if user:
                user_dm = await user.create_dm()  # Crea una DM se non esiste

            # Crea l'embed per l'archiviazione
            embed = discord.Embed(
                title="Ticket Chiuso",
                description=f"Il ticket aperto da <@{user_id}> è stato chiuso da {interaction.user.mention}.",
                color=discord.Color.red()
            )
            embed.add_field(name="Data e Ora di Chiusura", value=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            embed.set_footer(text=f"Ticket ID: {interaction.channel.id}")

            # Invia l'embed e il file di transcript nel canale di archivio
            archive_channel = bot.get_channel(ARCHIVE_CHANNEL_ID)
            if archive_channel:
                file = File(transcript_file_path)
                await archive_channel.send(embed=embed, file=file)
                print(f"Transcript salvato nel canale di archivio: {archive_channel.name}")
            else:
                print(f"Canale di archivio con ID {ARCHIVE_CHANNEL_ID} non trovato.")
            
            # Invia il transcript anche all'utente, se è disponibile
            if user_dm:
                await user_dm.send("Il tuo ticket è stato chiuso. Ecco una copia del transcript.", file=File(transcript_file_path))
                print(f"Transcript inviato all'utente {user.name} tramite DM.")

            # Elimina il canale del ticket
            await interaction.channel.delete()
            print(f"Canale del ticket {interaction.channel.name} eliminato.")
        else:
            print("Il comando non è stato eseguito in un canale testuale valido.")
    except Exception as e:
        print(f"Errore durante la chiusura del ticket: {e}")
        await interaction.response.send_message("Si è verificato un errore durante la chiusura del ticket. Contatta un amministratore.", ephemeral=True)

# Funzione per salvare il transcript del canale
async def salva_transcript(channel: discord.TextChannel):
    transcript_file_path = f'transcript_{channel.name}.txt'
    with open(transcript_file_path, 'w', encoding='utf-8') as f:
        async for message in channel.history(limit=None, oldest_first=True):
            f.write(f"[{message.created_at}] {message.author}: {message.content}\n")
    return transcript_file_path

@bot.event
async def on_ready():
    print(f"{bot.user} è online e pronto per l'uso!")
    await update_ticket_embed()

# Sostituisci con il tuo token reale
bot.run('YOUR_BOT_TOKEN')
