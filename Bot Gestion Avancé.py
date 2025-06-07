import discord
import json
from datetime import datetime
from datetime import timedelta
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Select, Button, Modal, TextInput
import re
import random
import asyncio

# ID du Buyer (l'admin de la whitelist)
BUYER_ID = {1305151957547221113, 690978270233100398} 

giveaways = {}  # Stocke les giveaways avec un index unique

# Chargement de la config du joiner
def load_joiner():
    try:
        with open("joiner.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Sauvegarde de la config du joiner
def save_joiner(data):
    with open("joiner.json", "w") as file:
        json.dump(data, file, indent=4)

# Chargement des warns
def load_warns():
    try:
        with open("warns.json", "r") as file:
            return json.load(file).get("warns", {})
    except FileNotFoundError:
        return {}

# Sauvegarde des warns
def save_warns(warns):
    with open("warns.json", "w") as file:
        json.dump({"warns": warns}, file, indent=4)

# Chargement des membres whitelistés
def load_whitelist():
    try:
        with open("whitelist.json", "r") as file:
            data = json.load(file)
            return data.get("whitelisted", [])
    except FileNotFoundError:
        return []

def save_whitelist(wl_list):
    with open("whitelist.json", "w") as file:
        json.dump({"whitelisted": wl_list}, file, indent=4)

# Initialisation du bot
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
bot = commands.Bot(command_prefix="!", intents=intents)

# Dictionnaire pour stocker le dernier message supprimé par salon
snipe_cache = {}

@bot.event
async def on_message_delete(message):
    if message.author.bot:  # Ignore les messages des bots
        return

    # Stocke les informations du message supprimé
    snipe_cache[message.channel.id] = {
        "content": message.content or "*Aucun texte*",
        "author": message.author,
        "time": message.created_at,
        "attachments": [att.url for att in message.attachments] if message.attachments else []  # Liste des images
    }

@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")
    await bot.tree.sync()

@bot.tree.command(name="buyerlist", description="Affiche la liste des buyers du bot.")
async def buyerlist(interaction: discord.Interaction):
    wl_list = load_whitelist()  # Charge la whitelist
    buyer_list = [1305151957547221113, 690978270233100398]  # Liste des buyers (à compléter)

    # Vérifie si l'utilisateur est un buyer
    if interaction.user.id not in buyer_list:
        embed = discord.Embed(
            title="⛔ Accès refusé",
            description="Tu n'as pas la permission d'utiliser cette commande.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Affiche tous les buyers
    buyer_mentions = [f"<@{buyer_id}>" for buyer_id in buyer_list]
    embed = discord.Embed(
        title="👑 Liste des Buyers",
        description="\n".join(buyer_mentions) if buyer_mentions else "Aucun buyer trouvé.",
        color=discord.Color.gold()
    )
    embed.set_footer(text="Liste des buyers officiels du bot.")

    await interaction.response.send_message(embed=embed, ephemeral=True)

# Commande /wl (ajouter à la whitelist)
@bot.tree.command(name="wl", description="Ajoute un membre à la whitelist")
@app_commands.describe(membre="Le membre à whitelister")
async def wl(interaction: discord.Interaction, membre: discord.Member):
    if interaction.user.id != BUYER_ID:
        embed = discord.Embed(title="⛔ Permission refusée", description="Vous n'avez pas accès à cette commande.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    whitelist = load_whitelist()
    if membre.id in whitelist:
        embed = discord.Embed(title="ℹ️ Déjà whitelisté", description=f"{membre.mention} est déjà whitelisté.", color=discord.Color.blue())
    else:
        whitelist.append(membre.id)
        save_whitelist(whitelist)
        embed = discord.Embed(title="✅ Whitelist ajouté", description=f"{membre.mention} a été ajouté à la whitelist.", color=discord.Color.green())

    await interaction.response.send_message(embed=embed, ephemeral=True)

# Commande /unwl (retirer de la whitelist)
@bot.tree.command(name="unwl", description="Retire un membre de la whitelist")
@app_commands.describe(membre="Le membre à retirer de la whitelist")
async def unwl(interaction: discord.Interaction, membre: discord.Member):
    if interaction.user.id != BUYER_ID:
        embed = discord.Embed(title="⛔ Permission refusée", description="Vous n'avez pas accès à cette commande.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    whitelist = load_whitelist()
    if membre.id not in whitelist:
        embed = discord.Embed(title="ℹ️ Non whitelisté", description=f"{membre.mention} n'est pas dans la whitelist.", color=discord.Color.blue())
    else:
        whitelist.remove(membre.id)
        save_whitelist(whitelist)
        embed = discord.Embed(title="✅ Whitelist retiré", description=f"{membre.mention} a été retiré de la whitelist.", color=discord.Color.green())

    await interaction.response.send_message(embed=embed, ephemeral=True)

# Commande /wlist (afficher la whitelist)
@bot.tree.command(name="wlist", description="Affiche la liste des membres whitelistés")
async def wlist(interaction: discord.Interaction):
    if interaction.user.id != BUYER_ID and interaction.user.id not in load_whitelist():
        embed = discord.Embed(title="⛔ Permission refusée", description="Vous n'avez pas accès à cette commande.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    whitelist = load_whitelist()
    if not whitelist:
        description = "Aucun membre n'est whitelisté."
    else:
        description = "\n".join([f"<@{user_id}>" for user_id in whitelist])

    embed = discord.Embed(title="📜 Liste des whitelistés", description=description, color=discord.Color.blue())
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ✅ Déplacement de can_warn() ici !
def can_warn(user_id):
    return user_id == BUYER_ID or user_id in load_whitelist()

# Commande /warn (ajouter un avertissement)
@bot.tree.command(name="warn", description="Ajoute un avertissement à un membre")
@app_commands.describe(membre="Le membre à avertir", raison="Raison de l'avertissement")
async def warn(interaction: discord.Interaction, membre: discord.Member, raison: str):
    if not can_warn(interaction.user.id):
        embed = discord.Embed(title="⛔ Permission refusée", description="Vous n'avez pas accès à cette commande.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return

    warns = load_warns()
    user_warns = warns.get(str(membre.id), [])

    # Ajouter le warn avec l'auteur et la date
    new_warn = {
        "raison": raison,
        "warned_by": interaction.user.id,
        "date": datetime.now().strftime("%d %B %Y")  # Format: "10 février 2025"
    }
    user_warns.append(new_warn)
    warns[str(membre.id)] = user_warns
    save_warns(warns)

    embed = discord.Embed(title="⚠️ Avertissement", description=f"{membre.mention} a été averti.", color=discord.Color.orange())
    embed.add_field(name="Raison", value=raison, inline=False)
    embed.add_field(name="Averti par", value=interaction.user.mention, inline=False)
    embed.add_field(name="Date", value=new_warn["date"], inline=False)
    embed.add_field(name="Nombre total d'avertissements", value=len(user_warns), inline=False)

    await interaction.response.send_message(embed=embed)

# Commande /unwarn (retirer un avertissement)
@bot.tree.command(name="unwarn", description="Retire un avertissement d'un membre")
@app_commands.describe(membre="Le membre dont retirer un avertissement", index="Index du warn à retirer")
async def unwarn(interaction: discord.Interaction, membre: discord.Member, index: int):
    if not can_warn(interaction.user.id):
        embed = discord.Embed(title="⛔ Permission refusée", description="Vous n'avez pas accès à cette commande.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return

    warns = load_warns()
    user_warns = warns.get(str(membre.id), [])

    if index < 1 or index > len(user_warns):
        embed = discord.Embed(title="❌ Index invalide", description="Aucun avertissement à cet index.", color=discord.Color.red())
    else:
        removed_warn = user_warns.pop(index - 1)
        warns[str(membre.id)] = user_warns
        save_warns(warns)

        embed = discord.Embed(title="✅ Avertissement retiré", description=f"L'avertissement n°{index} de {membre.mention} a été supprimé.", color=discord.Color.green())
        embed.add_field(name="Raison supprimée", value=removed_warn["raison"], inline=False)
        embed.add_field(name="Averti par", value=f"<@{removed_warn['warned_by']}>", inline=False)
        embed.add_field(name="Date", value=removed_warn["date"], inline=False)

    await interaction.response.send_message(embed=embed)

# Commande /warnlist (afficher les avertissements avec raison, auteur et date)
@bot.tree.command(name="warnlist", description="Affiche la liste des avertissements d'un membre")
@app_commands.describe(membre="Le membre dont afficher les avertissements")
async def warnlist(interaction: discord.Interaction, membre: discord.Member):
    if not can_warn(interaction.user.id):
        embed = discord.Embed(title="⛔ Permission refusée", description="Vous n'avez pas accès à cette commande.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return

    warns = load_warns()
    user_warns = warns.get(str(membre.id), [])

    if not user_warns:
        description = f"{membre.mention} n'a aucun avertissement."
    else:
        description = "\n".join([
            f"**{i+1}.** {warn['raison']} *(par <@{warn['warned_by']}> le {warn['date']})*"
            for i, warn in enumerate(user_warns)
        ])

    embed = discord.Embed(title=f"📜 Avertissements de {membre.display_name}", description=description, color=discord.Color.blue())
    await interaction.response.send_message(embed=embed)

# Vérifier si un membre peut configurer
def can_configure(user_id):
    return user_id == BUYER_ID or user_id in load_whitelist()

# 📌 Sélecteur de configuration
class JoinerSelect(discord.ui.Select):
    def __init__(self, guild_id):
        self.guild_id = guild_id
        options = [
            discord.SelectOption(label="Modifier le salon", description="Choisir où envoyer le message"),
            discord.SelectOption(label="Modifier le rôle", description="Définir le rôle des nouveaux"),
            discord.SelectOption(label="Modifier le message", description="Personnaliser le message d'arrivée")
        ]
        super().__init__(placeholder="Choisissez une option...", options=options)

    async def callback(self, interaction: discord.Interaction):
        if not can_configure(interaction.user.id):
            await interaction.response.send_message("⛔ Vous n'avez pas accès à cette commande.", ephemeral=True)
            return

        joiner_data = load_joiner()
        if str(self.guild_id) not in joiner_data:
            joiner_data[str(self.guild_id)] = {"channel_id": None, "role_id": None, "welcome_message": "Bienvenue {user} sur {guild} ! 🎉"}

        # Configuration en fonction du choix
        if self.values[0] == "Modifier le salon":
            await interaction.response.send_message("📢 **Mentionnez le salon où envoyer le message de bienvenue :**", ephemeral=True)

            def check(msg):
                return msg.author == interaction.user and msg.guild is not None and len(msg.channel_mentions) > 0

            msg = await bot.wait_for("message", check=check)
            joiner_data[str(self.guild_id)]["channel_id"] = msg.channel_mentions[0].id
            save_joiner(joiner_data)
            await msg.add_reaction("✅")

        elif self.values[0] == "Modifier le rôle":
            await interaction.response.send_message("🎭 **Mentionnez le rôle à donner aux nouveaux membres :**", ephemeral=True)

            def check(msg):
                return msg.author == interaction.user and msg.guild is not None and len(msg.role_mentions) > 0

            msg = await bot.wait_for("message", check=check)
            joiner_data[str(self.guild_id)]["role_id"] = msg.role_mentions[0].id
            save_joiner(joiner_data)
            await msg.add_reaction("✅")

        elif self.values[0] == "Modifier le message":
            await interaction.response.send_message(
                "✍️ **Envoyez le message de bienvenue personnalisé.**\n"
                "Utilisez `{user}` pour mentionner l'utilisateur, `{guild}` pour le nom du serveur et `{member_count}` pour le nombre de membres.",
                ephemeral=True
            )

            def check(msg):
                return msg.author == interaction.user and msg.guild is not None

            msg = await bot.wait_for("message", check=check)
            joiner_data[str(self.guild_id)]["welcome_message"] = msg.content
            save_joiner(joiner_data)
            await msg.add_reaction("✅")

# 📌 Vue contenant le sélecteur
class JoinerView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__()
        self.add_item(JoinerSelect(guild_id))

# 📜 Commande /joiner
@bot.tree.command(name="joiner", description="Configurer le système de bienvenue")
async def joiner(interaction: discord.Interaction):
    if not can_configure(interaction.user.id):
        await interaction.response.send_message("⛔ Vous n'avez pas accès à cette commande.", ephemeral=True)
        return

    joiner_data = load_joiner()
    guild_config = joiner_data.get(str(interaction.guild.id), {})

    channel_mention = f"<#{guild_config.get('channel_id', 'Non défini')}>" if guild_config.get("channel_id") else "Non défini"
    role_mention = f"<@&{guild_config.get('role_id', 'Non défini')}>" if guild_config.get("role_id") else "Non défini"
    welcome_message = guild_config.get("welcome_message", "Bienvenue {user} sur {guild} ! 🎉")

    embed = discord.Embed(title="⚙️ Configuration du système de bienvenue", color=discord.Color.blue())
    embed.add_field(name="📢 Salon", value=channel_mention, inline=False)
    embed.add_field(name="🎭 Rôle", value=role_mention, inline=False)
    embed.add_field(name="✍️ Message de bienvenue", value=welcome_message, inline=False)
    embed.set_footer(text="Utilisez le sélecteur ci-dessous pour modifier la configuration.")

    await interaction.response.send_message(embed=embed, view=JoinerView(interaction.guild.id))

# 📜 Commande /variable
@bot.tree.command(name="variable", description="Liste des variables pour le message de bienvenue")
async def variable(interaction: discord.Interaction):
    embed = discord.Embed(title="📌 Variables disponibles", color=discord.Color.green())
    embed.add_field(name="{user}", value="Mentionne le nouvel utilisateur", inline=False)
    embed.add_field(name="{guild}", value="Nom du serveur", inline=False)
    embed.add_field(name="{member_count}", value="Nombre total de membres", inline=False)
    await interaction.response.send_message(embed=embed)

# 📌 Événement quand un membre rejoint
@bot.event
async def on_member_join(member):
    joiner_data = load_joiner()
    guild_id = str(member.guild.id)

    if guild_id not in joiner_data:
        return  # Pas de configuration

    config = joiner_data[guild_id]
    channel = member.guild.get_channel(config["channel_id"])
    role = member.guild.get_role(config["role_id"])

    if channel:
        welcome_message = (
            config["welcome_message"]
            .replace("{user}", member.mention)
            .replace("{guild}", member.guild.name)
            .replace("{member_count}", str(member.guild.member_count))
        )
        await channel.send(welcome_message)

    if role:
        await member.add_roles(role)

# 📌 Événement quand un membre rejoint
@bot.event
async def on_member_join(member):
    joiner_data = load_joiner()
    guild_id = str(member.guild.id)

    if guild_id not in joiner_data:
        return  # Pas de configuration

    config = joiner_data[guild_id]
    channel = member.guild.get_channel(config["channel_id"])
    role = member.guild.get_role(config["role_id"])

    if channel:
        welcome_message = config["welcome_message"].replace("{user}", member.mention).replace("{guild}", member.guild.name).replace("{member_count}", str(member.guild.member_count))
        await channel.send(welcome_message)

# 📌 Vérifier si l'utilisateur peut utiliser la commande
def can_moderate(user_id):
    return user_id == BUYER_ID or user_id in load_whitelist()

# 📜 Commande /kick
@bot.tree.command(name="kick", description="Expulse un membre du serveur")
@app_commands.describe(membre="Le membre à expulser", raison="Raison de l'expulsion")
async def kick(interaction: discord.Interaction, membre: discord.Member, raison: str):
    if not can_moderate(interaction.user.id):
        await interaction.response.send_message("⛔ Vous n'avez pas accès à cette commande.", ephemeral=True)
        return

    # Vérifier si le bot peut kicker
    if not interaction.guild.me.guild_permissions.kick_members:
        await interaction.response.send_message("⚠️ Je n'ai pas la permission d'expulser des membres.", ephemeral=True)
        return

    # Vérifier que le bot peut kicker ce membre
    if interaction.guild.me.top_role <= membre.top_role:
        await interaction.response.send_message("⛔ Je ne peux pas expulser un membre ayant un rôle supérieur ou égal au mien.", ephemeral=True)
        return

    # Expulsion du membre
    try:
        await membre.kick(reason=raison)
        embed = discord.Embed(title="🔨 Membre Expulsé", color=discord.Color.orange())
        embed.add_field(name="👤 Membre", value=membre.mention, inline=True)
        embed.add_field(name="🛠️ Modérateur", value=interaction.user.mention, inline=True)
        embed.add_field(name="📜 Raison", value=raison, inline=False)
        await interaction.response.send_message(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message("⛔ Je n'ai pas la permission d'expulser ce membre.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Une erreur est survenue : {e}", ephemeral=True)

# 📜 Commande /ban
@bot.tree.command(name="ban", description="Bannit un membre du serveur")
@app_commands.describe(membre="Le membre à bannir", raison="Raison du bannissement")
async def ban(interaction: discord.Interaction, membre: discord.Member, raison: str):
    if not can_moderate(interaction.user.id):
        await interaction.response.send_message("⛔ Vous n'avez pas accès à cette commande.", ephemeral=True)
        return

    # Vérifier si le bot peut bannir
    if not interaction.guild.me.guild_permissions.ban_members:
        await interaction.response.send_message("⚠️ Je n'ai pas la permission de bannir des membres.", ephemeral=True)
        return

    # Vérifier que le bot peut bannir ce membre
    if interaction.guild.me.top_role <= membre.top_role:
        await interaction.response.send_message("⛔ Je ne peux pas bannir un membre ayant un rôle supérieur ou égal au mien.", ephemeral=True)
        return

    # Bannissement du membre
    try:
        await membre.ban(reason=raison)
        embed = discord.Embed(title="⛔ Membre Banni", color=discord.Color.red())
        embed.add_field(name="👤 Membre", value=membre.mention, inline=True)
        embed.add_field(name="🛠️ Modérateur", value=interaction.user.mention, inline=True)
        embed.add_field(name="📜 Raison", value=raison, inline=False)
        await interaction.response.send_message(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message("⛔ Je n'ai pas la permission de bannir ce membre.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Une erreur est survenue : {e}", ephemeral=True)

# 📌 Fonction pour convertir le temps en secondes
def parse_duration(duration: str):
    match = re.match(r"^(\d+)([smhd])$", duration)
    if not match:
        return None

    value, unit = int(match.group(1)), match.group(2)
    if unit == "s":
        return timedelta(seconds=value)
    elif unit == "m":
        return timedelta(minutes=value)
    elif unit == "h":
        return timedelta(hours=value)
    elif unit == "d":
        return timedelta(days=value)

# 📜 Commande /tempmute
@bot.tree.command(name="tempmute", description="Réduit au silence un membre temporairement (Timeout)")
@app_commands.describe(membre="Le membre à mute", duree="Durée (ex: 10m, 5h, 2d)", raison="Raison du mute")
async def tempmute(interaction: discord.Interaction, membre: discord.Member, duree: str, raison: str):
    if not can_moderate(interaction.user.id):
        await interaction.response.send_message("⛔ Vous n'avez pas accès à cette commande.", ephemeral=True)
        return

    # Vérifier si le bot a la permission de timeout
    if not interaction.guild.me.guild_permissions.moderate_members:
        await interaction.response.send_message("⚠️ Je n'ai pas la permission de mute.", ephemeral=True)
        return

    # Vérifier que le bot peut mute ce membre
    if interaction.guild.me.top_role <= membre.top_role:
        await interaction.response.send_message("⛔ Je ne peux pas mute un membre ayant un rôle supérieur ou égal au mien.", ephemeral=True)
        return

    # Vérifier que la durée est correcte
    delta = parse_duration(duree)
    if delta is None:
        await interaction.response.send_message("⛔ Format invalide ! Utilise : `10s`, `5m`, `3h`, `2d`.", ephemeral=True)
        return

    # Appliquer le timeout
    try:
        await membre.timeout(delta, reason=raison)
        embed = discord.Embed(title="🔇 Membre Muté Temporairement", color=discord.Color.blue())
        embed.add_field(name="👤 Membre", value=membre.mention, inline=True)
        embed.add_field(name="⏳ Durée", value=duree, inline=True)
        embed.add_field(name="🛠️ Modérateur", value=interaction.user.mention, inline=True)
        embed.add_field(name="📜 Raison", value=raison, inline=False)
        await interaction.response.send_message(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message("⛔ Je n'ai pas la permission de mute ce membre.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Une erreur est survenue : {e}", ephemeral=True)

# 📜 Commande /unmute
@bot.tree.command(name="unmute", description="Annule un mute temporaire")
@app_commands.describe(membre="Le membre à unmute")
async def unmute(interaction: discord.Interaction, membre: discord.Member):
    if not can_moderate(interaction.user.id):
        await interaction.response.send_message("⛔ Vous n'avez pas accès à cette commande.", ephemeral=True)
        return

    # Vérifier si le bot a la permission de gérer les mutes
    if not interaction.guild.me.guild_permissions.moderate_members:
        await interaction.response.send_message("⚠️ Je n'ai pas la permission d'unmute.", ephemeral=True)
        return

    # Vérifier si le membre est bien mute
    if membre.timed_out_until is None:
        await interaction.response.send_message("⛔ Ce membre n'est pas mute.", ephemeral=True)
        return

    # Retirer le timeout
    try:
        await membre.timeout(None, reason="Unmute par {}".format(interaction.user))
        embed = discord.Embed(title="🔊 Membre Unmute", color=discord.Color.green())
        embed.add_field(name="👤 Membre", value=membre.mention, inline=True)
        embed.add_field(name="🛠️ Modérateur", value=interaction.user.mention, inline=True)
        await interaction.response.send_message(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message("⛔ Je n'ai pas la permission d'unmute ce membre.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Une erreur est survenue : {e}", ephemeral=True)

# 📜 Commande /say
@bot.tree.command(name="say", description="Envoie un message en tant que bot")
@app_commands.describe(message="Le message à envoyer", salon="Le salon cible (optionnel)")
async def say(interaction: discord.Interaction, message: str, salon: discord.TextChannel = None):
    if not can_moderate(interaction.user.id):
        await interaction.response.send_message("⛔ Vous n'avez pas accès à cette commande.", ephemeral=True)
        return

    # Déterminer le salon d'envoi
    salon = salon or interaction.channel

    # Vérifier si le bot peut envoyer un message dans ce salon
    if not salon.permissions_for(interaction.guild.me).send_messages:
        await interaction.response.send_message(f"⚠️ Je ne peux pas envoyer de message dans {salon.mention}.", ephemeral=True)
        return

    # Envoyer le message
    try:
        await salon.send(message)
        await interaction.response.send_message(f"✅ Message envoyé dans {salon.mention} !", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Une erreur est survenue : {e}", ephemeral=True)

def can_use_embed(user_id):
    wl_list = load_whitelist()  # Charge la whitelist
    buyer_list = [1305151957547221113]  # ID du buyer
    return user_id in wl_list or user_id in buyer_list

class EmbedConfigurator(View):
    def __init__(self, interaction):
        super().__init__(timeout=300)
        self.interaction = interaction
        self.embed_data = {"title": "", "description": "", "color": 0x3498db, "image": "", "thumbnail": "", "footer": ""}
        self.channel = interaction.channel

    @discord.ui.select(
        placeholder="Choisissez une option",
        options=[
            discord.SelectOption(label="Titre", value="title"),
            discord.SelectOption(label="Description", value="description"),
            discord.SelectOption(label="Couleur", value="color"),
            discord.SelectOption(label="Image", value="image"),
            discord.SelectOption(label="Thumbnail", value="thumbnail"),
            discord.SelectOption(label="Footer", value="footer"),
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: Select):
        await interaction.response.send_message(f"Entrez la valeur pour **{select.values[0]}**.", ephemeral=True)

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        try:
            msg = await interaction.client.wait_for("message", check=check, timeout=60)
            if select.values[0] == "color":
                try:
                    self.embed_data["color"] = int(msg.content.replace("#", ""), 16)
                except ValueError:
                    await interaction.followup.send("❌ Couleur invalide ! Utilisez un hexadécimal (ex: `#3498db`).", ephemeral=True)
                    return
            else:
                self.embed_data[select.values[0]] = msg.content

            await interaction.followup.send(f"✅ **{select.values[0]}** mis à jour !", ephemeral=True)
        except TimeoutError:
            await interaction.followup.send("⏳ Temps écoulé !", ephemeral=True)

    @discord.ui.button(label="✅ Envoyer l'embed", style=discord.ButtonStyle.green)
    async def send_embed(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title=self.embed_data["title"],
            description=self.embed_data["description"],
            color=self.embed_data["color"]
        )

        if self.embed_data["image"]:
            embed.set_image(url=self.embed_data["image"])
        if self.embed_data["thumbnail"]:
            embed.set_thumbnail(url=self.embed_data["thumbnail"])
        if self.embed_data["footer"]:
            embed.set_footer(text=self.embed_data["footer"])

        await self.channel.send(embed=embed)
        await interaction.response.send_message("✅ Embed envoyé !", ephemeral=True)

@bot.tree.command(name="embed", description="Créer un embed personnalisé")
async def embed(interaction: discord.Interaction):
    if not can_use_embed(interaction.user.id):
        await interaction.response.send_message("❌ Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)
        return

    view = EmbedConfigurator(interaction)
    await interaction.response.send_message("🎨 **Configurer votre embed :**", view=view, ephemeral=False)


@bot.tree.command(name="userinfo", description="Affiche les informations d'un utilisateur.")
@app_commands.describe(member="L'utilisateur dont vous voulez voir les informations.")
async def userinfo(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user  # Si aucun membre n'est précisé, affiche les infos de l'utilisateur qui tape la commande.

    embed = discord.Embed(title=f"Informations de {member}", color=discord.Color.blue())

    # Informations de base
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.add_field(name="👤 Nom d'utilisateur", value=member.name, inline=True)
    embed.add_field(name="🏷️ Pseudo serveur", value=member.nick or "Aucun", inline=True)
    embed.add_field(name="🆔 ID", value=member.id, inline=False)

    # Dates importantes
    embed.add_field(name="📅 Compte créé le", value=member.created_at.strftime("%d/%m/%Y à %H:%M:%S"), inline=True)
    embed.add_field(name="📥 A rejoint le serveur le", value=member.joined_at.strftime("%d/%m/%Y à %H:%M:%S") if member.joined_at else "Inconnu", inline=True)

    # Statut & activité
    embed.add_field(name="🟢 Statut", value=str(member.status).capitalize(), inline=True)
    embed.add_field(name="🎮 Activité", value=member.activity.name if member.activity else "Aucune", inline=True)

    # Rôles
    roles = [role.mention for role in member.roles if role.name != "@everyone"]
    embed.add_field(name="🎭 Rôles", value=", ".join(roles) if roles else "Aucun", inline=False)

    # Affichage de l'embed
    await interaction.response.send_message(embed=embed, ephemeral=False)


@bot.tree.command(name="infoserveur", description="Affiche les informations du serveur.")
async def infoserveur(interaction: discord.Interaction):
    guild = interaction.guild  # Récupération du serveur

    embed = discord.Embed(title=f"📜 Informations du serveur : {guild.name}", color=discord.Color.blue())

    # Icone du serveur
    embed.set_thumbnail(url=guild.icon.url if guild.icon else "")

    # Informations générales
    embed.add_field(name="🆔 ID du serveur", value=guild.id, inline=True)
    embed.add_field(name="👑 Propriétaire", value=guild.owner.mention, inline=True)
    embed.add_field(name="🌍 Région", value=guild.preferred_locale, inline=True)

    # Statistiques des membres
    embed.add_field(name="👥 Membres", value=guild.member_count, inline=True)

    # Statistiques des salons
    text_channels = len(guild.text_channels)
    voice_channels = len(guild.voice_channels)
    embed.add_field(name="💬 Salons textuels", value=text_channels, inline=True)
    embed.add_field(name="🔊 Salons vocaux", value=voice_channels, inline=True)

    # Statistiques des rôles & boosts
    embed.add_field(name="🎭 Nombre de rôles", value=len(guild.roles), inline=True)
    embed.add_field(name="🚀 Niveau de boost", value=guild.premium_tier, inline=True)
    embed.add_field(name="💎 Boosts Nitro", value=guild.premium_subscription_count, inline=True)

    # Dates importantes
    embed.add_field(name="📅 Créé le", value=guild.created_at.strftime("%d/%m/%Y à %H:%M:%S"), inline=True)

    # Envoi de l'embed
    await interaction.response.send_message(embed=embed, ephemeral=False)

@bot.tree.command(name="avatar", description="Affiche l'avatar d'un utilisateur.")
@app_commands.describe(user="L'utilisateur dont vous voulez voir l'avatar.")
async def avatar(interaction: discord.Interaction, user: discord.Member = None):
    user = user or interaction.user  # Si aucun utilisateur n'est mentionné, on prend celui qui fait la commande

    embed = discord.Embed(title=f"🖼 Avatar de {user.display_name}", color=discord.Color.blue())
    embed.set_image(url=user.avatar.url if user.avatar else user.default_avatar.url)

    await interaction.response.send_message(embed=embed, ephemeral=False)


@bot.tree.command(name="baniere", description="Affiche la bannière d'un utilisateur.")
@app_commands.describe(user="L'utilisateur dont vous voulez voir la bannière.")
async def baniere(interaction: discord.Interaction, user: discord.Member = None):
    user = user or interaction.user  # Si aucun utilisateur n'est mentionné, on prend celui qui fait la commande

    # Récupération des données du membre
    user_data = await bot.fetch_user(user.id)

    # Vérifier si l'utilisateur a une bannière
    if user_data.banner:
        banner_url = user_data.banner.url
        embed = discord.Embed(title=f"🎨 Bannière de {user.display_name}", color=discord.Color.blue())
        embed.set_image(url=banner_url)
        await interaction.response.send_message(embed=embed, ephemeral=False)
    else:
        await interaction.response.send_message(f"❌ {user.display_name} n'a pas de bannière.", ephemeral=True)

def can_use_command(user_id):
    wl_list = load_whitelist()  # Charge la whitelist
    buyer_list = [1305151957547221113]  # ID du buyer

    print(f"DEBUG | User ID: {user_id}")  # Affiche ton ID dans la console
    print(f"DEBUG | WL List: {wl_list}")  # Affiche la whitelist
    print(f"DEBUG | Buyer List: {buyer_list}")  # Affiche les buyers

    return str(user_id) in wl_list or user_id in buyer_list

@bot.tree.command(name="clear", description="Supprime le nombre de messages demandé")
@app_commands.describe(nombre="Nombre de messages à supprimer (max 100)")
async def clear(interaction: discord.Interaction, nombre: int):
    if not can_use_command(interaction.user.id):  # Vérifie la permission
        await interaction.response.send_message("❌ Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)
        return

    if nombre <= 0 or nombre > 100:
        await interaction.response.send_message("❌ Vous devez entrer un nombre entre **1 et 100**.", ephemeral=True)
        return

    deleted = await interaction.channel.purge(limit=nombre + 1)  # +1 pour supprimer la commande
    embed = discord.Embed(
        title="🗑️ Messages supprimés",
        description=f"{len(deleted) - 1} messages ont été supprimés par {interaction.user.mention}.",
        color=discord.Color.red()
    )
    await interaction.channel.send(embed=embed)  # Message public


# Liste de 50 blagues en français
blagues = [
    "Pourquoi les plongeurs plongent-ils toujours en arrière et jamais en avant ? Parce que sinon ils tombent dans le bateau.",
    "Quel est le comble pour un électricien ? De ne pas être au courant.",
    "Pourquoi les poissons n’aiment pas les ordinateurs ? À cause des nets.",
    "Pourquoi les squelettes ne se battent jamais entre eux ? Parce qu’ils n’ont pas les tripes.",
    "Quelle est la ville la plus sale ? Toulon, car tout l’on jette.",
    "Pourquoi le football c'est rigolo ? Parce que Thierry en rit.",
    "Pourquoi Napoléon n'a jamais déménagé ? Parce qu'il avait un Bonaparte.",
    "Quel est le comble pour un jardinier ? De raconter des salades.",
    "Pourquoi le pamplemousse est un fruit sympa ? Parce qu’il ne se prend pas pour une orange.",
    "Que dit une imprimante dans l’eau ? J’ai papier !",
    "Pourquoi les pommes ne parlent pas ? Parce qu’elles sont pressées.",
    "Pourquoi les vaches ferment-elles les yeux quand elles dorment ? Parce qu’elles font du lait de nuit.",
    "Pourquoi le chien traverse-t-il la route ? Pour aller à la niche d’en face.",
    "Quelle est la boisson préférée des électriciens ? Le jus d’orange.",
    "Que fait une fraise sur un cheval ? Tagada tagada tagada !",
    "Quel est le comble pour un ébéniste ? De ne pas être dans son assiette.",
    "Pourquoi les carottes ne bronzent jamais ? Parce qu’elles restent dans le frigo.",
    "Quel est le comble pour un dentiste ? De perdre la face.",
    "Quel est le fruit le plus énergique ? La pêche, elle a la patate !",
    "Pourquoi le coq chante-t-il les pieds dans le fumier ? Parce que ça lui met du baume au cœur.",
    "Pourquoi les chats n’aiment pas Internet ? Parce qu’ils ont peur des souris.",
    "Pourquoi les pêcheurs sont-ils de mauvais musiciens ? Parce qu’ils font trop de fausses notes.",
    "Pourquoi le livre de maths est triste ? Parce qu’il a trop de problèmes.",
    "Quel est le comble pour un plombier ? De se faire arnaquer et de se retrouver sans un sou.",
    "Pourquoi les plongeurs plongent-ils en arrière ? Parce que sinon, ils tombent dans le bateau.",
    "Quel est le comble pour un facteur ? De perdre son courrier.",
    "Pourquoi la tomate est-elle rouge ? Parce qu’elle a vu la salade se déshabiller.",
    "Pourquoi les plongeurs n’aiment pas les ascenseurs ? Parce qu’ils préfèrent la plongée libre.",
    "Pourquoi les chauves-souris aiment-elles la bière ? Parce qu’elles se pendent aux mousses.",
    "Pourquoi le coiffeur a-t-il raté son train ? Parce qu’il s’est coiffé au poteau.",
    "Pourquoi les fantômes aiment-ils les ascenseurs ? Parce qu’ils les hantent.",
    "Pourquoi les girafes ont-elles un long cou ? Parce qu’elles puent des pieds.",
    "Pourquoi les oiseaux volent-ils en groupe ? Parce qu’ils ont peur des avions.",
    "Pourquoi les pompiers portent-ils des bretelles rouges ? Pour tenir leur pantalon.",
    "Pourquoi les chouettes ne chantent-elles jamais faux ? Parce qu’elles ont du hibou.",
    "Pourquoi le soleil est jaune ? Parce que si c’était rouge, ce serait une tomate.",
    "Pourquoi les statues sont-elles muettes ? Parce qu’elles ont perdu leur langue.",
    "Pourquoi les poules n’aiment-elles pas les voitures ? Parce qu’elles ont peur de se faire écraser.",
    "Pourquoi le poisson rit-il dans l’eau ? Parce qu’il trouve ça poissonnant.",
    "Pourquoi les policiers aiment-ils les montres ? Parce qu’ils arrêtent le temps.",
    "Pourquoi les plongeurs plongent-ils dans l’eau froide ? Parce qu’ils ont chaud dehors.",
    "Pourquoi les éléphants n’aiment-ils pas jouer aux cartes ? Parce qu’ils ont peur de se faire tirer l’oreille.",
    "Pourquoi les vaches aiment-elles la musique ? Parce qu’elles trouvent ça vachement bien.",
    "Pourquoi les canards sont-ils de mauvais joueurs ? Parce qu’ils font tout le temps coin-coin.",
    "Pourquoi les abeilles bourdonnent-elles ? Parce qu’elles ne savent pas parler.",
    "Pourquoi les poissons sont-ils mauvais en mathématiques ? Parce qu’ils n’aiment pas les problèmes.",
    "Pourquoi les écureuils aiment-ils les arbres ? Parce qu’ils y trouvent leur noisette.",
    "Pourquoi les grenouilles n’aiment-elles pas les serpents ? Parce qu’ils leur coupent la parole."
]

@bot.tree.command(name="blague", description="Affiche une blague aléatoire.")
async def blague(interaction: discord.Interaction):
    joke = random.choice(blagues)  # Sélectionne une blague au hasard
    embed = discord.Embed(title="***__😂 Blague du jour !__***", description=joke, color=discord.Color.random())
    embed.set_footer(text="Blague créée par Yn.is95 & ChatGPT !")

    await interaction.response.send_message(embed=embed, ephemeral=False)


@bot.tree.command(name="renew", description="Supprime et recrée le salon actuel.")
async def renew(interaction: discord.Interaction):
    wl_list = load_whitelist()  # Charge la whitelist
    buyer_list = [1305151957547221113, 690978270233100398]  # Liste des buyers (à compléter)

    # Vérifie si l'utilisateur est autorisé
    if interaction.user.id not in wl_list and interaction.user.id not in buyer_list:
        embed = discord.Embed(
            title="⛔ Accès refusé",
            description="Tu n'as pas la permission d'utiliser cette commande.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Sauvegarde des informations du salon
    channel = interaction.channel
    channel_name = channel.name
    channel_category = channel.category
    channel_position = channel.position
    channel_permissions = channel.overwrites

    # Confirmation avant suppression
    embed = discord.Embed(
        title="🔄 Création en cours...",
        description=f"Le salon {channel.mention} est en train d'être recréé...",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)

    # Supprime et recrée le salon
    await channel.delete()
    new_channel = await channel_category.create_text_channel(
        name=channel_name,
        position=channel_position,
        overwrites=channel_permissions
    )

    # Envoie un message dans le nouveau salon
    await new_channel.send(f"✅ Salon recréé avec succès ! {interaction.user.mention} a utilisé `/renew`.")

@bot.tree.command(name="snipe", description="Affiche le dernier message supprimé.")
@app_commands.describe(salon="Le salon où snipes un message (facultatif).")
async def snipe(interaction: discord.Interaction, salon: discord.TextChannel = None):
    channel = salon or interaction.channel  # Utilise le salon donné ou le salon actuel

    if channel.id not in snipe_cache:
        embed = discord.Embed(
            title="🛑 Aucun message trouvé",
            description=f"Aucun message supprimé récemment dans {channel.mention}.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Récupère les infos du dernier message supprimé
    sniped_message = snipe_cache[channel.id]
    embed = discord.Embed(
        title="✉️ Dernier message supprimé",
        description=f"**{sniped_message['author'].name}** a dit :\n```{sniped_message['content']}```",
        color=discord.Color.orange(),
        timestamp=sniped_message["time"]
    )
    embed.set_footer(text=f"Supprimé dans #{channel.name}")
    embed.set_author(name=sniped_message["author"], icon_url=sniped_message["author"].avatar.url)

    # Vérifie s'il y a des images et les affiche
    if sniped_message.get("attachments"):  # Vérifie si la clé "attachments" existe et contient des images
        embed.set_image(url=sniped_message["attachments"][0])  # Affiche la première image

    await interaction.response.send_message(embed=embed, ephemeral=False)

class HelpView(View):
    def __init__(self):
        super().__init__(timeout=None)  # Pas de timeout

        self.add_item(HelpSelect())

class HelpSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="👤 Utilisateurs", description="Commandes accessibles à tous.", emoji="👤"),
            discord.SelectOption(label="🛠️ Modération", description="Commandes de modération.", emoji="🛠️"),
            discord.SelectOption(label="⚙️ Configuration", description="Commandes pour configurer le bot.", emoji="⚙️"),
            discord.SelectOption(label="🔄 Divers", description="Commandes diverses et utiles.", emoji="🔄"),
        ]
        super().__init__(placeholder="Choisissez une catégorie", options=options)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]  # Récupère la catégorie sélectionnée

        # Définition des embeds selon la catégorie choisie
        if category == "👤 Utilisateurs":
            embed = discord.Embed(
                title="👤 Commandes Utilisateurs",
                description="Voici les commandes accessibles à tout le monde :",
                color=discord.Color.blue()
            )
            embed.add_field(name="/userinfo [@membre]", value="Affiche les infos d’un utilisateur.", inline=False)
            embed.add_field(name="/infoserveur", value="Affiche les infos du serveur.", inline=False)
            embed.add_field(name="/avatar [@membre]", value="Affiche la photo de profil d’un membre.", inline=False)
            embed.add_field(name="/baniere [@membre]", value="Affiche la bannière d’un membre.", inline=False)
            embed.add_field(name="/blague", value="Affiche une blague au hasard.", inline=False)

        elif category == "🛠️ Modération":
            embed = discord.Embed(
                title="🛠️ Commandes de Modération",
                description="Commandes accessibles uniquement aux **wl** et **buyer**.",
                color=discord.Color.red()
            )
            embed.add_field(name="/warn [@membre] [raison]", value="Ajoute un avertissement.", inline=False)
            embed.add_field(name="/unwarn [@membre] [index]", value="Supprime un avertissement.", inline=False)
            embed.add_field(name="/warnlist [@membre]", value="Affiche les avertissements d’un membre.", inline=False)
            embed.add_field(name="/kick [@membre] [raison]", value="Expulse un membre.", inline=False)
            embed.add_field(name="/ban [@membre] [raison]", value="Bannit un membre.", inline=False)
            embed.add_field(name="/tempmute [@membre] [durée] [raison]", value="Mute temporairement un membre.", inline=False)
            embed.add_field(name="/unmute [@membre]", value="Démute un membre.", inline=False)
            embed.add_field(name="/clear [nombre]", value="Supprime des messages.", inline=False)
            embed.add_field(name="/snipe [salon (optionnel)]", value="Affiche le dernier message supprimé.", inline=False)

        elif category == "⚙️ Configuration":
            embed = discord.Embed(
                title="⚙️ Commandes de Configuration",
                description="Commandes permettant de configurer le bot.",
                color=discord.Color.green()
            )
            embed.add_field(name="/wl [@membre]", value="Ajoute un membre à la whitelist.", inline=False)
            embed.add_field(name="/unwl [@membre]", value="Retire un membre de la whitelist.", inline=False)
            embed.add_field(name="/wlist", value="Affiche la liste des whitelisted.", inline=False)
            embed.add_field(name="/buyerlist", value="Affiche la liste des buyers.", inline=False)
            embed.add_field(name="/joiner", value="Configure le système de bienvenue.", inline=False)
            embed.add_field(name="/variable", value="Affiche les variables utilisables dans le message de bienvenue.", inline=False)
            embed.add_field(name="/embed", value="Crée un embed avec des options configurables.", inline=False)

        elif category == "🔄 Divers":
            embed = discord.Embed(
                title="🔄 Commandes Diverses",
                description="Commandes utiles et amusantes.",
                color=discord.Color.purple()
            )
            embed.add_field(name="/say [message] [salon (optionnel)]", value="Envoie un message en tant que bot.", inline=False)
            embed.add_field(name="/renew", value="Recrée un salon.", inline=False)
            embed.add_field(name="/giveaway [prix] [temps] [condition (optionnel)] [salon (optionnel)]", value="Créer un giveaway", inline=False)
            embed.add_field(name="/reroll [index]", value="Reroll un giveaway", inline=False)

        else:
            embed = discord.Embed(title="❌ Erreur", description="Catégorie inconnue.", color=discord.Color.red())

        # Met à jour le message avec le nouvel embed
        await interaction.response.edit_message(embed=embed)

@bot.tree.command(name="help", description="Affiche la liste des commandes disponibles.")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📜 Menu d'aide",
        description="Choisissez une **catégorie** ci-dessous pour voir les commandes correspondantes.\n\n🔢 Nombre de commande : `26`",
        color=discord.Color.gold()
    )
    view = HelpView()

    await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

def load_whitelist():
    try:
        with open("whitelist.json", "r") as f:
            data = json.load(f)
        return data.get("wl_list", []), data.get("buyer_list", [1305151957547221113, 690978270233100398])
    except FileNotFoundError:
        return [], []  # Retourne des listes vides si le fichier n'existe pas

def can_use_giveaway(user_id):
    wl_list, buyer_list = load_whitelist()  # Charge la whitelist depuis le fichier
    return user_id in wl_list or user_id in buyer_list
    
def parse_time(time_str):
    units = {"s": "seconds", "m": "minutes", "h": "hours", "d": "days"}
    unit = time_str[-1]
    if unit not in units:
        return None
    try:
        return timedelta(**{units[unit]: int(time_str[:-1])})
    except ValueError:
        return None

@bot.tree.command(name="giveaway", description="Créer un giveaway")
@app_commands.describe(prix="Récompense du giveaway", temps="Durée (ex: 5h, 9d)", conditions="Conditions (facultatif)", salon="Salon où envoyer (facultatif)")
async def giveaway(interaction: discord.Interaction, prix: str, temps: str, conditions: str = "Aucune", salon: discord.TextChannel = None):
    if not can_use_giveaway(interaction.user.id):
        await interaction.response.send_message("❌ Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)
        return

    duration = parse_time(temps)
    if not duration:
        await interaction.response.send_message("❌ Format de temps invalide ! Utilisez `5h`, `9d`, etc.", ephemeral=True)
        return

    target_channel = salon or interaction.channel
    index = len(giveaways) + 1  # Génère un index unique

    embed = discord.Embed(title="🎉 Giveaway !", description=f"**Récompense** : {prix}\n**Conditions** : {conditions}\n\nRéagissez 🎁 pour participer !", color=discord.Color.gold())
    embed.set_footer(text=f"Giveaway #{index} • Se termine dans {temps}")

    message = await target_channel.send(embed=embed)
    await message.add_reaction("🎁")

    giveaways[index] = {"message_id": message.id, "channel_id": target_channel.id, "prize": prix, "author": interaction.user.mention}

    await interaction.response.send_message(f"✅ Giveaway lancé dans {target_channel.mention} !", ephemeral=True)

    await asyncio.sleep(duration.total_seconds())  # Attend la durée du giveaway

    message = await target_channel.fetch_message(message.id)
    users = [user async for user in message.reactions[0].users() if not user.bot]

    if users:
        winner = random.choice(users)
        await target_channel.send(f"🎉 Félicitations {winner.mention} ! Tu gagnes **{prix}** ! 🎊")
    else:
        await target_channel.send("❌ Personne n'a participé au giveaway.")

@bot.tree.command(name="reroll", description="Relance un tirage sur un giveaway")
@app_commands.describe(index="Numéro du giveaway à reroll")
async def reroll(interaction: discord.Interaction, index: int):
    if not can_use_giveaway(interaction.user.id):
        await interaction.response.send_message("❌ Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True)
        return

    if index not in giveaways:
        await interaction.response.send_message("❌ Giveaway introuvable.", ephemeral=True)
        return

    data = giveaways[index]
    channel = bot.get_channel(data["channel_id"])
    message = await channel.fetch_message(data["message_id"])

    users = [user async for user in message.reactions[0].users() if not user.bot]

    if users:
        winner = random.choice(users)
        await channel.send(f"🔄 Nouveau gagnant pour **{data['prize']}** : {winner.mention} ! 🎊")
    else:
        await channel.send("❌ Toujours aucun participant pour ce giveaway.")

    await interaction.response.send_message("✅ Giveaway reroll avec succès.", ephemeral=True)
# Lancement du bot
TOKEN = "TON TOKEN"
bot.run(TOKEN)