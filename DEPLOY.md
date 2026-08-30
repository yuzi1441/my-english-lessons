# 部署指南（VPS / 静态托管）

构建产物 `lessons/week/` 是**纯静态站点**，任意静态文件服务器都能托管。

## 本地预览

```bash
python3 -m http.server 8770 --directory lessons/week
# 打开 http://localhost:8770
```

## VPS 部署（nginx 示例）

1. 在服务器上构建，或本地构建后同步：

```bash
rsync -avz --delete lessons/week/ user@your-vps:/var/www/english/
```

2. nginx 站点配置：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /var/www/english;
    index index.html;

    # 365 天课程页 + 音频，缓存可以激进一些
    location / {
        try_files $uri $uri/ =404;
    }
    location ~* \.(mp3|json)$ {
        expires 7d;
        add_header Cache-Control "public";
    }
}
```

3. HTTPS 建议用 certbot：

```bash
sudo certbot --nginx -d your-domain.com
```

注意事项：

- 音频总量约 1GB / 2 万+ 文件，rsync 首次同步较慢，之后增量很快。
- `lessons/` 已被 gitignore，部署请直接同步文件而不是 git pull。
- 重新学习内容后重跑 `python3 scripts/build_course.py --course speaking-vocab`，再 rsync 即可（音频增量跳过）。

## 云端生词本同步（可选）

- `lessons/week/_worker.js` 仅在 **Cloudflare Pages** 上生效：提供账号注册/登录和生词本云同步（D1 数据库）。`wrangler.toml` 已配置好数据库绑定，`wrangler pages deploy lessons/week` 即可。
- 部署到普通 VPS 时 `_worker.js` 不会被加载，站点自动进入**纯本地模式**：学习进度与生词本保存在浏览器 localStorage。换设备时无法云同步，属预期行为。

## 多课程

在 `examples/courses/<新课程id>/` 放入 `course.json` 与内容文件后重跑构建，课程目录页会自动列出所有课程。学习进度按课程隔离（localStorage 键前缀 `ir:<course>:`）。
