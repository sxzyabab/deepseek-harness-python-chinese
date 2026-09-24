from ...ui_插件设置.字段 import 取值字段,密钥字段
from .文案 import 表单标签

__all__=['网页搜索卡片']

class 网页搜索卡片:
    """密钥、接口地址与单次搜索次数页。"""
    def __init__(自身,属性):
        """记下 props。"""
        自身.属性=属性

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=属性

    def 渲染(自身):
        """摘要或表单。"""
        翻译=自身.属性['t']
        def 全量(快照):
            """整份卡片快照。"""
            return 快照
        状态=自身.属性['useWebSearchCard'](全量)
        if 自身.属性['view']=='summary':
            return 翻译('description')
        禁用=not 状态['writable']
        def 改密钥(文):
            """改密钥草稿。"""
            自身.属性['edit']('apiKey',文)
        def 改地址(文):
            """改接口地址草稿。"""
            自身.属性['edit']('baseURL',文)
        def 复地址():
            """恢复接口地址默认。"""
            自身.属性['resetField']('baseURL')
        def 改次数(文):
            """改搜索次数草稿。"""
            自身.属性['edit']('maxUses',文)
        def 复次数():
            """恢复搜索次数默认。"""
            自身.属性['resetField']('maxUses')
        已配=状态['apiKeyConfigured']
        控件=[
            密钥字段({
                'id':'plugin-config-web-search-key',
                'label':翻译('apiKey'),
                'hint':翻译('apiKeyHint'),
                'disabled':not 状态['apiKeyWritable'],
                'text':状态['apiKey']['text'],
                'configured':已配,
                'stateLabel':翻译('apiKeySet') if 已配 else 翻译('apiKeyUnset'),
                'onEdit':改密钥,
            })(),
            取值字段({
                'id':'plugin-config-web-search-endpoint',
                'label':翻译('baseUrl'),
                'hint':翻译('baseUrlHint'),
                'overriddenLabel':翻译('overridden'),
                'resetLabel':翻译('reset'),
                'invalidLabel':翻译('invalidNumber'),
                'disabled':禁用,
                **状态['baseURL'],
                'onEdit':改地址,
                'onReset':复地址,
            })(),
            取值字段({
                'id':'plugin-config-web-search-max-uses',
                'label':翻译('maxUses'),
                'hint':翻译('maxUsesHint'),
                'overriddenLabel':翻译('overridden'),
                'resetLabel':翻译('reset'),
                'invalidLabel':翻译('invalidNumber'),
                'numeric':True,
                'disabled':禁用,
                **状态['maxUses'],
                'onEdit':改次数,
                'onReset':复次数,
            })(),
        ]
        return {
            'type':'settings-form',
            'labels':表单标签(翻译),
            'state':状态,
            'onSave':自身.属性['save'],
            'onDiscard':自身.属性['discard'],
            'children':控件,
        }

    def __call__(自身,属性=None):
        """对齐 React 调用。"""
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
