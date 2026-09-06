"""访问模式芯片：只读 / 工作区写 / Full access。

对齐上游 `ui-conversation/src/client/skeleton/PermissionSelect.tsx`。公开面仅中文名。
属性与选项为 dict。
"""
import re#kebab 检测

__all__=['权限选择','显示名','选项标签','完全访问','权限字形键']#仅中文公开名

完全访问='danger-full-access'#Full access 机器名
短横名=re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*\Z',re.ASCII)#kebab
权限字形键=('read-only','workspace-write',完全访问)#设计集

def 恒等翻译(键,参数=None):
    """无文案表时返回键本身。"""
    return 键#键即文案

def 显示名(名):
    """非 kebab 原样；Full access 产品标签另走。"""
    if 短横名.match(名) is None:#非 kebab
        return 名#原样
    段列表=[]#段
    for 段 in 名.split('-'):#逐段
        段列表.append(段[:1].upper()+段[1:])#Title
    return ' '.join(段列表)#Title

def 选项标签(选项):
    """Full access 固定产品名。"""
    值=选项['value'] if 选项 is not None and 'value' in 选项 else None#值
    if 值==完全访问:#满权
        return 'Full access'#产品
    名=选项['name'] if 选项 is not None and 'name' in 选项 and 选项['name'] is not None else ''#名
    return 显示名(名)#名

class 权限选择:
    """无投影不渲染；Full access 需确认。"""

    def __init__(自身,属性=None):
        """记下 props 与本地态。"""
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.挑选=None#乐观值
        自身.已开=False#菜单
        自身.确认中=None#待确认 id
        自身.已知情=False#确认勾选

    def 更新(自身,属性):
        """锁定或无值时关菜单。"""
        自身.属性=属性 if 属性 is not None else {}#新
        锁定=自身.属性['locked'] is True if 'locked' in 自身.属性 else False#锁
        值=自身.属性['value'] if 'value' in 自身.属性 else None#值
        if 锁定 is True or 值 is None:#锁或无
            自身.已开=False#关
            自身.已知情=False#清
            自身.确认中=None#清

    def 切换菜单(自身):
        """翻转菜单。"""
        自身.已开=not 自身.已开#翻

    def 提交(自身,标识):
        """/permission <id>。"""
        命令=自身.属性['command'] if 'command' in 自身.属性 else None#命令
        自身.挑选=标识#乐观
        if 命令 is not None:#有
            try:#投递
                命令(f'/permission {标识}')#提交
            finally:#清乐观
                自身.挑选=None#清
        else:#无
            自身.挑选=None#清

    def 选择(自身,标识):
        """同值忽略；满权走确认。"""
        自身.已开=False#关菜单
        值=自身.属性['value'] if 'value' in 自身.属性 else None#投影
        if 值 is None:#无
            return#无事
        当前=值['currentValue'] if 'currentValue' in 值 else None#当前
        if 标识==当前:#同
            return#无事
        if 标识==完全访问:#满权
            自身.已知情=False#清勾
            自身.确认中=标识#待确认
            return#等确认
        自身.提交(标识)#直接提交

    def 关确认(自身):
        """清态。"""
        自身.已知情=False#清
        自身.确认中=None#清

    def 设知情(自身,开):
        """确认勾选。"""
        自身.已知情=开 is True#勾

    def 确认满权(自身):
        """需知情勾选。"""
        锁定=自身.属性['locked'] is True if 'locked' in 自身.属性 else False#锁
        if 锁定 is True or 自身.已知情 is False or 自身.确认中 is None:#不可
            return#无事
        标识=自身.确认中#id
        自身.关确认()#关
        自身.提交(标识)#提交

    def 渲染(自身):
        """无投影返回 None。"""
        属性=自身.属性#props
        值=属性['value'] if 'value' in 属性 else None#投影
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        锁定=属性['locked'] is True if 'locked' in 属性 else False#锁
        if 值 is None:#无能力
            return None#空
        当前值=自身.挑选 if 自身.挑选 is not None else (值['currentValue'] if 'currentValue' in 值 else None)#当前
        选项列表=值['options'] if 'options' in 值 and 值['options'] is not None else []#选项
        当前=None#当前选项
        for 项 in 选项列表:#找
            项值=项['value'] if 'value' in 项 else None#值
            if 项值==当前值:#命中
                当前=项#记下
                break#停
        忙=自身.挑选 is not None or 自身.确认中 is not None#忙
        条目=[]#菜单项
        for 项 in 选项列表:#过滤 custom
            项值=项['value'] if 'value' in 项 else None#值
            if 项值=='custom':#跳
                continue#跳
            条目.append({#项
                'id':项值,#id
                'label':选项标签(项),#标签
                'glyph':项值 if 项值 in 权限字形键 else None,#字形
            })#结束项
        触发名=选项标签(当前) if 当前 is not None else 显示名(当前值 if 当前值 is not None else '')#触发文案
        描述=当前['description'] if 当前 is not None and 'description' in 当前 else None#描述
        确认=None if 自身.确认中 is None else {#确认
            'title':翻译('access.confirm.title'),#标题
            'description':翻译('access.confirm.description'),#描述
            'acknowledge':翻译('access.confirm.acknowledge'),#知情
            'cancel':翻译('access.confirm.cancel'),#取消
            'enable':翻译('access.confirm.enable'),#启用
            'acknowledged':自身.已知情,#勾
            'onAcknowledge':自身.设知情,#勾选
            'onCancel':自身.关确认,#取消
            'onEnable':自身.确认满权,#启用
        }#结束确认
        return {#根
            'trigger':{#触发
                'label':触发名,#文案
                'aria':翻译('input.accessMode',{'name':触发名}),#aria
                'title':描述,#描述
                'glyph':当前值 if 当前值 in 权限字形键 else None,#字形
                'open':自身.已开,#开
                'disabled':锁定 is True or 忙 is True,#禁用
                'onClick':自身.切换菜单,#切换
            },#结束触发
            'menu':{'open':自身.已开,'items':条目,'selectedId':当前值,'onSelect':自身.选择},#菜单
            'confirm':确认,#确认
        }#结束根
