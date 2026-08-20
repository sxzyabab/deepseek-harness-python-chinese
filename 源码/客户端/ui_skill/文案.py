"""`skill` 命名空间词典：专用工具行。

对齐上游 `ui-skill/src/client/locales.ts`。公开面仅中文名；词典键与英文字面量保持上游。
"""

__all__=['命名空间','中文','英文']#仅中文公开名

命名空间='skill'#词典命名空间名
中文={#简体中文词条
    'row.running':'正在加载 skill',#加载中
    'row.failed':'skill 加载失败',#加载失败
    'row.stopped':'skill 加载已中止',#加载已中止
    'row.instructions':'说明',#说明
    'menu.userOnly':'仅用户',#仅用户菜单项
}#中文词典结束
英文={#英文词条
    'row.running':'Loading skill',#加载中
    'row.failed':'Skill load failed',#加载失败
    'row.stopped':'Skill load stopped',#加载已中止
    'row.instructions':'Instructions',#说明
    'menu.userOnly':'user-only',#仅用户菜单项
}#英文词典结束
