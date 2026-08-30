"""访问模式芯片：只读 / 工作区写 / Full access。

对齐上游 `ui-conversation/src/client/skeleton/PermissionSelect.tsx`。公开面仅中文名。
"""
import re#kebab 检测

__all__=['权限选择','显示名','选项标签','完全访问','权限字形键']#仅中文公开名

完全访问='danger-full-access'#Full access 机器名
短横名=re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')#kebab
权限字形键=('read-only','workspace-write',完全访问)#设计集

def 取字段(对象,键,缺省=None):#读字段
    """映射或对象。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 显示名(名):#kebab → Title Case
    """非 kebab 原样；Full access 产品标签另走。"""
    if not 短横名.match(名):#非 kebab
        return 名#原样
    return ' '.join(段[:1].upper()+段[1:] for 段 in 名.split('-'))#Title

def 选项标签(选项):#菜单/触发标签
    """Full access 固定产品名。"""
    if 取字段(选项,'value')==完全访问:#满权
        return 'Full access'#产品
    return 显示名(取字段(选项,'name') or '')#名

class 权限选择:#访问模式芯片
    """无投影不渲染；Full access 需确认。"""

    def __init__(自身,属性=None):#记下
        """记下 props 与本地态。"""
        自身.属性=属性 or {}#合成
        自身.挑选=None#乐观值
        自身.已开=False#菜单
        自身.确认中=None#待确认 id
        自身.已知情=False#确认勾选

    def 更新(自身,属性):#刷新
        """锁定或无值时关菜单。"""
        自身.属性=属性 or {}#新
        if 取字段(自身.属性,'locked') or 取字段(自身.属性,'value') is None:#锁或无
            自身.已开=False#关
            自身.已知情=False#清
            自身.确认中=None#清

    def 切换菜单(自身):#开合
        """翻转菜单。"""
        自身.已开=not 自身.已开#翻

    def 提交(自身,标识):#斜杠命令
        """/permission <id>。"""
        命令=取字段(自身.属性,'command')#命令
        自身.挑选=标识#乐观
        if callable(命令):#有
            try:#投递
                命令(f'/permission {标识}')#提交
            finally:#清乐观
                自身.挑选=None#清
        else:#无
            自身.挑选=None#清

    def 选择(自身,标识):#菜单选中
        """同值忽略；满权走确认。"""
        自身.已开=False#关菜单
        值=取字段(自身.属性,'value')#投影
        if 值 is None:#无
            return#无事
        if 标识==取字段(值,'currentValue'):#同
            return#无事
        if 标识==完全访问:#满权
            自身.已知情=False#清勾
            自身.确认中=标识#待确认
            return#等确认
        自身.提交(标识)#直接提交

    def 关确认(自身):#关确认框
        """清态。"""
        自身.已知情=False#清
        自身.确认中=None#清

    def 确认满权(自身):#启用 Full access
        """需知情勾选。"""
        if 取字段(自身.属性,'locked') or not 自身.已知情 or 自身.确认中 is None:#不可
            return#无事
        标识=自身.确认中#id
        自身.关确认()#关
        自身.提交(标识)#提交

    def 渲染(自身):#结构
        """无投影返回 None。"""
        属性=自身.属性#props
        值=取字段(属性,'value')#投影
        翻译=取字段(属性,'t',lambda 键,**_:键)#文案
        锁定=取字段(属性,'locked',False)#锁
        if 值 is None:#无能力
            return None#空
        当前值=自身.挑选 if 自身.挑选 is not None else 取字段(值,'currentValue')#当前
        选项们=取字段(值,'options') or []#选项
        当前=None#当前选项
        for 项 in 选项们:#找
            if 取字段(项,'value')==当前值:#命中
                当前=项#记下
                break#停
        忙=自身.挑选 is not None or 自身.确认中 is not None#忙
        条目=[]#菜单项
        for 项 in 选项们:#过滤 custom
            if 取字段(项,'value')=='custom':#跳
                continue#跳
            条目.append({#项
                'id':取字段(项,'value'),#id
                'label':选项标签(项),#标签
                'glyph':取字段(项,'value') if 取字段(项,'value') in 权限字形键 else None,#字形
            })#结束项
        触发名=选项标签(当前) if 当前 is not None else 显示名(当前值 or '')#触发文案
        return {#根
            'trigger':{#触发
                'label':触发名,#文案
                'aria':翻译('input.accessMode',{'name':触发名}),#aria
                'title':取字段(当前,'description'),#描述
                'glyph':当前值 if 当前值 in 权限字形键 else None,#字形
                'open':自身.已开,#开
                'disabled':锁定 or 忙,#禁用
                'onClick':自身.切换菜单,#切换
            },#结束触发
            'menu':{'open':自身.已开,'items':条目,'selectedId':当前值,'onSelect':自身.选择},#菜单
            'confirm':None if 自身.确认中 is None else {#确认
                'title':翻译('access.confirm.title'),#标题
                'description':翻译('access.confirm.description'),#描述
                'acknowledge':翻译('access.confirm.acknowledge'),#知情
                'cancel':翻译('access.confirm.cancel'),#取消
                'enable':翻译('access.confirm.enable'),#启用
                'acknowledged':自身.已知情,#勾
                'onAcknowledge':lambda 开:setattr(自身,'已知情',开),#勾选
                'onCancel':自身.关确认,#取消
                'onEnable':自身.确认满权,#启用
            },#结束确认
        }#结束根
