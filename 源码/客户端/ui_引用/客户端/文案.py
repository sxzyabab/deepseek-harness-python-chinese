"""统一 `@` 引用源的 `reference` 命名空间词典。

对齐上游 `ui-reference/src/client/locales.ts`。公开面仅中文名。
"""
__all__=['命名空间','中文','英文','NS','zh','en']#仅中文公开名

命名空间='reference'#locale 命名空间
NS=命名空间#上游名

中文={#简体中文词条（键集合真源）
    'section.files':'文件与文件夹',#文件分组标题
    'section.sessions':'对话',#会话分组标题
    'candidate.noCwd':'（无工作目录）',#无 cwd 占位
    'crumb.root':'工作区',#面包屑根
    'time.now':'刚刚',#相对时间：此刻
    'time.minutes':'{n}分钟',#相对时间：分钟
    'time.hours':'{n}小时',#相对时间：小时
    'time.days':'{n}天',#相对时间：天
    'time.months':'{n}个月',#相对时间：月
    'time.years':'{n}年',#相对时间：年
}#中文结束

英文={#英文文案，按中文键集合校验
    'section.files':'Files & folders',#文件分组标题
    'section.sessions':'Sessions',#会话分组标题
    'candidate.noCwd':'(no cwd)',#无 cwd 占位
    'crumb.root':'Workspace',#面包屑根
    'time.now':'now',#相对时间：此刻
    'time.minutes':'{n}min',#相对时间：分钟
    'time.hours':'{n}h',#相对时间：小时
    'time.days':'{n}d',#相对时间：天
    'time.months':'{n}mo',#相对时间：月
    'time.years':'{n}y',#相对时间：年
}#英文结束

zh=中文#上游名
en=英文#上游名
