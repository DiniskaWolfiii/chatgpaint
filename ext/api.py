import logging
import os

import aiohttp.web
import discord


async def _build_embed(data: dict) -> discord.Embed:
    embed = discord.Embed(
        title=data.get("title"),
        description=data.get("description"),
    )
    color = data.get("color")
    if color is not None:
        embed.color = int(color)
    else:
        embed.color = 0x1abc9c

    for field in data.get("fields", []):
        embed.add_field(
            name=field.get("name", ""),
            value=field.get("value", ""),
            inline=field.get("inline", False),
        )

    if footer := data.get("footer"):
        embed.set_footer(text=footer)
    if image_url := data.get("image_url"):
        embed.set_image(url=image_url)
    if thumbnail_url := data.get("thumbnail_url"):
        embed.set_thumbnail(url=thumbnail_url)

    return embed


def _build_poll(data: dict) -> discord.Poll:
    answers = data.get("answers", [])
    poll = discord.Poll(
        question=data["question"],
        duration=int(data.get("duration", 24)),
        allow_multiselect=bool(data.get("allow_multiselect", False)),
    )
    for answer in answers:
        if isinstance(answer, dict):
            poll.add_answer(text=answer.get("text", ""), emoji=answer.get("emoji"))
        else:
            poll.add_answer(text=answer)
    return poll


def create_app(bot: discord.Bot) -> aiohttp.web.Application:
    api_secret = os.getenv("API_SECRET")
    app = aiohttp.web.Application()

    def _auth(request: aiohttp.web.Request) -> bool:
        if not api_secret:
            return False
        auth = request.headers.get("Authorization", "")
        return auth == f"Bearer {api_secret}"

    async def send_dm(request: aiohttp.web.Request) -> aiohttp.web.Response:
        if not _auth(request):
            return aiohttp.web.json_response({"error": "Unauthorized"}, status=401)

        try:
            body = await request.json()
        except Exception:
            return aiohttp.web.json_response({"error": "Invalid JSON"}, status=400)

        user_id = body.get("user_id")
        embed_data = body.get("embed")

        if not user_id:
            return aiohttp.web.json_response({"error": "user_id is required"}, status=400)
        if not embed_data or not isinstance(embed_data, dict):
            return aiohttp.web.json_response({"error": "embed object is required"}, status=400)

        try:
            user = await bot.fetch_user(int(user_id))
        except discord.NotFound:
            return aiohttp.web.json_response({"error": "User not found"}, status=404)
        except discord.HTTPException as e:
            logging.warning(f"API /dm fetch_user failed: {e}")
            return aiohttp.web.json_response({"error": "Failed to fetch user"}, status=500)

        try:
            embed = await _build_embed(embed_data)
            await user.send(embed=embed)
        except discord.Forbidden:
            return aiohttp.web.json_response({"error": "Cannot send DM to this user"}, status=403)
        except discord.HTTPException as e:
            logging.warning(f"API /dm send failed: {e}")
            return aiohttp.web.json_response({"error": "Failed to send DM"}, status=500)

        logging.info(f"API: DM sent to user {user_id}")
        return aiohttp.web.json_response({"success": True})

    async def send_message(request: aiohttp.web.Request) -> aiohttp.web.Response:
        if not _auth(request):
            return aiohttp.web.json_response({"error": "Unauthorized"}, status=401)

        try:
            body = await request.json()
        except Exception:
            return aiohttp.web.json_response({"error": "Invalid JSON"}, status=400)

        channel_id = body.get("channel_id")
        content = body.get("content")

        if not channel_id:
            return aiohttp.web.json_response({"error": "channel_id is required"}, status=400)
        if not content or not isinstance(content, str):
            return aiohttp.web.json_response({"error": "content is required"}, status=400)

        try:
            channel = bot.get_channel(int(channel_id)) or await bot.fetch_channel(int(channel_id))
        except discord.NotFound:
            return aiohttp.web.json_response({"error": "Channel not found"}, status=404)
        except discord.HTTPException as e:
            logging.warning(f"API /message fetch_channel failed: {e}")
            return aiohttp.web.json_response({"error": "Failed to fetch channel"}, status=500)

        if not isinstance(channel, discord.abc.Messageable):
            return aiohttp.web.json_response({"error": "Channel is not messageable"}, status=400)

        try:
            await channel.send(content=content)
        except discord.Forbidden:
            return aiohttp.web.json_response({"error": "Cannot send message to this channel"}, status=403)
        except discord.HTTPException as e:
            logging.warning(f"API /message send failed: {e}")
            return aiohttp.web.json_response({"error": "Failed to send message"}, status=500)

        logging.info(f"API: message sent to channel {channel_id}")
        return aiohttp.web.json_response({"success": True})

    async def send_poll(request: aiohttp.web.Request) -> aiohttp.web.Response:
        if not _auth(request):
            return aiohttp.web.json_response({"error": "Unauthorized"}, status=401)

        try:
            body = await request.json()
        except Exception:
            return aiohttp.web.json_response({"error": "Invalid JSON"}, status=400)

        channel_id = body.get("channel_id")
        question = body.get("question")
        answers = body.get("answers")

        if not channel_id:
            return aiohttp.web.json_response({"error": "channel_id is required"}, status=400)
        if not question or not isinstance(question, str):
            return aiohttp.web.json_response({"error": "question is required"}, status=400)
        if not answers or not isinstance(answers, list):
            return aiohttp.web.json_response({"error": "answers list is required"}, status=400)

        try:
            channel = bot.get_channel(int(channel_id)) or await bot.fetch_channel(int(channel_id))
        except discord.NotFound:
            return aiohttp.web.json_response({"error": "Channel not found"}, status=404)
        except discord.HTTPException as e:
            logging.warning(f"API /poll fetch_channel failed: {e}")
            return aiohttp.web.json_response({"error": "Failed to fetch channel"}, status=500)

        if not isinstance(channel, discord.abc.Messageable):
            return aiohttp.web.json_response({"error": "Channel is not messageable"}, status=400)

        try:
            poll = _build_poll(body)
        except ValueError as e:
            return aiohttp.web.json_response({"error": str(e)}, status=400)

        try:
            await channel.send(poll=poll)
        except discord.Forbidden:
            return aiohttp.web.json_response({"error": "Cannot send poll to this channel"}, status=403)
        except discord.HTTPException as e:
            logging.warning(f"API /poll send failed: {e}")
            return aiohttp.web.json_response({"error": "Failed to send poll"}, status=500)

        logging.info(f"API: poll sent to channel {channel_id}")
        return aiohttp.web.json_response({"success": True})

    app.router.add_post("/api/dm", send_dm)
    app.router.add_post("/api/message", send_message)
    app.router.add_post("/api/poll", send_poll)
    return app


class ApiServer:
    def __init__(self, bot: discord.Bot):
        self._bot = bot
        self._runner: aiohttp.web.AppRunner | None = None

    async def start(self):
        port = int(os.getenv("API_PORT", "8080"))
        app = create_app(self._bot)
        self._runner = aiohttp.web.AppRunner(app)
        await self._runner.setup()
        site = aiohttp.web.TCPSite(self._runner, "0.0.0.0", port)
        await site.start()
        logging.warning(f"API server listening on port {port}")

    async def stop(self):
        if self._runner:
            await self._runner.cleanup()
            self._runner = None
