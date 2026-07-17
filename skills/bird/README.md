# bird - X/Twitter CLI Skill for OpenClaw

从 OpenClaw 2026.2.6 版本提取的 bird 技能，用于通过命令行操作 Twitter/X。

## 功能

- 读取推文
- 搜索
- 点赞/收藏
- 转发
- 发布推文
- 查看时间线
- 查看列表

## 安装

### 1. 安装 bird CLI

```bash
npm install -g @steipete/bird
```

### 2. 配置认证

在 `~/.openclaw/openclaw.json` 中添加：

```json
{
  "skills": {
    "entries": {
      "bird": {
        "enabled": true,
        "env": {
          "AUTH_TOKEN": "你的auth_token",
          "CT0": "你的ct0"
        }
      }
    }
  }
}
```

获取 AUTH_TOKEN 和 CT0：
1. 登录 twitter.com
2. 打开开发者工具 → Application → Cookies → twitter.com
3. 找到 `auth_token` 和 `ct0` 的值

### 3. 配置代理（如需要）

```bash
# 在 /etc/environment 中添加
export HTTP_PROXY="http://你的代理地址"
export HTTPS_PROXY="http://你的代理地址"
```

## 使用

```bash
# 查看当前用户
bird whoami

# 读取推文
bird read <tweet_id>

# 搜索
bird search "关键词"

# 查看时间线
bird home

# 发布推文
bird tweet "内容"
```

## 环境变量

| 变量 | 说明 |
|------|------|
| AUTH_TOKEN | Twitter auth_token cookie |
| CT0 | Twitter ct0 cookie |
| HTTP_PROXY | HTTP 代理 |
| HTTPS_PROXY | HTTPS 代理 |

## 注意事项

- 该 npm 包已被弃用，但仍然可用
- 配置文件目前仅支持浏览器相关选项，认证信息需通过环境变量传递
- 发推可能有频率限制

## 版本历史

- 提取自 OpenClaw 2026.2.6
