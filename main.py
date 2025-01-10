from typing import Final
import os
from dotenv import load_dotenv
from discord import Intents, Interaction, ButtonStyle, Member
from discord.ext import commands
from discord.ui import Button, View
import asyncio

# STEP 0: LOAD TOKEN FROM SOMEWHERE SAFE
load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')

# STEP 1: BOT SETUP
intents: Intents = Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# VALORANT maps
maps = ["Ascent", "Bind", "Icebox", "Split", "Sunset"]


# Map pick/ban state
class MapPickBan:
    def __init__(self):
        self.bans = []
        self.last_map = None


# Pick-ban logic
@bot.command()
async def pickban(ctx, opponent: Member):
    game_state = MapPickBan()
    players = [ctx.author, opponent]
    
    view = View()
    await ctx.send(f"{ctx.author.mention} and {opponent.mention} are doing the pickban!", view=view)
    view.add_item(
        Button(
            label="First",
            style=ButtonStyle.success,
            custom_id="first"
        )
    )
    view.add_item(
        Button(
            label="Second",
            style=ButtonStyle.success,
            custom_id="second"
        )
    )

    view.add_item(Button(label="Cancel",style=ButtonStyle.secondary,custom_id="cancel"))
    
    await ctx.send(f"{players[0].mention}, are you banning first or second?", view=view)

    def button_check(interaction):
        if (interaction.user == players[0]) or (interaction.user == ctx.author and interaction.data["custom_id"] == "cancel"):
            return True
        asyncio.create_task(interaction.response.send_message("You're not participating in this pickban!", ephemeral=True))
        return False

    try:
        interaction = await bot.wait_for("interaction", timeout=30.0, check=button_check)
        if(button_check(interaction) == False):
            await interaction.response.send_message("You're not participating in this pickban!", ephemeral=True)
        if(interaction.data["custom_id"] == "cancel"):
            await interaction.response.send_message("Pickban process was canceled.")
            view.stop()
            return
        if(interaction.data["custom_id"] == "second"):
            temp = players[0]
            players[0] = players[1]
            players[1] = temp
        await interaction.response.send_message(f"{players[0].mention} will be banning first!")
    except asyncio.TimeoutError:
        await ctx.send(f"{players[0].mention} took too long to respond. Exiting pick-ban.")
                
        view.stop()
        return

    # Ban phase happens twice
    for j in range(2):
        for i in range(2):
            current_player = players[i]
            remaining_maps = [map_ for map_ in maps if map_ not in game_state.bans]
            view = View()

            for map_name in remaining_maps:
                view.add_item(
                    Button(
                        label=map_name,
                        style=ButtonStyle.danger,
                        custom_id=map_name
                    )
                )
            view.add_item(Button(label="Cancel",style=ButtonStyle.secondary,custom_id="cancel"))
            

            await ctx.send(f"{current_player.mention}, choose a map to ban:", view=view)

            def button_check(interaction):
                if (interaction.user == current_player and interaction.data["custom_id"] in remaining_maps) or (interaction.user == ctx.author and interaction.data["custom_id"] == "cancel"):
                    return True
                asyncio.create_task(interaction.response.send_message("You're not participating in this pickban!", ephemeral=True))
                return False

            try:
                interaction = await bot.wait_for("interaction", timeout=300.0, check=button_check)
                if(button_check(interaction) == False):
                    await interaction.response.send_message("You're not participating in this pickban!", ephemeral=True)
                if(interaction.data["custom_id"] == "cancel"):
                    await interaction.response.send_message("Pick-ban process was canceled.")
                    view.stop()
                    return
                banned_map = interaction.data["custom_id"]
                game_state.bans.append(banned_map)
                await interaction.response.send_message(f"{banned_map} has been banned!")
                
            except asyncio.TimeoutError:
                await ctx.send(f"{current_player.mention} took too long to respond. Exiting pick-ban.")
                
                view.stop()
                return

    # Last map and side selection
    remaining_maps = [map_ for map_ in maps if map_ not in game_state.bans]
    game_state.last_map = remaining_maps[0]
    side_picker = players[0]

    view = View()
    view.add_item(Button(label="Attack", style=ButtonStyle.success, custom_id="attack"))
    view.add_item(Button(label="Defense", style=ButtonStyle.success, custom_id="defense"))
    view.add_item(Button(label="Cancel",style=ButtonStyle.secondary,custom_id="cancel"))

    await ctx.send(f"The last map is **{game_state.last_map}**. {side_picker.mention}, choose your starting side:", view=view)

    def button_check(interaction):
        if (interaction.user == players[0]) or (interaction.user == ctx.author and interaction.data["custom_id"] == "cancel"):
            return True
        asyncio.create_task(interaction.response.send_message("You're not participating in this pickban!", ephemeral=True))
        return False

    try:
        interaction = await bot.wait_for("interaction", timeout=300.0, check=button_check)
        if(button_check(interaction) == False):
            await interaction.response.send_message("You're not participating in this pickban!", ephemeral=True)
        if(interaction.data["custom_id"] == "cancel"):
            await interaction.response.send_message("Pickban process was canceled.") 
            view.stop()
            return
        chosen_side = interaction.data["custom_id"]
        await interaction.response.send_message(f"{side_picker.mention} has chosen to start on **{chosen_side.upper()}**!")
          
    except asyncio.TimeoutError:
        await ctx.send(f"{side_picker.mention} took too long to respond. Exiting pickban.")
          
        view.stop()
        return

    # Summary
    await ctx.send(
        f"**Pick-Ban Summary**\n"
        f"Picked Map: {game_state.last_map}\n"
        f"{side_picker.mention} will start on **{chosen_side.upper()}**!"
    )

