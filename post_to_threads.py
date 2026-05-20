import anthropic, requests, os, random, time

ACCESS_TOKEN = os.environ.get("THREADS_ACCESS_TOKEN", "")
USER_ID = "36197973126460747"
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GITHUB_RAW_IMG = "https://raw.githubusercontent.com/headmkyoto-star/saki-cameron-threads/main/images/"
GITHUB_RAW_VID = "https://raw.githubusercontent.com/headmkyoto-star/saki-cameron-threads/main/videos/"
GITHUB_API_IMG = "https://api.github.com/repos/headmkyoto-star/saki-cameron-threads/contents/images"
GITHUB_API_VID = "https://api.github.com/repos/headmkyoto-star/saki-cameron-threads/contents/videos"

def get_media():
    """images/とvideos/からランダムに1つメディアを選ぶ"""
    media_list = []
    try:
        r = requests.get(GITHUB_API_IMG)
        if r.status_code == 200:
            for f in r.json():
                n = f.get("name", "")
                if n.lower().endswith((".jpg", ".jpeg", ".png")) and not n.startswith("."):
                    media_list.append(("IMAGE", GITHUB_RAW_IMG + n.replace(" ", "_")))
    except Exception as e:
        print(f"画像取得エラー: {e}")
    try:
        r = requests.get(GITHUB_API_VID)
        if r.status_code == 200:
            for f in r.json():
                n = f.get("name", "")
                if n.lower().endswith((".mp4", ".mov")) and not n.startswith("."):
                    media_list.append(("VIDEO", GITHUB_RAW_VID + n.replace(" ", "_")))
    except Exception as e:
        print(f"動画取得エラー: {e}")
    if media_list:
        return random.choice(media_list)
    return (None, None)

def generate_post():
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    if random.random() < 0.2:
        p = "ドライヘッドスパ専門サロンのセラピストとして営業投稿を作成。必ず改行して絵文字を入れる。70分3980円を含む。ハッシュタグなし。150文字以内。投稿文のみ出力。"
    else:
        p = "ドライヘッドスパ専門サロンのセラピストとして日常日記系の投稿を作成。必ず改行して絵文字を入れる。ハッシュタグなし。150文字以内。営業色なし。投稿文のみ出力。"
    msg = client.messages.create(model="claude-opus-4-6", max_tokens=300, messages=[{"role": "user", "content": p}])
    return msg.content[0].text.strip()

def post_to_threads(text, media_type, media_url):
    base = f"https://graph.threads.net/v1.0/{USER_ID}/threads"
    if media_type == "IMAGE":
        params = {"media_type": "IMAGE", "image_url": media_url, "text": text, "access_token": ACCESS_TOKEN}
    elif media_type == "VIDEO":
        params = {"media_type": "VIDEO", "video_url": media_url, "text": text, "access_token": ACCESS_TOKEN}
    else:
        params = {"media_type": "TEXT", "text": text, "access_token": ACCESS_TOKEN}
    r = requests.post(base, params=params)
    if r.status_code != 200:
        if media_type != "TEXT":
            print(f"⚠️ メディア投稿失敗、テキストのみで再試行: {r.text}")
            return post_to_threads(text, "TEXT", None)
        return r
    cid = r.json().get("id")
    if media_type == "VIDEO":
        for i in range(30):
            time.sleep(10)
            try:
                status = requests.get(f"https://graph.threads.net/v1.0/{cid}",
                                       params={"fields": "status", "access_token": ACCESS_TOKEN}).json().get("status", "")
                print(f"動画処理ステータス ({i+1}/30): {status}")
                if status == "FINISHED":
                    break
                if status == "ERROR":
                    print("動画処理エラー、テキストのみで再試行")
                    return post_to_threads(text, "TEXT", None)
            except Exception as e:
                print(f"ステータス確認エラー: {e}")
    else:
        time.sleep(30)
    return requests.post(f"https://graph.threads.net/v1.0/{USER_ID}/threads_publish",
                         params={"creation_id": cid, "access_token": ACCESS_TOKEN})

text = generate_post()
print(f"投稿テキスト:\n{text}\n")
mtype, murl = get_media()
if murl:
    print(f"メディア ({mtype}): {murl}\n")
    r = post_to_threads(text, mtype, murl)
else:
    print("メディアなし、テキストのみ投稿\n")
    r = post_to_threads(text, "TEXT", None)
print("✅ 投稿成功！" if r.status_code == 200 else f"❌ 投稿失敗: {r.text}")
