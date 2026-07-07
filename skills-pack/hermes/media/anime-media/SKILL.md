---
name: anime-media
description: 免费无key的动漫/二次元素材查询。Jikan(MyAnimeList) 提供动漫元数据，NekosBest 提供二次元图片/GIF。当主人需要查动漫作品、找二次元表情包/头像素材、给内容加动漫元素时使用。
---

# anime-media — 动漫元数据 + 二次元素材

## 何时使用

- 查动漫作品（评分、集数、简介、封面）→ `media-cli anime`
- 要**通用**二次元图片 / **情绪动作 GIF**（笑、摸头、拥抱等）→ `media-cli neko`
- 想看 NekosBest 都有哪些分类 → `media-cli neko-list`

## 🚦 请求意图判定（IP/角色关键词场景先读这段！）

当主人说 "找个 **XX** 的动图/表情包/图片"（XX 是 IP/角色/梗，如"JoJo"、"火影"、"派蒙"）时，先分辨真实意图：

| 意图 | 举例 | 走哪条路 |
|---|---|---|
| **A. 只要动漫风氛围** | 主人只是想在群里活跃气氛，"JoJo" 是随口举例 | `media-cli neko --category smile/dance/laugh` 通用动作 GIF ✅ |
| **B. 要该 IP 相关素材（元数据/封面/推荐）** | 想聊 JoJo 这部作品、发角色卡、配简介 | `media-cli anime "jojo"` 拿封面+简介+评分，可搭 `neko` 情绪 GIF 组合发 ✅ |
| **C. 必须精确该 IP 的动图/桥段** | "承太郎欧拉欧拉那段"、"迪奥 sowsow" 等具体桥段 | 技能内**无稳定路径**，如实告知主人做不到，不要外求兜底 ❌ |

**默认动作**：
- 关键词**只有 IP 名**、没有具体动作/桥段 → 先按 **B** 处理（元数据+组合），主动问主人 "要动漫本身的信息+封面，还是要该 IP 的动图桥段？"
- 关键词只是动作/情绪（"想要个大笑的动图"、"摸头动图"）→ 直接 A，`neko --category laugh/pat`
- 场景 C 目前技能不覆盖，直说 → 不要自行外扩到搜索引擎/爬站点等不稳定路径

## 数据源

| 命令 | 数据源 | 特色 |
|---|---|---|
| `anime` | Jikan v4 (MyAnimeList 非官方 API) | 动漫百科级数据，含评分、集数、genres、简介、封面、片头曲 |
| `neko` | nekos.best v2 | 高质量二次元图/GIF，含**画师署名**（Pixiv 链接），可商用需自行确认 |

## 用法

### 1. Jikan 动漫搜索

```bash
media-cli anime "鬼灭之刃" --limit 3
media-cli anime "spy family" --type tv --limit 1
media-cli anime "君の名は" --type movie
```

参数：
- `--type`：`tv` / `movie` / `ova` / `special` / `ona` / `music`（不传则不过滤）
- `--limit`：默认 3，Jikan 上限 25

输出字段：标题（原文/日文）、评分、集数、状态、genres、封面 URL、简介。

**Jikan 速率限制**：官方是每秒 3 请求 / 每分钟 60 请求。CLI 已带 5xx 自动重试，不用担心偶发抖动。

### 2. NekosBest 图片/GIF

```bash
# 单张 waifu 图
media-cli neko --category waifu --amount 1

# 一次拿 5 张（最大 20）
media-cli neko --category husbando --amount 5

# 情绪 GIF（击掌、微笑、大笑等）
media-cli neko --category highfive --amount 1
media-cli neko --category smile --amount 1
```

**分类查看**：
```bash
media-cli neko-list
```

分类分两类：
- **图片类**（`png` 格式）：`neko` / `waifu` / `husbando` / `kitsune`
- **动作 GIF 类**（`gif` 格式）：`smile` / `wave` / `poke` / `tickle` / `laugh` / `pat` / `hug` / `kiss` / `cry` / `dance` / `stare` / `wink` / 等 40+ 种情绪动作

返回字段含：图片 URL、画师名 `artist_name`、Pixiv 原图链接 `source_url`、图片尺寸 `dimensions`。

### 3. 常见组合玩法

**给公众号/小红书文章找配图**：
```bash
media-cli neko --category waifu --amount 3
```

### 3b. 📥 批量下载素材（含画师版权清单）

```bash
# 下载 10 张 waifu 图到 ~/media-cache/waifu
media-cli neko-download --category waifu --amount 10 --outdir ~/media-cache/waifu

# 下载 20 张 pat（摸头 GIF）
media-cli neko-download --category pat --amount 20 --outdir ~/media-cache/pat-gif

# 默认目录 ~/media-cache/neko
media-cli neko-download --amount 5
```

**特色**：
- 自动分批调用（NekosBest 单次上限 20 张）
- 每张图之间温柔 sleep 0.5s，避免打扰对方服务
- **自动生成 `manifest.json`**：记录每张图对应的**画师名 + Pixiv 原图链接**（图片类会有，动作 GIF 类可能为空）
- 商用/公开使用时，务必读 manifest 保留画师署名 🎨

