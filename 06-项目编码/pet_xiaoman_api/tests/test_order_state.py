"""状态机测试：PRD §5.2.2 / §6.4 验收标准直接转用例。"""
import pytest

from app.services import order_state as osm
from app.services.order_state import TransitionContext, TransitionError, validate_transition


def ok(media=True, pay="未支付", owner=False):
    return TransitionContext(has_media=media, pay_type=pay, is_owner=owner)


def test_normal_path_to_in_service_requires_media():
    # AC：接宠中→服务中 需接宠完成影像
    validate_transition("接宠中", "服务中", ok(media=True))
    with pytest.raises(TransitionError, match="影像"):
        validate_transition("接宠中", "服务中", ok(media=False))


def test_wait_delivery_requires_media():
    validate_transition("服务中", "待交付", ok(media=True))
    with pytest.raises(TransitionError, match="影像"):
        validate_transition("服务中", "待交付", ok(media=False))


def test_complete_requires_settled_pay():
    # AC：未结清不可标记完成
    with pytest.raises(TransitionError, match="结清"):
        validate_transition("待交付", "已完成", ok(pay="未支付"))
    with pytest.raises(TransitionError, match="结清"):
        validate_transition("待交付", "已完成", ok(pay="定金已付"))
    validate_transition("待交付", "已完成", ok(pay="全款已付"))
    validate_transition("待交付", "已完成", ok(pay="到店付已结清"))


def test_illegal_jumps_rejected():
    for cur, tgt in [("待确认", "服务中"), ("已预约", "已完成"),
                     ("服务中", "已预约"), ("待交付", "接宠中")]:
        with pytest.raises(TransitionError, match="非法状态流转"):
            validate_transition(cur, tgt, ok())


def test_terminal_states_frozen():
    for tgt in ["已预约", "服务中", "已取消"]:
        with pytest.raises(TransitionError):
            validate_transition("已完成", tgt, ok())
        with pytest.raises(TransitionError):
            validate_transition("已取消", tgt, ok())


def test_in_service_cannot_cancel_directly():
    with pytest.raises(TransitionError):
        validate_transition("服务中", "已取消", ok())
