# 网站登记表

所有已部署网站的汇总。修改网站时先查这里，再点飞书档案链接获取详细配置。

| 项目名 | 类型 | 前端地址 | 后端地址 | GitHub仓库 | 本地路径 | 端口 | 飞书档案 | 创建时间 |
|--------|------|---------|---------|-----------|---------|------|---------|---------|
| AI小说写作助手 | 前后端分离 | https://novel.superkali.online | https://api.superkali.online/api | {{GITHUB_USERNAME}}/AI-Novel-Writing-Assistant | /root/AI-Novel-Writing-Assistant | 3000(后端), 5173(前端预览) | https://{{FEISHU_DOMAIN}}.feishu.cn/docx/FFRKdEQk2oED18xhL1dcOwSmnjf | 2026-06-30 |
| kali-portfolio | 纯静态 | https://kali.superkali.online | — | {{GITHUB_USERNAME}}/kali-portfolio | — | — | https://{{FEISHU_DOMAIN}}.feishu.cn/docx/EblSdYC1Xoe0pKxrX13c6gFnn8S | 2026-06-30 |
| lumina-cms | 前后端分离 | https://lumina-cms.superkali.online | https://lumina-cms-api.superkali.online/api | {{GITHUB_USERNAME}}/lumina-cms | /opt/lumina-cms | 8787 | https://{{FEISHU_DOMAIN}}.feishu.cn/docx/E5hjdvsmaoG0QJxDYblca1lznwb | 2026-07-01 |
| tiaotiao-site | 纯静态 | https://tiaotiao.superkali.online | — | {{GITHUB_USERNAME}}/tiaotiao-site | /home/ubuntu/kaka-tmp/tiaotiao-site | — | https://{{FEISHU_DOMAIN}}.feishu.cn/docx/MJt7d9Gh6o3euoxEGjgcoLmqnCd | 2026-07-02 |
| yingdao-agent | 纯前端+CF Functions | https://yingdao-agent.superkali.online | — | {{GITHUB_USERNAME}}/yingdao-agent | /home/ubuntu/kaka-tmp/yingdao-agent | — | https://{{FEISHU_DOMAIN}}.feishu.cn/docx/R2oPdBehIoZqYsxdxTOck3l0nNf | 2026-07-02 |

## Tunnel 配置

| Tunnel名 | ID | 配置文件 | Ingress规则 | 进程管理 |
|----------|----|---------|------------|---------|
| ai-novel | 98c490a8-44a1-429c-b653-fba25fe5ba2e | /etc/cloudflared/config.yml | novel.superkali.online→:5173, api.superkali.online→:3000 | systemd (cloudflared.service, enabled) |
| lumina-cms | 8d35f9bc-1d37-45e9-8c3f-a797a6f51e71 | /home/ubuntu/.cloudflared/lumina-cms.yml | lumina-cms-api.superkali.online→:8787 | systemd (cloudflared-lumina-cms.service, enabled) |
