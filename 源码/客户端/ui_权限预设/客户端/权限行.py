from .呈现 import 完全权限预设,展示权限预设#产品标签与完全访问机值

__all__=['权限行','样式表']#仅中文公开名

样式表='''#对齐 PermissionRow.module.css
.row{display:flex;align-items:center;gap:8px;padding:16px 0;border-bottom:0.5px solid var(--dsw-alias-border-l2)}
.rowText{flex:1;min-width:0;display:flex;flex-direction:column;gap:4px;padding-right:48px}
.title{font-size:14px;font-weight:400;line-height:22px;color:var(--dsw-alias-label-primary)}
.desc{font-size:12px;font-weight:400;line-height:18px;color:var(--dsw-alias-label-tertiary)}
.selector{display:inline-flex;align-items:center;gap:12px;height:36px;padding:0 14px;border:none;border-radius:18px;background:var(--dsw-alias-bg-module-platform);font:inherit;font-size:14px;line-height:22px;color:var(--dsw-alias-label-primary);cursor:pointer}
.selector:hover:not(:disabled){background:var(--dsw-alias-interactive-bg-hover)}
.selector:disabled{cursor:default}
.chevron{flex:none}
'''#样式表结束

class 权限行:
    """后续新建会话的默认预设行。"""
    def __init__(自身,属性):
        """记下 props 并触发首读。"""
        自身.属性=属性#合成 props
        自身.已开=False#菜单
        自身.确认满权=False#待确认完全权限
        自身.已知情=False#确认勾选
        属性['load']()#首读

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=属性#最新
        自身.复位若失效()#不可写则关

    def 读状态(自身):
        """经 usePermission 选择器。"""
        用权限=自身.属性['usePermission']#选择器
        def 原样(快照):
            """整表。"""
            return 快照#快照
        return 用权限(原样)#快照

    def 复位若失效(自身):
        """不可写或不可用时关菜单。"""
        状态=自身.读状态()#行快照
        if 状态['writable'] is True and 状态['status']!='unavailable':#仍有效
            return#不动
        自身.已开=False#关菜单
        自身.已知情=False#清勾
        自身.确认满权=False#清确认

    def 关菜单(自身):
        """关掉下拉。"""
        自身.已开=False#关

    def 切换菜单(自身):
        """翻转菜单。"""
        自身.已开=not 自身.已开#翻

    def 选择(自身,标识):
        """同值忽略；满权走确认。"""
        自身.已开=False#关菜单
        状态=自身.读状态()#行快照
        if 标识==状态['currentValue']:#同
            return#无事
        if 标识==完全权限预设:#满权
            自身.已知情=False#清勾
            自身.确认满权=True#待确认
            return#等确认
        自身.属性['select'](标识)#写入默认

    def 关确认(自身):
        """清确认态。"""
        自身.已知情=False#清勾
        自身.确认满权=False#清确认

    def 设知情(自身,开):
        """确认勾选。"""
        自身.已知情=开 is True#勾

    def 确认启用(自身):
        """关掉确认后写入完全权限。"""
        自身.已知情=False#清勾
        自身.确认满权=False#清确认
        自身.属性['select'](完全权限预设)#写入

    def 渲染(自身):
        """宿主未露出权限设置则 None。"""
        自身.复位若失效()#快照驱动关菜单
        翻译=自身.属性['t']#文案
        状态=自身.读状态()#行快照
        if 状态['status']=='unavailable':#未服务
            return None#不渲染
        选中=None#当前选项
        for 项 in 状态['options']:#找
            if 项['id']==状态['currentValue']:#命中
                选中=项#记下
                break#停
        忙=(状态['status']=='loading' or 状态['status']=='saving'
            or 自身.确认满权 is True)#加载、保存或确认中
        if 选中 is not None:#有当前
            标签=展示权限预设(选中['id'],选中['label'],翻译)#产品标签
        elif 忙 is True:#尚未选出
            标签=翻译('loading')#加载
        else:#无选项
            标签=翻译('unavailable')#不可用
        说明=状态['error'] if 状态['error'] is not None else 翻译('description')#错误或说明
        条目=[]#菜单项
        for 项 in 状态['options']:#各预设
            条目.append({#项
                'id':项['id'],#机值
                'label':展示权限预设(项['id'],项['label'],翻译),#产品标签
            })#项结束
        禁用=(忙 is True or 状态['writable'] is not True
            or len(状态['options'])==0)#忙、只读或空选项
        return {#视图
            'type':'permission-row',#类型
            'title':翻译('title'),#标题
            'description':说明,#说明
            'role':'alert' if 状态['error'] is not None else None,#错误才 alert
            'label':标签,#触发文案
            'open':自身.已开,#菜单开
            'items':条目,#选项
            'selectedId':状态['currentValue'],#当前
            'onClose':自身.关菜单,#关菜单
            'onSelect':自身.选择,#点中
            'align':'end',#右齐
            'portal':True,#portal
            'disabled':禁用,#禁用
            'onToggle':自身.切换菜单,#切换
            'confirm':{#风险确认
                'open':自身.确认满权,#开
                'title':翻译('confirm.title'),#标题
                'description':翻译('confirm.description'),#说明
                'acknowledgeLabel':翻译('confirm.acknowledge'),#已知
                'cancelLabel':翻译('confirm.cancel'),#取消
                'closeLabel':翻译('close'),#关闭
                'confirmLabel':翻译('confirm.enable'),#启用
                'acknowledged':自身.已知情,#勾
                'disabled':状态['writable'] is not True or 状态['status']=='saving',#只读或保存中
                'onAcknowledgedChange':自身.设知情,#勾选
                'onCancel':自身.关确认,#取消
                'onConfirm':自身.确认启用,#启用
            },#确认结束
            'css':样式表,#样式
        }#视图结束

    def __call__(自身,属性=None):
        """对齐 React 调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
