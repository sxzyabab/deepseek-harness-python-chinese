"""Web UI 复制控件共用的宿主剪贴板写入。

对齐上游 `ui-primitives/src/clipboard.ts`。公开面仅中文名。
成功反馈留在各控件；本助手只报告宿主是否接受了一次写入。
浏览器环境优先 Clipboard API；无 DOM 时返回 False。
"""

__all__=['写剪贴板']#仅中文公开名

def 写剪贴板(文本):#写入宿主剪贴板
    """仅当宿主接受写入时为 True。"""
    try:#探测浏览器全局
        导航=globals().get('navigator')#navigator
        文档=globals().get('document')#document
    except Exception:#无
        导航=None#无
        文档=None#无
    if 导航 is not None:#有 navigator
        剪贴=getattr(导航,'clipboard',None)#clipboard
        写入=getattr(剪贴,'writeText',None) if 剪贴 is not None else None#writeText
        if 写入 is not None:#有异步 API
            try:#尝试
                结果=写入(文本)#写入
                if hasattr(结果,'等待'):#承诺
                    结果.等待()#等
                return True#接受
            except Exception:#权限拒绝
                return False#失败
    if 文档 is None:#无从回退
        return False#失败
    执行=getattr(文档,'execCommand',None)#execCommand
    if not callable(执行):#没有
        return False#失败
    try:#造文本框选中复制
        体=getattr(文档,'body',None)#body
        创建=getattr(文档,'createElement',None)#createElement
        if 体 is None or 创建 is None:#缺 DOM
            return False#失败
        框=创建('textarea')#文本框
        框.value=文本#填入
        框.setAttribute('readonly','')#只读
        样式=getattr(框,'style',None)#样式
        if 样式 is not None:#有
            样式.position='fixed'#移出流
            样式.left='-9999px'#藏起
        体.appendChild(框)#插入
        框.select()#选中
        try:#copy
            return bool(执行('copy'))#布尔结果
        finally:#拆掉
            框.remove()#移除
    except Exception:#回退失败
        return False#失败
