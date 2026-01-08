"""
AquaFrost Discord Bot
"""
import os
import sys
import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
import aiohttp
import json
import random

# ============================================
# BOT CONFIGURATION
# ============================================

class Config:
    PREFIX = "!"
    TOKEN = os.environ.get("DISCORD_TOKEN", "")
    DEFAULT_COLOR = 0x00FFFF
    WEBHOOK_COLOR = 0x00FFF0  # New webhook color
    
    # Logging channel
    LOG_SERVER_ID = 1445061695520116860
    LOG_CHANNEL_ID = 1454112006180442193
    
    # URLs
    PROJECTS_URL = "https://org.aquafrost.ct.ws/discord/projects.txt"
    MODDL_URL = "https://org.aquafrost.ct.ws/discord/moddl.txt"
    
    # 8-ball responses
    EIGHTBALL_RESPONSES = [
        "As I see it, yes",
        "Yes",
        "No", 
        "Very likely",
        "Not even close",
        "Maybe",
        "Very unlikely",
        "Gino's mom told me yes",
        "Gino's mom told me no",
        "Ask again later",
        "Better not tell you now",
        "Concentrate and ask again",
        "Don't count on it",
        "It is certain",
        "My sources say no",
        "Outlook good",
        "You may rely on it",
        "Very Doubtful",
        "Without a doubt"
    ]
    
    if not TOKEN:
        try:
            from dotenv import load_dotenv
            load_dotenv()
            TOKEN = os.getenv("DISCORD_TOKEN", "")
        except:
            pass

# ============================================
# STATUS ROTATION SYSTEM
# ============================================

class StatusManager:
    def __init__(self):
        self.statuses = ["Aqua Client", "Apple Client", "Jet Client", "Loup Client", "Unifix Client"]
        self.status_modes = [discord.Status.online, discord.Status.idle, discord.Status.dnd]
        self.current_status_index = 0
        self.current_mode_index = 0
    
    def get_next_status(self):
        status = self.statuses[self.current_status_index]
        self.current_status_index = (self.current_status_index + 1) % len(self.statuses)
        return discord.Game(name=status)
    
    def get_next_mode(self):
        mode = self.status_modes[self.current_mode_index]
        self.current_mode_index = (self.current_mode_index + 1) % len(self.status_modes)
        return mode

# ============================================
# MAIN BOT CLASS
# ============================================

