"""pet_xiaoman-api 入口。"""
import logging

from fastapi import FastAPI

from app.config import settings
from pathlib import Path

from fastapi.staticfiles import StaticFiles

from app.routes import health, c_orders, b_orders, pay, service_items, products, boarding, customers, c_extra, stats, auth
from app.routes import b_auth, b_staff, b_rbac

app = FastAPI(title="pet_xiaoman API", version="0.1.0",
              description="宠物善终门店系统（单店版）。接口文档即知识地图接口协议来源。")

app.include_router(health.router)
app.include_router(c_orders.router, prefix="/api/c", tags=["c-订单"])
app.include_router(b_orders.router, prefix="/api/b", tags=["b-订单"])
app.include_router(pay.router, prefix="/api/pay", tags=["支付"])
app.include_router(service_items.router, prefix="/api/b", tags=["服务项目"])
app.include_router(products.router, tags=["纪念品"])  # 路由含全路径
app.include_router(boarding.router, tags=["寄存"])  # 路由含全路径
app.include_router(customers.router, prefix="/api/b", tags=["客户"])
app.include_router(c_extra.router, prefix="/api/c", tags=["C 端公开"])
app.include_router(stats.router, prefix="/api/b", tags=["数据看板"])
app.include_router(auth.router, prefix="/api/c", tags=["登录"])
app.include_router(b_auth.router, prefix="/api/b", tags=["b-登录"])
app.include_router(b_staff.router, prefix="/api/b/staff", tags=["b-成员"])
app.include_router(b_rbac.router, prefix="/api/b", tags=["b-角色权限"])

# 影像静态目录（本地存储版；云托管上线切 COS 后移除）
_UPLOAD_DIR = Path("uploads")
_UPLOAD_DIR.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(_UPLOAD_DIR)), name="uploads")


logger = logging.getLogger(__name__)


@app.on_event("startup")
def startup():
    logger.info("ENV=%s pay_enabled=%s", settings.ENV, settings.PAY_ENABLED)
