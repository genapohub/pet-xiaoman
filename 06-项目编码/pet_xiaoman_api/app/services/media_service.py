"""影像服务（PRD §5.2.2）：本地存储落盘 + 元数据落库；云托管上线后切 COS（接口不变）。

强制影像节点的服务端校验入口：has_node_media()——流转校验以此为准，不信任前端 has_media 参数。
"""
import shutil
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.service_media import MediaNode, MediaType, ServiceMedia

UPLOAD_ROOT = Path("uploads")
MAX_PHOTO_BYTES = 10 * 1024 * 1024
MAX_VIDEO_BYTES = 50 * 1024 * 1024
ALLOWED_PHOTO = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_VIDEO = {".mp4"}  # H.264；iOS HEVC 由小程序端 compressVideo 预处理

# 流转目标 → 必须已有影像的节点（对齐 order_state.REQUIRED_MEDIA_TARGETS）
TARGET_NODE_REQUIREMENT = {
    "服务中": MediaNode.PICKUP,      # 接宠完成影像
    "待交付": MediaNode.CREMATION,   # 火化完成影像
}


def has_node_media(db: Session, order_id: int, node: MediaNode) -> bool:
    return (db.query(ServiceMedia)
            .filter(ServiceMedia.order_id == order_id,
                    ServiceMedia.node == node,
                    ServiceMedia.revoked.is_(False))
            .count() > 0)


def node_media_satisfied(db: Session, order_id: int, target_status: str) -> bool:
    """流转到 target_status 的影像前置是否满足（无要求则 True）。"""
    node = TARGET_NODE_REQUIREMENT.get(target_status)
    return node is None or has_node_media(db, order_id, node)


def save_media(db: Session, order: Order, node: str, filename: str,
               content: bytes, uploaded_by: int) -> ServiceMedia:
    """上传落盘 + 落库。校验：节点合法 / 大小限制 / 扩展名白名单。"""
    node_enum = MediaNode(node)
    ext = Path(filename).suffix.lower()
    if ext in ALLOWED_VIDEO:
        media_type, limit = MediaType.VIDEO, MAX_VIDEO_BYTES
    elif ext in ALLOWED_PHOTO:
        media_type, limit = MediaType.PHOTO, MAX_PHOTO_BYTES
    else:
        raise ValueError(f"不支持的文件格式 {ext}（视频需 H.264 mp4，照片 jpg/png/webp）")
    if len(content) > limit:
        raise ValueError(f"文件超过大小限制（{limit // 1024 // 1024}MB）")

    dest_dir = UPLOAD_ROOT / order.order_no
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{uuid.uuid4().hex}{ext}"
    dest.write_bytes(content)

    media = ServiceMedia(order_id=order.id, node=node_enum, media_type=media_type,
                         url=f"/uploads/{order.order_no}/{dest.name}",
                         uploaded_by=uploaded_by, store_id=order.store_id)
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


def revoke_media(db: Session, media_id: int, is_owner: bool, reason: str) -> ServiceMedia:
    """撤回（PRD：仅店长，强制原因，留审计日志）。"""
    if not is_owner:
        raise PermissionError("仅店长可撤回影像")
    media = db.get(ServiceMedia, media_id)
    if not media:
        raise ValueError("影像不存在")
    media.revoked = True
    # 审计日志：TODO 接入统一审计表时迁移（当前以 reason 落应用日志代替）
    import logging
    logging.getLogger(__name__).warning("影像撤回 media_id=%s reason=%s", media_id, reason)
    db.commit()
    db.refresh(media)
    return media


def list_order_media(db: Session, order: Order) -> list[dict]:
    """客户侧/详情页影像列表（不含已撤回）。"""
    rows = (db.query(ServiceMedia)
            .filter(ServiceMedia.order_id == order.id, ServiceMedia.revoked.is_(False))
            .order_by(ServiceMedia.created_at)
            .all())
    return [{"id": m.id, "node": m.node.value, "media_type": m.media_type.value,
             "url": m.url} for m in rows]
