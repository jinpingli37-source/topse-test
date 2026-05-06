def wait_network_idle(page, timeout=30000):
    """等待页面网络请求完成"""
    page.wait_for_load_state("networkidle", timeout=timeout)


def short_wait(page, ms=1000):
    """短暂等待，仅在动画/过渡必须时使用"""
    page.wait_for_timeout(ms)
