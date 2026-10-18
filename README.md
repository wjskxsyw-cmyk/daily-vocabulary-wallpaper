# Daily Vocabulary Wallpaper

每天自动生成英语＋塞语 iPhone 锁屏壁纸。每天按固定顺序轮换八种极简配色：暖象牙白、森林绿、勃艮第红、石墨灰、薰衣草紫、摩卡、灰玫瑰、石板蓝。顶部 40% 和底部 15% 留白给系统时钟、组件和锁屏按钮。配色从 2026-10-17 的暖象牙白开始，每八天循环；与现有 30 组词汇的循环独立。

## 初次部署

1. 把本 ZIP **解压后** 的所有内容上传到 GitHub 仓库根目录。注意 `.github/workflows/daily-wallpaper.yml` 的目录结构必须保留。
2. 仓库 Settings → Pages → Build and deployment → Source 选 **GitHub Actions**。
3. 仓库 Actions → `Daily bilingual wallpaper` → `Run workflow` → 运行一次。
4. 等待绿色成功标记后打开：
   - 页面：`https://wjskxsyw-cmyk.github.io/daily-vocabulary-wallpaper/`
   - 固定图片：`https://wjskxsyw-cmyk.github.io/daily-vocabulary-wallpaper/latest.png`
   - 日期信息：`https://wjskxsyw-cmyk.github.io/daily-vocabulary-wallpaper/latest.json`

## iPhone 快捷指令（锁屏自动更换）

在 iPhone「快捷指令」新建快捷指令：

1. **URL**：输入固定图片地址，并追加 `?day=` 和「当前日期」格式化为 `yyyy-MM-dd`，避免缓存旧图。也可直接用固定图片地址测试。
2. **获取 URL 内容**（Get Contents of URL）：GET。
3. **设定墙纸照片**（Set Wallpaper Photo）：图片使用上一步结果，目标选择锁定屏幕，关闭显示预览（如果系统提供此选项）。
4. 手动运行一次并授权。
5. 「自动化」→「特定时间」→ **每天 00:20** →「立即运行」→选择该快捷指令。

重要：GitHub Actions 定时可能延迟；00:20 不保证最新壁纸已发布。想确保不显示旧图，可先获取 `latest.json`，检查其中 `date` 是否等于手机当天日期，仅相同时才设置壁纸。不同 iOS 版本的快捷指令操作名称可能略有不同。

## 编辑词汇

修改 `data/words.json`，每条包括英语和塞语单词、释义和例句。词库目前 30 组，超过 30 天会循环，需要定期扩充。例句宜短，避免挤占安全区域。

## 运行时间

工作流分别在 UTC 22:05 和 23:05 触发，通过 `Europe/Belgrade` 当地小时判断，只在当地 00 点运行。手动触发随时运行。GitHub 定时任务可能延迟，极端情况下会跳过当天。

## 本地预览

```bash
pip install -r requirements.txt
python -m unittest
python generate.py 2026-10-17
```

Linux 环境需要安装 `fonts-noto-cjk` 和 `fonts-dejavu-core`。其他系统可通过 `FONT_LATIN`、`FONT_CJK` 环境变量指定本机字体路径。字体文件不包含在项目内。

## 费用及隐私

公开仓库与 GitHub Pages 的基础使用通常免费；图片及代码公开可见，不应加入私人资料。无需 AI API key。生成是词库驱动，并非每天由 ChatGPT 实时创作新词。
