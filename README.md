# 生日图腾 H5 Demo

这是一个可直接运行的全栈 Demo：访客输入公历生日后，系统按照 GMT 584283 口径换算，并从 20 款文创产品中返回唯一的一款。页面包含生日输入、计算过渡、唯一结果、产品详情、分享卡、完整历法、20款图鉴和文化说明，并提供简单产品后台。

本版本已迁入 `NFC-抽签/coding/生日图腾H5`，并接入项目内
`图片资产/日期神数字资产` 的20套正式日期守护神PNG。

- `static/img/date-gods/full`：结果主图、产品详情、分享卡使用的完整图。
- `static/img/date-gods/icon`：首页转盘、浮动背景、图鉴使用的压缩图。
- 页面通过产品的 `sign_key` 自动选择同名图片，后续替换图片不需要修改计算逻辑。

## 本地体验

Windows：

```powershell
python -m pip install -r requirements.txt
python app.py
```

浏览器访问 `http://127.0.0.1:8000/`。产品后台为 `http://127.0.0.1:8000/admin`，Demo 默认令牌为 `demo-admin`。

## 数据与隐私

- 20款产品资料保存在 `data/maya_calendar.db`（SQLite）。
- 默认不会记录访客的完整生日；匿名计算量统计也默认关闭。
- 后台可修改寓意、故事、材质、价格、库存与产品图地址。
- 正式上线前必须通过 `MAYA_ADMIN_TOKEN` 修改默认管理令牌。

## 腾讯云轻量应用服务器部署

建议使用 Ubuntu 22.04/24.04，并安装 Docker 与 Docker Compose：

1. 将整个项目上传到服务器，例如 `/opt/birthday-totem`。
2. 在项目目录创建 `.env`：

   ```env
   MAYA_ADMIN_TOKEN=换成一段足够长的随机字符串
   MAYA_ENABLE_ANALYTICS=0
   ```

3. 启动：`docker compose up -d --build`
4. 容器只监听本机的 `127.0.0.1:8000`；在服务器现有 Nginx 中配置 HTTPS 与反向代理。
5. 域名解析到服务器公网 IP；正式使用建议再配置 HTTPS 证书。

SQLite 数据通过 `./data:/app/data` 持久化，升级容器不会丢失产品资料。上线前请备份 `data/maya_calendar.db`。

### 部署到 `/maya20dategods/` 子路径

应用通过 Nginx 的 `X-Forwarded-Prefix` 自动识别部署前缀。因此，Nginx 必须将子路径从上游请求中移除，并传入该请求头；不要在 Flask 路由中重复添加 `/maya20dategods`。以下配置可加入 `kyun-exhibition.com` 的 HTTPS `server` 块：

```nginx
location = /maya20dategods {
    return 301 /maya20dategods/;
}

location /maya20dategods/ {
    # 尾部斜杠会将 /maya20dategods/ 从转发给 Flask 的 URI 中移除。
    proxy_pass http://127.0.0.1:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header X-Forwarded-Prefix /maya20dategods;
}
```

完成 Nginx 配置后，访问 `https://kyun-exhibition.com/maya20dategods/`。本地开发不设置该请求头，仍可直接使用 `http://127.0.0.1:8000/`。

## 替换真实产品素材

当前图腾与手链为 CSS 视觉占位，避免在 Demo 阶段绑定未确认版权的玛雅文字图片。你可以先在后台填写每款产品图地址；下一阶段建议整理 20 个已获授权的透明 PNG/SVG 日符图，再把 `icon_text` 升级为正式图形素材。

## 测试

```powershell
python -m unittest discover -s tests -v
```
