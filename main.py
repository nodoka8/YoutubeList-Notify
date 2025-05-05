import discord
from discord.ext import tasks, commands
import aiohttp
import json
import os
import asyncio
from dotenv import load_dotenv

# 環境変数をロード
load_dotenv()

# ----------- 設定項目 ------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
PLAYLIST_ID = os.getenv("PLAYLIST_ID")
TARGET_CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID"))  # 通知先のチャンネルID
STATE_FILE = "latest_video.json"
CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", 20))  # デフォルトは20秒
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")  # YouTube Data APIキーを設定


print("Bot Token:", BOT_TOKEN)
print("Playlist ID:", PLAYLIST_ID)
print("Target Channel ID:", TARGET_CHANNEL_ID)
# ----------------------------------

YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/playlistItems"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

def load_last_position():
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE, "r") as f:
        return json.load(f).get("position")

def save_last_position(position):
    with open(STATE_FILE, "w") as f:
        json.dump({"position": position}, f)

async def fetch_all_videos():
    videos = []
    next_page_token = None

    while True:
        params = {
            "part": "snippet",
            "playlistId": PLAYLIST_ID,
            "maxResults": 50,  # 最大50件取得
            "key": YOUTUBE_API_KEY,
            "pageToken": next_page_token
        }

        # Noneの値を持つキーを削除
        params = {key: value for key, value in params.items() if value is not None}

        # デバッグ用にparamsの内容をログ出力
        #print("YouTube APIリクエストパラメータ:", params)

        # pageTokenがNoneの場合は無視する
        invalid_params = {key: value for key, value in params.items() if key != "pageToken" and not value}
        if invalid_params:
            print(f"無効なパラメータ: {invalid_params}")
            raise ValueError("YouTube APIリクエストのパラメータに無効な値があります。")

        async with aiohttp.ClientSession() as session:
            async with session.get(YOUTUBE_API_URL, params=params) as response:
                if response.status != 200:
                    error_data = await response.json()
                    print(f"YouTube APIエラー: {error_data}")
                    raise ValueError(f"YouTube APIリクエスト失敗: HTTP {response.status}")
                data = await response.json()

                #print(f"取得データ: {data}")

                if "items" not in data or not data["items"]:
                    break

                videos.extend(data["items"])

                next_page_token = data.get("nextPageToken")
                if not next_page_token:
                    break

    # positionで昇順に並べ替え
    sorted_videos = sorted(
        videos,
        key=lambda x: x["snippet"].get("position", 0)
    )

    return sorted_videos

@tasks.loop(seconds=CHECK_INTERVAL_SECONDS)
async def check_playlist():
    videos = await fetch_all_videos()
    if not videos:
        print("動画が見つかりません。")
        return

    last_position = load_last_position()
    new_videos = [
        {
            "video_id": video["snippet"]["resourceId"]["videoId"],
            "title": video["snippet"]["title"],
            "url": f"https://www.youtube.com/watch?v={video['snippet']['resourceId']['videoId']}&list={PLAYLIST_ID}&index={video['snippet']['position'] + 1}&ab_channel={video['snippet']['channelTitle']}"
        }
        for video in videos
        if video["snippet"].get("position", 0) > (last_position or -1)
    ]

    if new_videos:
        channel = bot.get_channel(TARGET_CHANNEL_ID)
        if channel:
            for video in new_videos:
                await channel.send(f"📢 プレイリストに新しい動画が追加されました！\n**{video['title']}**\n{video['url']}")
                print(f"✅ 通知を送信: {video['title']}")
            save_last_position(videos[-1]["snippet"].get("position", 0))
        else:
            print("❌ 通知チャンネルが見つかりません。")
    else:
        print("⏳ 変更なし")

@bot.event
async def on_ready():
    print(f"✅ Bot起動完了: {bot.user}")
    check_playlist.start()

bot.run(BOT_TOKEN)