"""Pydantic请求/响应模型"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

# ===== 用户 =====
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, description="用户名3-20位")
    password: str = Field(..., min_length=6, max_length=30, description="密码6-30位")
    phone: Optional[str] = Field(None, pattern=r"^1[3-9]\d{9}$")

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    phone: Optional[str]
    created_at: datetime
    class Config: from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# ===== 商品 =====
class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    stock: int
    image: Optional[str]
    category: Optional[str]
    class Config: from_attributes = True

# ===== 订单项 =====
class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., ge=1, le=99)

class OrderItemResponse(BaseModel):
    product_id: int
    product_name: str
    price: float
    quantity: int
    class Config: from_attributes = True

# ===== 订单 =====
class OrderCreate(BaseModel):
    items: List[OrderItemCreate] = Field(..., min_length=1)

class OrderResponse(BaseModel):
    id: int
    order_no: str
    total_amount: float
    status: str
    created_at: datetime
    items: List[OrderItemResponse]
    class Config: from_attributes = True

# ===== 支付回调 =====
class PaymentCallback(BaseModel):
    order_no: str
    pay_status: str = Field(..., description="success/fail")
    transaction_id: Optional[str] = None

class PaymentResponse(BaseModel):
    code: int = 0
    message: str = "success"
    order_no: str
    status: str
