"""配置：环境变量优先，本地开发默认值。生产环境变量由微信云托管注入。"""
import os


class Settings:
    APP_NAME = "pet_xiaoman-api"
    ENV = os.getenv("ENV", "development")

    # 数据库（ADR-002：直接 MySQL，本地用 Docker MySQL 保持一致）
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "pet_xiaoman")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASS = os.getenv("DB_PASS", "")

    @classmethod
    def db_url(cls) -> str:
        # 生产环境：MySQL 缺配置直接抛错，禁止静默降级（宠宝树教训：环境不一致）
        if cls.ENV == "production":
            missing = [k for k, v in [("DB_HOST", cls.DB_HOST), ("DB_NAME", cls.DB_NAME),
                                      ("DB_USER", cls.DB_USER), ("DB_PASS", cls.DB_PASS)] if not v]
            if missing:
                raise RuntimeError(f"生产环境缺少数据库配置: {missing}（ADR-002：禁止降级 SQLite）")
            return (f"mysql+pymysql://{cls.DB_USER}:{cls.DB_PASS}"
                    f"@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}?charset=utf8mb4")
        # 开发：默认 Docker MySQL；SQLITE_FALLBACK=true 显式切换（跑测试/无 Docker 时）
        if os.getenv("SQLITE_FALLBACK", "false").lower() == "true":
            return "sqlite:///./pet_xiaoman-dev.sqlite"
        return (f"mysql+pymysql://{cls.DB_USER}:{cls.DB_PASS}"
                f"@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}?charset=utf8mb4")

    # 微信（商户号开通后填入；支付模块有功能开关，PRD §10.1）
    WX_APPID = os.getenv("WX_APPID", "")
    WX_MCH_ID = os.getenv("WX_MCH_ID", "")
    WX_PAY_KEY = os.getenv("WX_PAY_KEY", "")  # APIv3 密钥走密钥管理，禁止入库
    PAY_ENABLED = os.getenv("PAY_ENABLED", "false").lower() == "true"  # 支付功能开关

    # 微信登录（开关关闭时 C 端走轻量 customer_id 模式，存量接口不强制 token）
    WX_SECRET = os.getenv("WX_SECRET", "")
    WX_LOGIN_ENABLED = os.getenv("WX_LOGIN_ENABLED", "false").lower() == "true"
    TOKEN_SECRET = os.getenv("TOKEN_SECRET", "")


settings = Settings()
