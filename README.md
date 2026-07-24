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
4. 在腾讯云防火墙放行 80 和 443 端口。
5. 域名解析到服务器公网 IP；正式使用建议再配置 HTTPS 证书。

SQLite 数据通过 `./data:/app/data` 持久化，升级容器不会丢失产品资料。上线前请备份 `data/maya_calendar.db`。

## 替换真实产品素材

当前图腾与手链为 CSS 视觉占位，避免在 Demo 阶段绑定未确认版权的玛雅文字图片。你可以先在后台填写每款产品图地址；下一阶段建议整理 20 个已获授权的透明 PNG/SVG 日符图，再把 `icon_text` 升级为正式图形素材。

## 测试

```powershell
python -m unittest discover -s tests -v
```
