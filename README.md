[Uploading README.md…]()
# 微商城API - 部署说明

## 方式一：Docker部署（推荐，服务器上一条命令）

```bash
# 1. 把整个 microshop-api 文件夹上传到服务器
scp -r microshop-api root@你的服务器IP:/opt/

# 2. 服务器上启动
cd /opt/microshop-api
docker compose up -d --build

# 3. 访问
http://服务器IP:8012          首页
http://服务器IP:8012/docs     接口文档（给面试官看这个）
```

## 方式二：直接运行（不用Docker）

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动
uvicorn main:app --host 0.0.0.0 --port 8012

# 3. 后台运行（关掉ssh也不停）
nohup uvicorn main:app --host 0.0.0.0 --port 8012 > app.log 2>&1 &
```

## 端口占用说明

如果你的服务器8012端口被占用，改成其他端口：
```bash
docker compose 改 ports: "8001:8012"
# 或
uvicorn main:app --host 0.0.0.0 --port 8001
```

## 接口测试流程（面试官在线演示）

1. 打开 `/docs`
2. 找到 `POST /api/register` → Try it out → 填用户名密码 → Execute
3. 复制返回的 `access_token`
4. 点页面右上角 **Authorize** → 粘贴token
5. 调试商品列表、创建订单、支付回调接口

## 核心接口

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | /api/register | 注册（返回token） |
| POST | /api/login | 登录 |
| GET | /api/products | 商品列表（支持category/keyword筛选） |
| GET | /api/products/{id} | 商品详情 |
| POST | /api/orders | 创建订单（需登录） |
| GET | /api/orders | 我的订单 |
| POST | /api/payment/callback | 支付回调（已做幂等处理） |
| GET | /health | 健康检查 |

## 简历上怎么写链接

```
微商城自动化测试项目  http://服务器IP:8012/docs
```

或者用Nginx反代到域名/子路径。
