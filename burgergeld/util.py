import discord
from discord.ext import commands
import aiosqlite
import json
import asyncio

class BurgerUtil(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bg_path = "./../data/burgergeld.db"
        self.inv_path = "./../data/bg_inventory.db"
        self.menu_path = "./../data/bg_menu.json"

    bg_command = discord.SlashCommandGroup(name="bg", description="Commands for Burgergeld.")
    @bg_command.command(name="show", description="Shows your current Burgergeld.")
    async def burgergeld(self, ctx, user: discord.Member = None):
        await ctx.defer()
        if user is None:
            async with aiosqlite.connect(self.bg_path) as db:
                async with db.execute(f"SELECT burgergeld FROM guild_{ctx.guild.id} WHERE user_id = ?", (ctx.author.id,)) as cursor:
                    result = await cursor.fetchone()
                    if result is None:
                        await ctx.respond("You currently don't have Burgergeld!")
                    else:
                        await ctx.respond(f"You have {result[0]} Burgergeld!")
        else:
            async with aiosqlite.connect(self.bg_path) as db:
                async with db.execute(f"SELECT burgergeld FROM guild_{ctx.guild.id} WHERE user_id = ?", (user.id,)) as cursor:
                    result = await cursor.fetchone()
                    if result is None:
                        await ctx.respond(f"{user.mention} hat noch kein Burgergeld!")
                    else:
                        await ctx.respond(f"{user.mention} hat {result[0]} Burgergeld!")
    
    @bg_command.command(name="add", description="Gives a user Burgergeld.")
    @commands.has_permissions(administrator=True)
    async def addbg(self, ctx, user: discord.Member, amount: int):
        await ctx.defer(ephemeral=True)
        async with aiosqlite.connect(self.bg_path) as db:
            await db.execute(f"INSERT OR IGNORE INTO guild_{ctx.guild.id} (user_id, burgergeld) VALUES (?, ?)", (user.id, 0))
            await db.execute(f"UPDATE guild_{ctx.guild.id} SET burgergeld = burgergeld + ? WHERE user_id = ?", (amount, user.id))
            await db.commit()
        await ctx.respond(f"{amount} Burgergeld were added to {user.mention}!")

    @bg_command.command(name="remove", description="Removes Burgergeld from user.")
    @commands.has_permissions(administrator=True)
    async def removebg(self, ctx, user: discord.Member, amount: int):
        await ctx.defer(ephemeral=True)
        async with aiosqlite.connect(self.bg_path) as db:
            await db.execute(f"INSERT OR IGNORE INTO guild_{ctx.guild.id} (user_id, burgergeld) VALUES (?, ?)", (user.id, 0))
            await db.execute(f"UPDATE guild_{ctx.guild.id} SET burgergeld = burgergeld - ? WHERE user_id = ?", (amount, user.id))
            await db.commit()
        await ctx.respond(f"{amount} Burgergeld were removed from {user.mention}!")

    @bg_command.command(name="menu", description="Shows the current Burger-Menu.")
    async def menu(self, ctx):
        await ctx.defer()
        with open(self.menu_path, "r") as file:
            menu_data = json.load(file)
        
        burgers = menu_data.get("Burger", [])
        sides = menu_data.get("Sides", [])

        embed = discord.Embed(title="Burger-Menu", color=discord.Color.blurple())
        embed.add_field(name="Burger", value="\n".join([f"{burger['name']} - {burger['price']} BG" for burger in burgers]), inline=False)
        embed.add_field(name="Sides", value="\n".join([f"{side['name']} - {side['price']} BG" for side in sides]), inline=False)
        await ctx.respond(embed=embed)



    buy_command = discord.SlashCommandGroup(name="buy", description="Buy something from the menu.")
    @buy_command.command(name="burger", description="Buy a burger from the menu.")
    async def buy_burger(self, ctx):
        await ctx.defer()
        menu = None
        with open(self.menu_path, "r") as file:
            menu = json.load(file)
        burgers = menu.get("Burger", [])

        if len(burgers) == 0:
            await ctx.respond("There are currently no burgers in the menu!", ephemeral=True)
            return
        elif len(burgers) <= 25:
            class BurgerView(discord.ui.View):
                def __init__(self, inv_path, bg_path, menu_path):
                    super().__init__(timeout=60.0)     
                    self.inv_path = inv_path
                    self.bg_path = bg_path
                    self.menu_path = menu_path      
                async def interaction_check(self, interaction):
                    if interaction.user.id == ctx.author.id:
                        async with aiosqlite.connect(self.bg_path) as db:
                            async with db.execute(f"SELECT burgergeld FROM guild_{ctx.guild.id} WHERE user_id = ?", (ctx.author.id,)) as bg_cursor:
                                bg_result = await bg_cursor.fetchone()
                                if bg_result is None:
                                    await ctx.edit(content="You currently don't have Burgergeld!", view=None, embed=None)
                                    return False
                                price = None
                                with open(self.menu_path, "r") as file:
                                    menu_data = json.load(file)
                                    for burger in menu_data.get("Burger", []):
                                        if burger["id"] == int(interaction.custom_id):
                                            price = burger["price"]
                                    if price > bg_result[0]:
                                        await ctx.edit(content="You don't have enough Burgergeld to buy this burger!", view=None, embed=None)
                                        return False
                        async with aiosqlite.connect(self.inv_path) as db:
                            result = await db.execute_fetchall(f"SELECT * FROM guild_{ctx.guild.id} WHERE user_id = ? AND menu_id = ?", (ctx.author.id, interaction.custom_id))
                            if len(result) == 0:
                                await db.execute(f"INSERT INTO guild_{ctx.guild.id} (user_id, menu_id, amount) VALUES (?, ?, 1)", (ctx.author.id, interaction.custom_id))
                            else:
                                await db.execute(f"UPDATE guild_{ctx.guild.id} SET amount = amount + 1 WHERE user_id = ? AND menu_id = ?", (ctx.author.id, interaction.custom_id))
                            await db.commit()
                        async with aiosqlite.connect(self.bg_path) as db:
                            await db.execute(f"UPDATE guild_{ctx.guild.id} SET burgergeld = burgergeld - ? WHERE user_id = ?", (price, ctx.author.id))
                            await db.commit()
                        await ctx.edit(content="You bought a burger!", view=None, embed=None)
                        return True
                    else:
                        await interaction.response.send_message("You can't interact with this menu!", ephemeral=True)
                        self.stop()
                        return False
                async def on_timeout(self):
                    self.clear_items()
                    self.stop()
                    await ctx.edit(content="The menu timed out! Please re-run the Buy Command!", view=None, embed=None)
            view = BurgerView(self.inv_path, self.bg_path, self.menu_path)
            row = 0
            i = 0
            for burger in burgers:
                if i % 5 == 0 and i != 0:
                    row += 1
                view.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, label=burger["name"], row=row, custom_id=str(burger["id"])))
                i += 1
            embed = discord.Embed(title="Burger-Menu", color=discord.Color.blurple())
            embed.add_field(name="Burger", value="\n".join([f"{burger['name']} - {burger['price']} BG" for burger in burgers]), inline=False)
            await ctx.respond(embed=embed, view=view)            
                    
        elif len(burgers) > 25:
            await ctx.respond("There are too many burgers in the menu to display them all at once! Please get back to Wolfiii!", ephemeral=True)
            return
        
    @buy_command.command(name="side", description="Buy a side from the menu.")
    async def buy_side(self, ctx):
        await ctx.defer()
        menu = None
        with open(self.menu_path, "r") as file:
            menu = json.load(file)
        sides = menu.get("Sides", [])

        if len(sides) == 0:
            await ctx.respond("There are currently no sides in the menu!", ephemeral=True)
            return
        elif len(sides) <= 25:
            class SideView(discord.ui.View):
                def __init__(self, inv_path, bg_path, menu_path):
                    super().__init__(timeout=60.0)     
                    self.inv_path = inv_path
                    self.bg_path = bg_path
                    self.menu_path = menu_path      
                async def interaction_check(self, interaction):
                    if interaction.user.id == ctx.author.id:
                        async with aiosqlite.connect(self.bg_path) as db:
                            async with db.execute(f"SELECT burgergeld FROM guild_{ctx.guild.id} WHERE user_id = ?", (ctx.author.id,)) as bg_cursor:
                                bg_result = await bg_cursor.fetchone()
                                if bg_result is None:
                                    await ctx.edit(content="You currently don't have Burgergeld!", view=None, embed=None)
                                    return False
                                price = None
                                with open(self.menu_path, "r") as file:
                                    menu_data = json.load(file)
                                    for side in menu_data.get("Sides", []):
                                        if side["id"] == int(interaction.custom_id):
                                            price = side["price"]
                                    if price > bg_result[0]:
                                        await ctx.edit(content="You don't have enough Burgergeld to buy this side!", view=None, embed=None)
                                        return False
                        async with aiosqlite.connect(self.inv_path) as db:
                            result = await db.execute_fetchall(f"SELECT * FROM guild_{ctx.guild.id} WHERE user_id = ? AND menu_id = ?", (ctx.author.id, interaction.custom_id))
                            if len(result) == 0:
                                await db.execute(f"INSERT INTO guild_{ctx.guild.id} (user_id, menu_id, amount) VALUES (?, ?, 1)", (ctx.author.id, interaction.custom_id))
                            else:
                                await db.execute(f"UPDATE guild_{ctx.guild.id} SET amount = amount + 1 WHERE user_id = ? AND menu_id = ?", (ctx.author.id, interaction.custom_id))
                            await db.commit()
                        async with aiosqlite.connect(self.bg_path) as db:
                            await db.execute(f"UPDATE guild_{ctx.guild.id} SET burgergeld = burgergeld - ? WHERE user_id = ?", (price, ctx.author.id))
                            await db.commit()
                        await ctx.edit(content="You bought a side!", view=None, embed=None)
                        return True
                    else:
                        await interaction.response.send_message("You can't interact with this menu!", ephemeral=True)
                        self.stop()
                        return False
                async def on_timeout(self):
                    self.clear_items()
                    self.stop()
                    await ctx.edit(content="The menu timed out! Please re-run the Buy Command!", view=None, embed=None)
            view = SideView(self.inv_path, self.bg_path, self.menu_path)
            row = 0
            i = 0
            for side in sides:
                if i % 5 == 0 and i != 0:
                    row += 1
                view.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, label=side["name"], row=row, custom_id=str(side["id"])))
                i += 1
            embed = discord.Embed(title="Burger-Menu", color=discord.Color.blurple())
            embed.add_field(name="Sides", value="\n".join([f"{side['name']} - {side['price']} BG" for side in sides]), inline=False)
            await ctx.respond(embed=embed, view=view)
        elif len(sides) > 25:
            await ctx.respond("There are too many sides in the menu to display them all at once! Please get back to Wolfiii!", ephemeral=True)

    @discord.slash_command(name="inventory", description="Shows your current inventory.")
    async def inventory(self, ctx):
        await ctx.defer()
        async with aiosqlite.connect(self.inv_path) as db:
            result = await db.execute_fetchall(f"SELECT * FROM guild_{ctx.guild.id} WHERE user_id = ?", (ctx.author.id,))
            if len(result) == 0:
                await ctx.respond("You currently don't have anything in your inventory!")
                return
            with open(self.menu_path, "r") as file:
                menu_data = json.load(file)
            burgers = menu_data.get("Burger", [])
            sides = menu_data.get("Sides", [])
            inv = {}
            for item in result:
                for burger in burgers:
                    if burger["id"] == item[1]:
                        if inv.get(burger["name"]) is None:
                            inv[burger["name"]] = item[2]
                        else:
                            inv[burger["name"]] += item[2]
                for side in sides:
                    if side["id"] == item[1]:
                        if inv.get(side["name"]) is None:
                            inv[side["name"]] = item[2]
                        else:
                            inv[side["name"]] += item[2]
            embed = discord.Embed(title="Inventory", color=discord.Color.blurple())
            for item, amount in inv.items():
                embed.add_field(name=item, value=amount, inline=False)
            await ctx.respond(embed=embed)



    consume_command = discord.SlashCommandGroup(name="consume", description="Commands for the Burger-Menu.")
    @consume_command.command(name="burger", description="Consume a burger from your inventory.")
    async def consume_burger(self, ctx):
        await ctx.defer()
        menu = None
        with open(self.menu_path, "r") as file:
            menu = json.load(file)
        burgers = menu.get("Burger", [])
        raw_inventory = None
        async with aiosqlite.connect(self.inv_path) as db:
            raw_inventory = await db.execute_fetchall(f"SELECT * FROM guild_{ctx.guild.id} WHERE user_id = ?", (ctx.author.id,))

        for item in burgers[:]: # Copy the list to avoid modifying it while iterating -> Causes to skip items otherwise
            is_burger = False
            for inv_item in raw_inventory:
                if item["id"] == inv_item[1]:
                    is_burger = True
                    item["amount"] = inv_item[2]
                    break
            if not is_burger:
                burgers.remove(item)
        if len(burgers) == 0:
            await ctx.respond("You currently don't have any burgers in your inventory!", ephemeral=True)
            return
        elif len(burgers) > 25:
            await ctx.respond("There are too many burgers in your inventory to display them all at once! Please get back to Wolfiii!", ephemeral=True)
            return
        

        class ConsumeBurgerView(discord.ui.View):
            def __init__(self, inv_path, bg_path, menu_path):
                super().__init__(timeout=60.0)
                self.inv_path = inv_path
                self.bg_path = bg_path
                self.menu_path = menu_path
            async def interaction_check(self, interaction):
                if interaction.user.id == ctx.author.id:
                    async with aiosqlite.connect(self.inv_path) as db:
                        result = await db.execute(f"SELECT * FROM guild_{ctx.guild.id} WHERE user_id = ? AND menu_id = ?", (ctx.author.id, interaction.custom_id))
                        result = await result.fetchone()
                        if result[2] == 1: # If the user only has one of the item, delete the row
                            await db.execute(f"DELETE FROM guild_{ctx.guild.id} WHERE user_id = ? AND menu_id = ?", (ctx.author.id, interaction.custom_id))
                        else:
                            await db.execute(f"UPDATE guild_{ctx.guild.id} SET amount = amount - 1 WHERE user_id = ? AND menu_id = ?", (ctx.author.id, interaction.custom_id))
                        await db.commit()
                    await ctx.edit(content="You consumed a burger!", view=None, embed=None)
                else:
                    await interaction.response.send_message("You can't interact with this menu!", ephemeral=True)
                    self.stop()
                    return False
            async def on_timeout(self):
                self.clear_items()
                self.stop()
                await ctx.edit(content="The menu timed out! Please re-run the Consume Command!", view=None, embed=None)
        view = ConsumeBurgerView(self.inv_path, self.bg_path, self.menu_path)
        row = 0
        i = 0
        embed = discord.Embed(title="Inventory", color=discord.Color.blurple())
        for burger in burgers:
            if i % 5 == 0 and i != 0:
                row += 1
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, label=burger["name"], row=row, custom_id=str(burger["id"])))
            
            embed.add_field(name=burger["name"], value=f"Amount: {burger["amount"]}", inline=False)
            i += 1
        await ctx.respond(embed=embed, view=view, ephemeral=True)

    @consume_command.command(name="side", description="Consume a side from your inventory.")
    async def consume_side(self, ctx):
        await ctx.defer()
        menu = None
        with open(self.menu_path, "r") as file:
            menu = json.load(file)
        sides = menu.get("Sides", [])
        raw_inventory = None
        async with aiosqlite.connect(self.inv_path) as db:
            raw_inventory = await db.execute_fetchall(f"SELECT * FROM guild_{ctx.guild.id} WHERE user_id = ?", (ctx.author.id,))

        for item in sides[:]: # Copy the list to avoid modifying it while iterating -> Causes to skip items otherwise
            is_side = False
            for inv_item in raw_inventory:
                if item["id"] == inv_item[1]:
                    is_side = True
                    item["amount"] = inv_item[2]
                    break
            if not is_side:
                sides.remove(item)
        if len(sides) == 0:
            await ctx.respond("You currently don't have any sides in your inventory!", ephemeral=True)
            return
        elif len(sides) > 25:
            await ctx.respond("There are too many sides in your inventory to display them all at once! Please get back to Wolfiii!", ephemeral=True)
            return
        
        class ConsumeSideView(discord.ui.View):
            def __init__(self, inv_path, bg_path, menu_path):
                super().__init__(timeout=60.0)
                self.inv_path = inv_path
                self.bg_path = bg_path
                self.menu_path = menu_path
            async def interaction_check(self, interaction):
                if interaction.user.id == ctx.author.id:
                    async with aiosqlite.connect(self.inv_path) as db:
                        result = await db.execute(f"SELECT * FROM guild_{ctx.guild.id} WHERE user_id = ? AND menu_id = ?", (ctx.author.id, interaction.custom_id))
                        result = await result.fetchone()
                        if result[2] == 1: # If the user only has one of the item, delete the row
                            await db.execute(f"DELETE FROM guild_{ctx.guild.id} WHERE user_id = ? AND menu_id = ?", (ctx.author.id, interaction.custom_id))
                        else:
                            await db.execute(f"UPDATE guild_{ctx.guild.id} SET amount = amount - 1 WHERE user_id = ? AND menu_id = ?", (ctx.author.id, interaction.custom_id))
                        await db.commit()
                    await ctx.edit(content="You consumed a side!", view=None, embed=None)
                else:
                    await interaction.response.send_message("You can't interact with this menu!", ephemeral=True)
                    self.stop()
                    return False
            async def on_timeout(self):
                self.clear_items()
                self.stop()
                await ctx.edit(content="The menu timed out! Please re-run the Consume Command!", view=None, embed=None)
        view = ConsumeSideView(self.inv_path, self.bg_path, self.menu_path)
        row = 0
        i = 0
        embed = discord.Embed(title="Inventory", color=discord.Color.blurple())
        for side in sides:
            if i % 5 == 0 and i != 0:
                row += 1
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, label=side["name"], row=row, custom_id=str(side["id"])))
            embed.add_field(name=side["name"], value=f"Amount: {side['amount']}", inline=False)
            i += 1
        await ctx.respond(embed=embed, view=view, ephemeral=True)

    gift_command = discord.SlashCommandGroup(name="gift", description="Gift a burger or side to another user.")
    @gift_command.command(name="gift", description="Gift a burger to another user.")
    async def gift_burger(self, ctx):
        await ctx.defer()
        await ctx.respond("This command is not implemented yet!", ephemeral=True)
    


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
