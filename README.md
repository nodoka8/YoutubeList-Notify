### .envの項目
- BOT_TOKEN：Discord Botのトークン 
- PLAYLIST_ID：YouTubeの再生リストID
- TARGET_CHANNEL_ID：DiscordのターゲットチャンネルID
- YOUTUBE_API_KEY：YouTube DATA APIキー
- CHECK_INTERVAL_SECONDS：更新の確認間隔（s）


### uvのインストール
```
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# pip
pip install uv

# Homebrew
brew install uv
```

### 依存関係のインストール
```
uv sync
```

### スクリプトの実行
``` 
uv run python main.py
 ```