class AquaFrost(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix=commands.when_mentioned_or(Config.PREFIX),
            intents=intents,
            help_command=None
        )
        
        self.start_time = datetime.utcnow()
        self.status_manager = StatusManager()
        self.log_channel = None
    
    async def setup_hook(self):
        print("=" * 50)
        print("🚀 AquaFrost Bot Starting...")
        print("=" * 50)
        await self.load_commands()
        try:
            synced = await self.tree.sync()
            print(f"✅ Synced {len(synced)} commands")
        except Exception as e:
            print(f"⚠️ Command sync: {e}")
    
    @tasks.loop(seconds=5)
    async def rotate_playing_status(self):
        if self.is_ready():
            activity = self.status_manager.get_next_status()
            current_mode = self.status_manager.status_modes[self.status_manager.current_mode_index]
            await self.change_presence(activity=activity, status=current_mode)
    
    @tasks.loop(seconds=10)
    async def rotate_status_mode(self):
        if self.is_ready():
            new_mode = self.status_manager.get_next_mode()
            activity = discord.Game(name=self.status_manager.statuses[self.status_manager.current_status_index])
            await self.change_presence(activity=activity, status=new_mode)
    
    async def log_command(self, interaction: discord.Interaction, command_name: str, args: dict = None):
        """Log command usage to the logging channel"""
        try:
            if not self.log_channel:
                # Get the logging channel
                log_server = self.get_guild(Config.LOG_SERVER_ID)
                if log_server:
                    self.log_channel = log_server.get_channel(Config.LOG_CHANNEL_ID)
            
            if self.log_channel:
                embed = discord.Embed(
                    title="📝 Command Executed",
                    color=0x3498db,
                    timestamp=datetime.utcnow()
                )
                
                embed.add_field(name="👤 User", value=f"{interaction.user.mention}\nID: {interaction.user.id}", inline=True)
                embed.add_field(name="🏷️ Command", value=f"`/{command_name}`", inline=True)
                
                if interaction.guild:
                    embed.add_field(name="🛡️ Server", value=f"{interaction.guild.name}\nID: {interaction.guild.id}", inline=True)
                
                if args:
                    args_str = "\n".join([f"`{k}`: {v}" for k, v in args.items()])
                    embed.add_field(name="📊 Arguments", value=args_str[:500], inline=False)
                
                embed.add_field(name="🕐 Time", value=f"<t:{int(datetime.utcnow().timestamp())}:F>", inline=True)
                
                await self.log_channel.send(embed=embed)
                
        except Exception as e:
            print(f"⚠️ Failed to log command: {e}")
    
    async def fetch_text_content(self, url: str) -> str:
        """Fetch text content from a URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        return None
        except:
            return None
    
    async def load_commands(self):
        """Load all bot commands"""
        
        # ========== PROJECTS COMMAND ==========
        
        @self.tree.command(name="projects", description="AquaFrost's Projects and project links")
        async def projects(interaction: discord.Interaction):
            """Show AquaFrost projects"""
            await interaction.response.defer()
            
            # Log the command
            await self.log_command(interaction, "projects")
            
            try:
                # Fetch projects text
                projects_content = await self.fetch_text_content(Config.PROJECTS_URL)
                
                if projects_content:
                    # Send the raw text directly
                    await interaction.followup.send(content=projects_content)
                else:
                    embed = discord.Embed(
                        title="❌ Could Not Fetch Projects",
                        description=f"Failed to fetch from:\n`{Config.PROJECTS_URL}`",
                        color=0xFF0000
                    )
                    await interaction.followup.send(embed=embed)
                    
            except Exception as e:
                embed = discord.Embed(
                    title="❌ Error",
                    description=f"```{str(e)[:200]}```",
                    color=0xFF0000
                )
                await interaction.followup.send(embed=embed)
        
        # ========== MOD DOWNLOAD COMMAND ==========
        
        @self.tree.command(name="moddl", description="Minecraft Mod Download Link")
        async def moddl(interaction: discord.Interaction):
            """Send the raw text file content"""
            await interaction.response.defer()
            
            # Log the command
            await self.log_command(interaction, "moddl")
            
            try:
                # Fetch moddl text
                moddl_content = await self.fetch_text_content(Config.MODDL_URL)
                
                if moddl_content:
                    # Send the raw text directly
                    await interaction.followup.send(content=moddl_content)
                else:
                    embed = discord.Embed(
                        title="❌ Download Failed",
                        description=f"Failed to fetch from:\n`{Config.MODDL_URL}`",
                        color=0xFF0000
                    )
                    await interaction.followup.send(embed=embed)
                    
            except Exception as e:
                embed = discord.Embed(
                    title="❌ Error",
                    description=f"```{str(e)[:200]}```",
                    color=0xFF0000
                )
                await interaction.followup.send(embed=embed)
        
        # ========== AVATAR COMMAND ==========
        
        @self.tree.command(name="avatar", description="Get a user's avatar")
        @app_commands.describe(user="User to get avatar from (defaults to yourself)")
        async def avatar(interaction: discord.Interaction, user: discord.User = None):
            """Get user avatar"""
            # Default to command user if no user specified
            target_user = user or interaction.user
            
            # Log the command
            args = {"user": f"{target_user.name} ({target_user.id})"} if user else {}
            await self.log_command(interaction, "avatar", args)
            
            # Get all avatar sizes
            avatar_url = target_user.display_avatar.url
            
            # Create embed with avatar
            embed = discord.Embed(
                title=f"👤 {target_user.name}'s Avatar",
                color=Config.DEFAULT_COLOR,
                timestamp=datetime.utcnow()
            )
            
            # Set the avatar as the main image
            embed.set_image(url=avatar_url)
            
            # Add download links for different sizes
            embed.add_field(
                name="📥 Download Links",
                value=f"[256px]({avatar_url.replace('?size=1024', '?size=256')}) | "
                      f"[512px]({avatar_url.replace('?size=1024', '?size=512')}) | "
                      f"[1024px]({avatar_url}) | "
                      f"[2048px]({avatar_url.replace('?size=1024', '?size=2048')})",
                inline=False
            )
            
            # Add user info
            embed.add_field(
                name="👤 User Info",
                value=f"**Name:** {target_user.mention}\n"
                      f"**ID:** `{target_user.id}`\n"
                      f"**Account Created:** <t:{int(target_user.created_at.timestamp())}:R>",
                inline=True
            )
            
            # Add server join date if applicable
            if interaction.guild and target_user in interaction.guild.members:
                member = interaction.guild.get_member(target_user.id)
                if member and member.joined_at:
                    embed.add_field(
                        name="🛡️ Server Info",
                        value=f"**Joined:** <t:{int(member.joined_at.timestamp())}:R>\n"
                              f"**Roles:** {len(member.roles) - 1}",
                        inline=True
                    )
            
            embed.set_footer(text=f"Requested by {interaction.user.name}")
            
            await interaction.response.send_message(embed=embed)
        
        # ========== 8BALL COMMAND ==========
        
        @self.tree.command(name="8ball", description="Ask the magic 8-ball a question")
        @app_commands.describe(question="Your question for the magic 8-ball")
        async def eightball(interaction: discord.Interaction, question: str):
            """Magic 8-ball command"""
            # Log the command
            await self.log_command(interaction, "8ball", {"question": question[:100]})
            
            # Get random response
            response = random.choice(Config.EIGHTBALL_RESPONSES)
            
            # Determine color based on response type
            positive_responses = ["yes", "certain", "good", "rely", "doubt", "likely"]
            negative_responses = ["no", "not", "doubtful", "unlikely"]
            
            response_lower = response.lower()
            color = 0x00FF00  # Default green
            
            if any(word in response_lower for word in negative_responses):
                color = 0xFF0000  # Red for negative
            elif any(word in response_lower for word in positive_responses):
                color = 0x00FF00  # Green for positive
            else:
                color = 0xFFFF00  # Yellow for neutral
            
            # Create embed
            embed = discord.Embed(
                title="🎱 The Magic 8-Ball",
                color=color,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(name="❓ Your Question", value=f"```{question}```", inline=False)
            embed.add_field(name="🎯 Answer", value=f"**{response}**", inline=False)
            
            # Add fun emoji based on response
            if "yes" in response_lower or "certain" in response_lower:
                emoji = "✅"
            elif "no" in response_lower or "not" in response_lower:
                emoji = "❌"
            elif "maybe" in response_lower or "later" in response_lower:
                emoji = "🤔"
            else:
                emoji = "🎱"
            
            embed.set_footer(text=f"{emoji} Asked by {interaction.user.name}")
            
            await interaction.response.send_message(embed=embed)
        
        # ========== NEW: UPTIME COMMAND ==========
        
        @self.tree.command(name="uptime", description="Check how long the bot has been online")
        async def uptime(interaction: discord.Interaction):
            """Show bot uptime"""
            # Log the command
            await self.log_command(interaction, "uptime")
            
            uptime = datetime.utcnow() - self.start_time
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            # Format uptime string
            if days > 0:
                uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
            elif hours > 0:
                uptime_str = f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                uptime_str = f"{minutes}m {seconds}s"
            else:
                uptime_str = f"{seconds}s"
            
            # Create embed
            embed = discord.Embed(
                title="⏱️ Bot Uptime",
                color=Config.DEFAULT_COLOR,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="📅 Start Time",
                value=f"<t:{int(self.start_time.timestamp())}:F>\n(<t:{int(self.start_time.timestamp())}:R>)",
                inline=True
            )
            
            embed.add_field(
                name="⏳ Current Uptime",
                value=f"**{uptime_str}**",
                inline=True
            )
            
            embed.add_field(
                name="🔄 Status",
                value=f"Playing: Every 5s\nMode: Every 10s",
                inline=False
            )
            
            # Add current activity
            current_client = self.status_manager.statuses[self.status_manager.current_status_index]
            current_mode = self.status_manager.status_modes[self.status_manager.current_mode_index]
            
            mode_emoji = {
                discord.Status.online: "🟢",
                discord.Status.idle: "🌙",
                discord.Status.dnd: "⛔"
            }
            
            embed.add_field(
                name="🎮 Current Activity",
                value=f"{mode_emoji.get(current_mode, '⚪')} Playing **{current_client}**",
                inline=True
            )
            
            embed.set_footer(text=f"Bot started by {self.user.name}")
            
            await interaction.response.send_message(embed=embed)
        
        # ========== NEW: REFRESH COMMAND (ADMIN ONLY) ==========
        
        @app_commands.checks.has_permissions(administrator=True)
        @self.tree.command(name="refresh", description="[ADMIN] Refresh bot commands")
        async def refresh(interaction: discord.Interaction):
            """Refresh bot commands (Admin only)"""
            await interaction.response.defer(ephemeral=True)
            
            # Log the command
            await self.log_command(interaction, "refresh")
            
            try:
                # Reload commands
                await self.load_commands()
                
                # Sync tree
                synced = await self.tree.sync()
                
                embed = discord.Embed(
                    title="🔄 Commands Refreshed",
                    description=f"✅ Successfully synced **{len(synced)}** commands",
                    color=0x00FF00
                )
                
                # List all commands
                command_list = []
                for cmd in self.tree.get_commands():
                    command_list.append(f"• `/{cmd.name}` - {cmd.description}")
                
                if command_list:
                    embed.add_field(
                        name="📋 Available Commands",
                        value="\n".join(command_list[:15]),
                        inline=False
                    )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
                # Also send to log channel
                if self.log_channel:
                    log_embed = discord.Embed(
                        title="🔄 Commands Refreshed by Admin",
                        description=f"**Admin:** {interaction.user.mention}\n**Commands:** {len(synced)} synced",
                        color=0x3498db,
                        timestamp=datetime.utcnow()
                    )
                    await self.log_channel.send(embed=log_embed)
                    
            except Exception as e:
                error_embed = discord.Embed(
                    title="❌ Refresh Failed",
                    description=f"```{str(e)[:200]}```",
                    color=0xFF0000
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
        
        # ========== NEW: SAY COMMAND (ADMIN ONLY) ==========
        
        @app_commands.checks.has_permissions(administrator=True)
        @self.tree.command(name="say", description="[ADMIN] Make the bot say something")
        @app_commands.describe(
            message="Message to send",
            channel="Channel to send to (defaults to current)"
        )
        async def say(interaction: discord.Interaction, message: str, channel: discord.TextChannel = None):
            """Make the bot say something (Admin only)"""
            await interaction.response.defer(ephemeral=True)
            
            # Log the command
            args = {
                "message": message[:100] + "..." if len(message) > 100 else message,
                "channel": channel.mention if channel else "Current"
            }
            await self.log_command(interaction, "say", args)
            
            try:
                # Determine target channel
                target_channel = channel or interaction.channel
                
                # Check if bot has permission to send messages
                if not target_channel.permissions_for(interaction.guild.me).send_messages:
                    embed = discord.Embed(
                        title="❌ Permission Error",
                        description=f"I don't have permission to send messages in {target_channel.mention}",
                        color=0xFF0000
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
                
                # Send the message
                await target_channel.send(message)
                
                # Send confirmation to admin
                embed = discord.Embed(
                    title="✅ Message Sent",
                    description=f"Message sent to {target_channel.mention}",
                    color=0x00FF00
                )
                embed.add_field(name="📝 Message", value=f"```{message[:500]}```", inline=False)
                await interaction.followup.send(embed=embed, ephemeral=True)
                
            except Exception as e:
                error_embed = discord.Embed(
                    title="❌ Failed to Send Message",
                    description=f"```{str(e)[:200]}```",
                    color=0xFF0000
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
        
        # ========== NEW: WEBHOOK SAY COMMAND (ADMIN ONLY) ==========
        
        @app_commands.checks.has_permissions(administrator=True)
        @self.tree.command(name="webhook-say", description="[ADMIN] Send a message via webhook (cool style)")
        @app_commands.describe(
            message="Message to send",
            username="Webhook username (defaults to bot name)",
            channel="Channel to send to"
        )
        async def webhook_say(interaction: discord.Interaction, message: str, 
                            username: str = None, channel: discord.TextChannel = None):
            """Send message via webhook (Admin only)"""
            await interaction.response.defer(ephemeral=True)
            
            # Log the command
            args = {
                "message": message[:100] + "..." if len(message) > 100 else message,
                "username": username or "Default",
                "channel": channel.mention if channel else "Current"
            }
            await self.log_command(interaction, "webhook-say", args)
            
            try:
                # Determine target channel
                target_channel = channel or interaction.channel
                
                # Check if bot has permission to manage webhooks
                if not target_channel.permissions_for(interaction.guild.me).manage_webhooks:
                    embed = discord.Embed(
                        title="❌ Permission Error",
                        description=f"I need **Manage Webhooks** permission in {target_channel.mention}",
                        color=0xFF0000
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
                
                # Get or create webhook
                webhooks = await target_channel.webhooks()
                webhook = None
                
                # Look for existing bot webhook
                for wh in webhooks:
                    if wh.user and wh.user.id == self.user.id:
                        webhook = wh
                        break
                
                # Create new webhook if none exists
                if not webhook:
                    webhook = await target_channel.create_webhook(
                        name="AquaFrost Bot",
                        reason="Created for webhook-say command"
                    )
                
                # Set default username if not provided
                webhook_username = username or self.user.name
                
                # Send message via webhook
                await webhook.send(
                    content=message,
                    username=webhook_username,
                    avatar_url=self.user.display_avatar.url,
                    wait=True
                )
                
                # Create confirmation embed with webhook color
                embed = discord.Embed(
                    title="✅ Webhook Message Sent",
                    description=f"Message sent via webhook to {target_channel.mention}",
                    color=Config.WEBHOOK_COLOR  # Using the specified color
                )
                
                embed.add_field(name="👤 Webhook Name", value=f"`{webhook_username}`", inline=True)
                embed.add_field(name="🔗 Webhook URL", value=f"`{webhook.url[:50]}...`", inline=True)
                embed.add_field(name="📝 Message", value=f"```{message[:300]}```", inline=False)
                
                # Add webhook info
                embed.add_field(
                    name="🔄 Webhook Info",
                    value=f"**ID:** `{webhook.id}`\n**Channel:** {webhook.channel.mention}\n**Created:** <t:{int(webhook.created_at.timestamp())}:R>",
                    inline=True
                )
                
                embed.set_footer(text="Sent via webhook")
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
            except Exception as e:
                error_embed = discord.Embed(
                    title="❌ Webhook Failed",
                    description=f"```{str(e)[:200]}```",
                    color=0xFF0000
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
        
        # ========== UTILITY COMMANDS ==========
        
        @self.tree.command(name="ping", description="Check bot latency")
        async def ping(interaction: discord.Interaction):
            """Check bot ping"""
            # Log the command
            await self.log_command(interaction, "ping")
            
            latency = round(self.latency * 1000)
            embed = discord.Embed(
                title="🏓 Pong!",
                description=f"**Latency:** {latency}ms",
                color=Config.DEFAULT_COLOR
            )
            
            # Add uptime
            uptime = datetime.utcnow() - self.start_time
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            if days > 0:
                uptime_str = f"{days}d {hours}h {minutes}m"
            else:
                uptime_str = f"{hours}h {minutes}m {seconds}s"
            
            embed.add_field(name="⏱️ Uptime", value=uptime_str, inline=True)
            embed.add_field(name="📊 Servers", value=len(self.guilds), inline=True)
            
            # Add current status
            current_client = self.status_manager.statuses[self.status_manager.current_status_index]
            embed.add_field(name="🎮 Status", value=f"Playing {current_client}", inline=True)
            
            await interaction.response.send_message(embed=embed)
        
        @self.tree.command(name="help", description="Show all commands")
        async def help_cmd(interaction: discord.Interaction):
            """Show help menu"""
            # Log the command
            await self.log_command(interaction, "help")
            
            embed = discord.Embed(
                title="🛠️ AquaFrost Help Menu",
                description="Minecraft Client Download Bot",
                color=Config.DEFAULT_COLOR
            )
            
            commands_list = """
            **`/ping`**
            Check bot latency and status
            
            **`/uptime`**
            Check how long the bot has been online
            
            **`/projects`**
            Show AquaFrost's projects and links
            
            **`/moddl`**
            Get Minecraft client download links
            
            **`/avatar [@user]`**
            Get a user's avatar with download links
            
            **`/8ball [question]`**
            Ask the magic 8-ball a question
            
            **`/help`**
            Show this menu
            """
            
            embed.add_field(name="🔧 Public Commands", value=commands_list, inline=False)
            
            # Admin commands section
            admin_commands = """
            **`/refresh`** ⚠️
            Refresh bot commands (Admin only)
            
            **`/say [message] [channel]`** ⚠️
            Make bot send a message (Admin only)
            
            **`/webhook-say [message] [username] [channel]`** ⚠️
            Send message via webhook (Admin only)
            """
            
            embed.add_field(name="🛡️ Admin Commands", value=admin_commands, inline=False)
            
            # Available clients
            clients_list = """
            **Available Clients:**
            • Aqua Client
            • Apple Client
            • Jet Client
            • Loup Client
            • Unifix Client
            """
            
            embed.add_field(name="🎮 Clients", value=clients_list, inline=True)
            
            # Status info
            status_info = """
            **Status Rotation:**
            • Playing: Every 5s
            • Online/Idle/DND: Every 10s
            """
            
            embed.add_field(name="🔄 Bot Status", value=status_info, inline=True)
            
            embed.set_footer(text="Bot by AquaFrost Team | Admin commands marked with ⚠️")
            await interaction.response.send_message(embed=embed)
    
    async def on_ready(self):
        """Called when bot is ready"""
        print(f"\n✅ Logged in as: {self.user}")
        print(f"🆔 Bot ID: {self.user.id}")
        print(f"📊 Servers: {len(self.guilds)}")
        print(f"👥 Users: {len(self.users)}")
        
        print(f"\n🔄 Status Rotation Active")
        print(f"• Playing: Every 5 seconds")
        print(f"• Mode: Every 10 seconds")
        
        # Try to get logging channel
        try:
            log_server = self.get_guild(Config.LOG_SERVER_ID)
            if log_server:
                self.log_channel = log_server.get_channel(Config.LOG_CHANNEL_ID)
                if self.log_channel:
                    print(f"📝 Logging Channel: #{self.log_channel.name} (ID: {self.log_channel.id})")
                    
                    # Send startup log
                    startup_embed = discord.Embed(
                        title="🚀 Bot Started",
                        description=f"**Bot:** {self.user.name}\n**ID:** {self.user.id}",
                        color=0x00FF00,
                        timestamp=datetime.utcnow()
                    )
                    startup_embed.add_field(name="Servers", value=len(self.guilds), inline=True)
                    startup_embed.add_field(name="Users", value=len(self.users), inline=True)
                    startup_embed.add_field(name="Commands", value="9 commands loaded", inline=True)
                    startup_embed.set_footer(text="Command logging active")
                    
                    await self.log_channel.send(embed=startup_embed)
                else:
                    print(f"⚠️ Log channel not found: {Config.LOG_CHANNEL_ID}")
            else:
                print(f"⚠️ Log server not found: {Config.LOG_SERVER_ID}")
        except Exception as e:
            print(f"⚠️ Failed to setup logging: {e}")
        
        print("\n" + "=" * 50 + "\n")
        
        # Start rotation tasks
        self.rotate_playing_status.start()
        self.rotate_status_mode.start()

# ============================================
# START THE BOT
# ============================================

if __name__ == "__main__":
    if not Config.TOKEN:
        print("❌ ERROR: No Discord token found!")
        print("Set environment variable: DISCORD_TOKEN=your_token")
        sys.exit(1)
    
    bot = AquaFrost()
    
    try:
        bot.run(Config.TOKEN)
    except discord.LoginFailure:
        print("❌ Invalid token!")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