class RockPaperScissors(View):
    def __init__(self, player1, player2):
        super().__init__(timeout=60)            # add a timeout for the game
        self.player1 = player1
        self.player2 = player2
        self.choices = {player1: None, player2: None}
        self.game_result = None

    async def interaction_check(self, interaction: Interaction) -> bool:
        # Only allow participating players to interact with the button
        if interaction.user not in [self.player1, self.player2]:
            await interaction.response.send_message("You are not part of this game.", ephemeral=True)
            return False
        return True
    
    async def button_callback(self, interaction: Interaction, choice: str):
        # Record the player's choice
        self.choices[interaction.user] = choice
        await interaction.response.send_message(f"You chose {choice}!", ephemeral=True)

        # Disable the buttons for the player that already picked
        for item in self.children:
            if isinstance(item, Button) and interaction.user in [self.player1, self.player2]:
                item.disabled = True
    
        if all(self.choices.values()):
            self.stop()
    
    def add_buttons(self):
        for option in ["Rock", "Paper", "Scissors"]:
            button = Button(label=option, style=ButtonStyle.primary)
            button.callback = lambda interaction, choice=option: asyncio.create_task(self.button_callback(interaction, choice))
            self.add_item(button)

@bot.command()
async def rps(ctx, opponent: Member):
    if opponent == ctx.author:
        await ctx.send("You can't play Rock-Paper-Scissors with yourself!")
        return

    # Initialize the game
    view = RockPaperScissors(ctx.author, opponent)
    view.add_buttons()

    await ctx.send(f"{ctx.author.mention} vs {opponent.mention}: Rock, Paper, Scissors!", view=view)
    
    # Wait for the game to finish
    await view.wait()

    # Check the result
    player1_choice = view.choices[ctx.author]
    player2_choice = view.choices[opponent]

    if not all(view.choices.values()):  # Timeout or incomplete game
        await ctx.send("The game timed out. Please try again.")
        return

    # Determine the winner
    results = {
        ("Rock", "Scissors"): ctx.author,
        ("Paper", "Rock"): ctx.author,
        ("Scissors", "Paper"): ctx.author,
        ("Scissors", "Rock"): opponent,
        ("Rock", "Paper"): opponent,
        ("Paper", "Scissors"): opponent,
    }

    if player1_choice == player2_choice:
        result_message = f"It's a tie! Both players chose {player1_choice}."
    else:
        winner = results.get((player1_choice, player2_choice))
        result_message = f"The winner is {winner.mention}! {ctx.author.mention} chose {player1_choice} and {opponent.mention} chose {player2_choice}."

    # Send the result
    await ctx.send(result_message)


# Bot startup message
@bot.event
async def on_ready():
    print(f"{bot.user} is now running!")


# STEP 5: MAIN ENTRY POINT
def main() -> None:
    bot.run(TOKEN)


if __name__ == '__main__':
    main()
