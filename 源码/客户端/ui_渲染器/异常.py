__all__=['槽装配错误']#仅中文公开名

class 槽装配错误(Exception):
    '必须逃出组件错误边界的渲染器装配失败'
    pass#基类消息即可

class 槽组装错误(Exception):
    '缺少渲染器组装依赖。边界会再抛'
    pass#无额外字段
