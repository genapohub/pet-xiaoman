"""订单状态机（PRD §6.4）。合法流转表是唯一真相；非法流转一律拒绝。

规则：
- 终态（已完成/已取消）不可流转
- 强制影像节点：接宠完成/告别仪式/火化完成——无影像不可流转（例外审批走店长权限，另行记录）
- 「已完成」前置校验：pay_type ∈ {全款已付, 到店付已结清}
- 回退仅店长可操作（路由层控制角色，本模块只管合法流转）
"""
from dataclasses import dataclass


class OrderStatus:
    PENDING_CONFIRM = "待确认"
    BOOKED = "已预约"
    PICKING = "接宠中"
    IN_SERVICE = "服务中"
    WAIT_DELIVERY = "待交付"
    COMPLETED = "已完成"
    CANCELLED = "已取消"


# PRD §6.4 合法流转表
TRANSITIONS: dict[str, list[str]] = {
    OrderStatus.PENDING_CONFIRM: [OrderStatus.BOOKED, OrderStatus.CANCELLED],
    OrderStatus.BOOKED: [OrderStatus.PICKING, OrderStatus.CANCELLED],
    OrderStatus.PICKING: [OrderStatus.IN_SERVICE, OrderStatus.CANCELLED],
    OrderStatus.IN_SERVICE: [OrderStatus.WAIT_DELIVERY],
    OrderStatus.WAIT_DELIVERY: [OrderStatus.COMPLETED],
    OrderStatus.COMPLETED: [],
    OrderStatus.CANCELLED: [],
}

# 强制影像节点：流转到目标状态前必须已有该节点影像
REQUIRED_MEDIA_TARGETS = {
    OrderStatus.IN_SERVICE,     # 接宠完成影像
    OrderStatus.WAIT_DELIVERY,  # 火化完成影像
}
# 注：告别仪式节点影像随「服务中→待交付」前在服务中阶段上传，归入火化完成前检查

# 「已完成」的合法支付状态
SETTLED_PAY_TYPES = {"全款已付", "到店付已结清"}


class TransitionError(Exception):
    """非法流转/前置条件不满足。"""


@dataclass
class TransitionContext:
    has_media: bool            # 目标节点影像是否 ≥1
    pay_type: str              # 当前支付状态
    is_owner: bool = False     # 店长权限（回退等扩展用）


def can_transition(current: str, target: str) -> bool:
    return target in TRANSITIONS.get(current, [])


def validate_transition(current: str, target: str, ctx: TransitionContext) -> None:
    """校验一次状态流转；不合法抛 TransitionError。"""
    if not can_transition(current, target):
        raise TransitionError(f"非法状态流转：{current} → {target}")

    if target in REQUIRED_MEDIA_TARGETS and not ctx.has_media:
        raise TransitionError(f"流转到「{target}」前需至少上传 1 张该节点影像")

    if target == OrderStatus.COMPLETED and ctx.pay_type not in SETTLED_PAY_TYPES:
        raise TransitionError("订单未结清（需全款已付或到店付已结清）才能标记完成")

    if current == OrderStatus.IN_SERVICE and target == OrderStatus.CANCELLED:
        raise TransitionError("服务中订单不可直接取消（已发生服务），如需特殊情况由店长线下处理")
