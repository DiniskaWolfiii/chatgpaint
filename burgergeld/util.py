import discord
from discord.ext import commands
import aiosqlite

class BurgerUtil(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bg_path = "./../data/burgergeld.db"
        self.inv_path = "./../data/bg_inventory.db"
        self.menu_path = "./../data/bg_menu.json"

    @discord.slash_command(name="burgergeld", description="Zeigt dir dein aktuelles Burgergeld an.")
    async def burgergeld(self, ctx, user: discord.Member = None):
        await ctx.defer()
        if user is None:
            async with aiosqlite.connect(self.bg_path) as db:
                async with db.execute(f"SELECT burgergeld FROM guild_{ctx.guild.id} WHERE user_id = ?", (ctx.author.id,)) as cursor:
                    result = await cursor.fetchone()
                    if result is None:
                        await ctx.respond("Du hast noch kein Burgergeld!")
                    else:
                        await ctx.respond(f"Du hast {result[0]} Burgergeld!")
        else:
            async with aiosqlite.connect(self.bg_path) as db:
                async with db.execute(f"SELECT burgergeld FROM guild_{ctx.guild.id} WHERE user_id = ?", (user.id,)) as cursor:
                    result = await cursor.fetchone()
                    if result is None:
                        await ctx.respond(f"{user.mention} hat noch kein Burgergeld!")
                    else:
                        await ctx.respond(f"{user.mention} hat {result[0]} Burgergeld!")
    
    @discord.slash_command(name="addbg", description="Gibt einem User Burgergeld.")
    @commands.has_permissions(administrator=True)
    async def addbg(self, ctx, user: discord.Member, amount: int):
        await ctx.defer(ephemeral=True)
        async with aiosqlite.connect(self.bg_path) as db:
            await db.execute(f"INSERT OR IGNORE INTO guild_{ctx.guild.id} (user_id, burgergeld) VALUES (?, ?)", (user.id, 0))
            await db.execute(f"UPDATE guild_{ctx.guild.id} SET burgergeld = burgergeld + ? WHERE user_id = ?", (amount, user.id))
            await db.commit()
        await ctx.respond(f"{amount} Burgergeld wurden {user.mention} hinzugefügt!")

    @discord.slash_command(name="removebg", description="Nimmt einem User Burgergeld.")
    @commands.has_permissions(administrator=True)
    async def removebg(self, ctx, user: discord.Member, amount: int):
        await ctx.defer(ephemeral=True)
        async with aiosqlite.connect(self.bg_path) as db:
            await db.execute(f"INSERT OR IGNORE INTO guild_{ctx.guild.id} (user_id, burgergeld) VALUES (?, ?)", (user.id, 0))
            await db.execute(f"UPDATE guild_{ctx.guild.id} SET burgergeld = burgergeld - ? WHERE user_id = ?", (amount, user.id))
            await db.commit()
        await ctx.respond(f"{amount} Burgergeld wurden {user.mention} entfernt!")

    @discord.Cog.listener()
    async def on_ready(self):
        await setup_db(self)
    
async def setup_db(self):
    async with aiosqlite.connect(self.bg_path) as db:
        for guild in self.bot.guilds:
            await db.execute(f"CREATE TABLE IF NOT EXISTS guild_{guild.id} (user_id INTEGER PRIMARY KEY, burgergeld INTEGER)")
        await db.commit()
    async with aiosqlite.connect(self.inv_path) as db:
        for guild in self.bot.guilds:
            await db.execute(f"CREATE TABLE IF NOT EXISTS guild_{guild.id} (user_id INTEGER, menu_id INTEGER, amount INTEGER)")
        await db.commit()

def setup(bot):
    bot.add_cog(BurgerUtil(bot))
