"""通用 Streamlit UI 组件"""
import streamlit as st


def result_card(title: str, icon: str = ""):
    """开始一个结果卡片（用 st.container 模拟）"""
    header = f"{icon} {title}" if icon else title
    st.markdown(f"---")
    st.markdown(f"### {header}")
    return st.container()


def result_value(label: str, value: str, unit: str = ""):
    """显示一个大号的结果值"""
    text = f"{value} {unit}".strip()
    st.metric(label=label, value=text)


def result_grid(items: list[dict]):
    """多列结果展示，items = [{'label': str, 'value': str, 'unit': str}]"""
    if not items:
        return
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        with col:
            st.metric(
                label=item.get('label', ''),
                value=f"{item.get('value', '')} {item.get('unit', '')}".strip()
            )


def steps_card(steps: list[dict]):
    """展示计算步骤
    steps = [{'label': str, 'detail': str}]
    """
    with st.expander("📝 计算步骤", expanded=False):
        for i, step in enumerate(steps, 1):
            st.markdown(f"**{i}. {step['label']}**")
            st.markdown(step['detail'])
            if i < len(steps):
                st.markdown("")


def alert(message: str, type: str = "info"):
    """显示提示信息"""
    icon_map = {
        "error": "⚠️",
        "warning": "⚠️",
        "success": "✅",
        "info": "💡",
    }
    icon = icon_map.get(type, "💡")
    if type == "error":
        st.error(f"{icon} {message}")
    elif type == "warning":
        st.warning(f"{icon} {message}")
    elif type == "success":
        st.success(f"{icon} {message}")
    else:
        st.info(f"{icon} {message}")
