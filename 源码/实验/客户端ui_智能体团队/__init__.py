"""浏览器发现的 Agent Teams UI 插件的纯宿主半边。

对齐上游 `client-ui-agent-team/src/index.ts`。公开面仅中文名。
"""
__all__=['应用']#仅中文公开名

def 应用():#空宿主 apply
    """宿主插件体；Team 行为在浏览器导出与宿主 RPC 域。"""
    return None#空

apply=应用#入口