**⚠️ 批量下载的两个已踩坑**：
- **单次 `--amount` 建议 ≤ 20 张**：GIF 类单文件常 500KB+，串行下载 30 张容易撞 60s 命令超时被中断（实测 30 张只跑完 22 张）。需要更大批量就分多次，或者主动把 terminal timeout 拉到 180s+。
- **中断会导致 `manifest.json` 不生成**：CLI 是"全部下完才写 manifest"的逻辑，任何超时/异常中断都会丢清单。分批下 + 每批下完立刻检查 `ls outdir/manifest.json` 是否存在。

**manifest.json 示例**：
```json
[
  {
    "file": "/home/ubuntu/media-cache/waifu/xxx.png",
    "artist": "freng",
    "source": "https://www.pixiv.net/en/artworks/96072338",
    "anime": null
  }
]
```

**做「今日番剧推荐」内容**：
```bash
media-cli anime "$(date +%Y) fall" --limit 5
```

**做客户礼物：动漫台词卡（配合其他技能）**：
1. `media-cli anime "名侦探柯南" --limit 1` 拿到简介和封面
2. 用 `frontend-design` 技能出一张卡片

## 陷阱与技巧

1. **商用/客户场景**：优先用 `neko`/`waifu` 的 SFW 图，或者动作 GIF 类（更安全）。
2. **画师署名**：如果把图发布出去，**务必保留 `source_url` 或注明 Pixiv 画师**，尊重原创。
3. **Jikan 中文查询**：Jikan 后端是 MyAnimeList，中文查询命中率一般，用英文/日文/罗马音更稳。例：查「进击的巨人」用 `attack on titan` 或 `shingeki no kyojin`。
4. **图片下载**：URL 可以直接 `curl -O` 下载，或用 kaka 内置的 `image-upload-to-shareable-url` 技能转存。
5. **🚨🚨 IM/微信发图硬规则：外链图必须下本地后发送，绝对不许"跳过不发"**
   - 微信端 `MEDIA:<https://...>` 外链 **不会预览渲染**（只显示链接文字，等于没发）
   - **❌ 严禁**："外链发不出来，那我就不发了"——这是主人明确纠正过的错误行为
   - **✅ 必做**：任何要给主人展示的图（AniList 封面 / NekosBest / 任意 URL），一律先 `curl -sS --max-time 20 -o /tmp/带前缀_序号.jpg "$URL"` 下本地，再用 `MEDIA:/tmp/xxx.jpg` 发送
   - 下载失败要**告诉主人失败原因**并给出 URL，让主人自己点，不能静默丢弃

6. **⚠️ 绝对不要"发完立即 rm"（竞态陷阱）**：微信 MEDIA 发送是**异步**的——响应里写 `MEDIA:/tmp/xxx.jpg` 后，gateway 才会读文件上传。如果在同轮或紧接着 `rm`，会出现**文件已删除、图片还没发出去** 的竞态，主人收到空消息或路径错误。正确做法：
   - 文件名带**时间戳** + 有辨识度前缀：`/tmp/anime_$(date +%s)_N.jpg` 或 `/tmp/geass_r1.jpg` 这种带作品名的
   - **不主动 rm**，交给 `/tmp` 系统清理机制（tmpreaper / reboot 自动清）
   - 如果确实想清理旧文件，只清理**上一轮及更早**产生的（可以用 `find /tmp -name 'anime_*' -mmin +10 -delete`），永远不删本轮刚生成的

## 与其他技能的组合

- **配文案** → `xiaohongshu-copywriter`（小红书） 或 `xinchuan-kaoyan-wechat-article`（长图文）
- **配图片** → 结合 `minimax-image-generation` 生成原创图
- **图床上传** → `image-upload-to-shareable-url`

## CLI 位置

`/home/ubuntu/.local/bin/media-cli`（与 `music-metadata` 技能共享同一 CLI）

## 🆘 Jikan 504 时的 AniList GraphQL 兜底（实测可用）

**触发场景**：`media-cli anime "xxx"` 连续返回 `❌ HTTP 504: Gateway Time-out`，或直接 curl Jikan 得到 `MyAnimeList may be down/unavailable`。Jikan 是 MAL 的非官方镜像，MAL 侧一挂 Jikan 全挂，重试无意义，直接切换数据源。

**用 AniList GraphQL 替代**（免 key、境内直连、字段更全）：

```bash
# 查单部作品（把 SEARCH 换成作品名，中/英/日/罗马音都行）
curl -sS --max-time 20 -X POST https://graphql.anilist.co \
  -H "Content-Type: application/json" \
  -d '{"query":"query{Media(search:\"SEARCH\",type:ANIME){id title{romaji english native}format episodes duration status startDate{year month day}endDate{year month day}season seasonYear averageScore meanScore popularity favourites source studios{nodes{name}}genres tags{name rank}coverImage{extraLarge}siteUrl description(asHtml:false)}}"}'

# 查系列（含续作/剧场版，返回多条按人气排序）
curl -sS --max-time 20 -X POST https://graphql.anilist.co \
  -H "Content-Type: application/json" \
  -d '{"query":"query{Page(perPage:5){media(search:\"SEARCH\",type:ANIME,sort:POPULARITY_DESC){id title{romaji english native}format episodes status startDate{year month day}averageScore popularity siteUrl}}}"}'
```

