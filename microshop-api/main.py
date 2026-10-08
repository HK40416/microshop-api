"""
微商城API - 测试工程师项目演示
FastAPI + SQLAlchemy + JWT
接口文档：/docs  备用文档：/redoc
"""
import time
import uuid
from datetime import datetime
from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import engine, get_db, SessionLocal
import models, schemas, auth

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="微商城API",
    description="""
## 测试工程师项目演示 - 微商城接口系统
覆盖**用户认证、商品查询、订单创建、支付回调**核心链路。

### 测试说明
- 接口自动化：pytest + Requests
- 性能压测：JMeter（200并发）
- 响应校验：JSON Schema
- 缺陷管理：禅道/Jira

### 快速体验
1. 先 `/api/register` 注册账号
2. `/api/login` 登录获取 token
3. 点右上角 **Authorize** 输入 token
4. 调试商品、订单接口
    """,
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== 初始化测试数据 ==========
@app.on_event("startup")
def init_data():
    db = SessionLocal()
    if db.query(models.Product).count() == 0:
        products = [
            models.Product(name="无线蓝牙耳机", description="主动降噪，续航30小时，蓝牙5.3", price=299.0, stock=200, category="数码", image="🎧"),
            models.Product(name="机械键盘", description="青轴/RGB背光/104键/热插拔", price=359.0, stock=150, category="数码", image="⌨️"),
            models.Product(name="游戏鼠标", description="16000DPI/轻量化/无线双模", price=189.0, stock=300, category="数码", image="🖱️"),
            models.Product(name="27寸2K显示器", description="IPS/165Hz/HDR400/Type-C", price=1299.0, stock=80, category="数码", image="🖥️"),
            models.Product(name="保温杯", description="316不锈钢/500ml/24小时保温", price=79.0, stock=500, category="生活", image="🥤"),
            models.Product(name="双肩背包", description="防泼水/大容量/电脑隔层", price=159.0, stock=120, category="生活", image="🎒"),
            models.Product(name="USB-C数据线", description="100W快充/1.5米/编织线", price=29.9, stock=800, category="配件", image="🔌"),
            models.Product(name="移动电源", description="20000mAh/22.5W快充/可上飞机", price=129.0, stock=200, category="配件", image="🔋"),
        ]
        db.add_all(products)
        db.commit()
    db.close()

# ========== 1. 用户认证 ==========
@app.post("/api/register", response_model=schemas.Token, tags=["1.用户认证"], summary="用户注册")
def register(payload: schemas.UserRegister, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = models.User(
        username=payload.username,
        password_hash=auth.hash_password(payload.password),
        phone=payload.phone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = auth.create_token({"sub": str(user.id)})
    return schemas.Token(access_token=token, user=user)

@app.post("/api/login", response_model=schemas.Token, tags=["1.用户认证"], summary="用户登录")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = auth.create_token({"sub": str(user.id)})
    return schemas.Token(access_token=token, user=user)

@app.get("/api/me", response_model=schemas.UserResponse, tags=["1.用户认证"], summary="获取当前用户信息")
def me(user: models.User = Depends(auth.get_current_user)):
    return user

# ========== 2. 商品 ==========
@app.get("/api/products", response_model=List[schemas.ProductResponse], tags=["2.商品"], summary="商品列表")
def list_products(category: str = None, keyword: str = None, db: Session = Depends(get_db)):
    q = db.query(models.Product)
    if category:
        q = q.filter(models.Product.category == category)
    if keyword:
        q = q.filter(models.Product.name.like(f"%{keyword}%"))
    return q.all()

@app.get("/api/products/{product_id}", response_model=schemas.ProductResponse, tags=["2.商品"], summary="商品详情")
def product_detail(product_id: int, db: Session = Depends(get_db)):
    p = db.query(models.Product).get(product_id)
    if not p:
        raise HTTPException(status_code=404, detail="商品不存在")
    return p

# ========== 3. 订单 ==========
@app.post("/api/orders", response_model=schemas.OrderResponse, tags=["3.订单"], summary="创建订单")
def create_order(payload: schemas.OrderCreate,
                 user: models.User = Depends(auth.get_current_user),
                 db: Session = Depends(get_db)):
    order_no = datetime.now().strftime("%Y%m%d%H%M%S") + uuid.uuid4().hex[:6].upper()
    total = 0.0
    items = []
    for it in payload.items:
        product = db.query(models.Product).get(it.product_id)
        if not product:
            raise HTTPException(status_code=400, detail=f"商品{it.product_id}不存在")
        if product.stock < it.quantity:
            raise HTTPException(status_code=400, detail=f"商品[{product.name}]库存不足，剩余{product.stock}")
        total += product.price * it.quantity
        items.append(models.OrderItem(
            product_id=product.id,
            product_name=product.name,
            price=product.price,
            quantity=it.quantity,
        ))
        product.stock -= it.quantity
    order = models.Order(order_no=order_no, user_id=user.id, total_amount=round(total, 2), items=items)
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

@app.get("/api/orders", response_model=List[schemas.OrderResponse], tags=["3.订单"], summary="我的订单列表")
def my_orders(user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    return db.query(models.Order).filter(models.Order.user_id == user.id).order_by(desc(models.Order.created_at)).all()

@app.get("/api/orders/{order_no}", response_model=schemas.OrderResponse, tags=["3.订单"], summary="订单详情")
def order_detail(order_no: str, user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.order_no == order_no).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.user_id != user.id:
        raise HTTPException(status_code=403, detail="无权查看他人订单")
    return order

# ========== 4. 支付回调 ==========
@app.post("/api/payment/callback", response_model=schemas.PaymentResponse, tags=["4.支付"], summary="支付回调（需保证幂等）")
def payment_callback(payload: schemas.PaymentCallback, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.order_no == payload.order_no).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    # 幂等：已支付订单重复回调直接返回成功，不重复处理
    if order.status == "paid":
        return schemas.PaymentResponse(message="order already paid", order_no=order.order_no, status="paid")
    if payload.pay_status == "success":
        order.status = "paid"
        order.paid_at = datetime.utcnow()
        db.commit()
    else:
        order.status = "cancelled"
        db.commit()
    return schemas.PaymentResponse(order_no=order.order_no, status=order.status)

# ========== 健康检查 ==========
@app.get("/health", tags=["系统"], summary="健康检查")
def health():
    return {"status": "ok", "service": "microshop-api", "time": datetime.now().isoformat()}

# ========== 首页 ==========
@app.get("/", include_in_schema=False)
def index():
    return FileResponse("static/index.html")

app.mount("/static", StaticFiles(directory="static"), name="static")