**AniList vs Jikan 字段对照**（AniList 甚至更详细）：
| 需求 | Jikan 字段 | AniList 字段 |
|---|---|---|
| 评分 | `score` (0-10) | `averageScore`/`meanScore` (0-100) |
| 分类 | `genres` + `themes` | `genres` + `tags[{name,rank}]` |
| 制作 | `studios` | `studios.nodes` |
| 简介 | `synopsis` | `description(asHtml:false)`（含 HTML 标签，需 `re.sub(r'<[^>]+>','',...)`) |
| 季度 | `season`/`year`（分开字段） | `season`+`seasonYear`（同层） |

**已踩坑**：AniList 的 `description` 字段带 `<br>` 等 HTML 标签，输出前必须去掉；日期是 `{year,month,day}` 三个 int 字段而不是字符串。

## ⚠️ neko-download 已知限制

- **单批 amount 建议 ≤ 20**：NekosBest 单张 GIF 可能几 MB，30 张串行下载容易撞 60s terminal 超时。要下大量素材请分批多次调用。
- **manifest.json 只在循环结束才写**（当前 CLI 实现），超时/中断后已下载的图会留下但清单丢失。需要抗中断请自己在下载后手动构造清单（从 API 响应里拿 `artist_name`/`source_url`/`anime_name`）。
- **NekosBest 图片外链在微信里不预览**：给主人发图必须 `curl -O` 下到本地临时目录再走 MEDIA: 引用。**不要发完立即 rm**（异步竞态见"陷阱与技巧 §6"），用带时间戳/作品名的路径让文件自然过期即可。

## 故障排查

```bash
# Jikan 测活（504 就走上方 AniList 兜底，不要死循环重试）
curl -s "https://api.jikan.moe/v4/anime?q=naruto&limit=1" | jq -r .data[0].title

# AniList 测活
curl -sS -X POST https://graphql.anilist.co -H "Content-Type: application/json" \
  -d '{"query":"{Media(search:\"naruto\",type:ANIME){title{romaji}}}"}' | jq -r '.data.Media.title.romaji'

# NekosBest 测活
curl -s "https://nekos.best/api/v2/neko?amount=1" | jq -r '.results[0].url'

# 分类清单
curl -s "https://nekos.best/api/v2/endpoints" | jq 'keys'
```

### Jikan 持续 504 时的备用数据源：AniList GraphQL

**触发条件**：Jikan 返回 `HTTP 504 / BadResponseException / "Jikan failed to connect to MyAnimeList"` **且重试 2+ 次仍失败**——说明是上游 MAL 挂了，不是 Jikan 抖动，重试无用。此时切 AniList。

**AniList 特点**：无需 API key、境内直连稳定、字段比 Jikan 更全（含 tags 权重、季度、favourites、AniList 站内页 URL）。缺点：中文标题命中率与 Jikan 相当，仍建议英/日/罗马音查询。

```bash
# 用 romaji / english 关键词查询（例：Guilty Crown）
Q="Guilty Crown"
curl -sS --max-time 20 -X POST https://graphql.anilist.co \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"query{Media(search:\\\"$Q\\\",type:ANIME){id title{romaji english native}format episodes duration status startDate{year month day}endDate{year month day}season seasonYear averageScore meanScore popularity favourites source studios{nodes{name}}genres tags{name rank}coverImage{extraLarge}siteUrl description(asHtml:false)}}\"}" \
  | python3 -c "
import sys, json, re
r = json.load(sys.stdin)['data']['Media']
def d(x): return f\"{x['year']}-{x['month']:02d}-{x['day']:02d}\" if x and x.get('year') else '未知'
print('标题:', r['title']['romaji'], '/', r['title']['english'], '/', r['title']['native'])
print('类型:', r['format'], '集数:', r['episodes'], '状态:', r['status'])
print('放送:', d(r['startDate']),'→',d(r['endDate']), f\"({r['season']} {r['seasonYear']})\")
print('评分:', r['averageScore'],'/100  人气:', r['popularity'])
print('制作:', ', '.join(s['name'] for s in r['studios']['nodes']))
print('类型:', ', '.join(r['genres']))
print('高频tag:', ', '.join(t['name'] for t in sorted(r['tags'],key=lambda x:-x['rank'])[:8]))
print('封面:', r['coverImage']['extraLarge'])
print('URL:', r['siteUrl'])
print('简介:', re.sub(r'<[^>]+>','',r['description']).strip())
"
```

**说到 Jikan 恢复后**：优先切回 `media-cli anime`，AniList 只作应急兜底。判断 Jikan 是否恢复只需 `curl -sS -w "%{http_code}\n" -o /dev/null "https://api.jikan.moe/v4/anime?q=naruto&limit=1"` 看到 200 即可。
