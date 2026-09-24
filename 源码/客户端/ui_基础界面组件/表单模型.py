from ..存储 import 创建快照存储

__all__=['设置数字字段','设置文本字段','设置表单模型']

def 设置数字字段(字段):
    """空草稿清除；非有限数字挡住保存。"""
    def 格式化(值):
        if type(值) is bool:
            return ''
        if type(值) in (int,float):
            return str(值)
        return ''
    def 解析(文本):
        修剪=文本.strip()
        if 修剪=='':
            return {'kind':'clear'}
        try:
            if any(符 in 修剪 for 符 in '.eE'):
                解析值=float(修剪)
            else:
                解析值=int(修剪)
        except ValueError:
            return None
        if type(解析值) is float and (解析值!=解析值 or 解析值==float('inf') or 解析值==float('-inf')):
            return None
        return {'kind':'set','value':解析值}
    return {'field':字段,'format':格式化,'parse':解析}

def 设置文本字段(字段):
    """空草稿清除，与复位同一手势。"""
    def 格式化(值):
        return 值 if isinstance(值,str) else ''
    def 解析(文本):
        修剪=文本.strip()
        if 修剪=='':
            return {'kind':'clear'}
        return {'kind':'set','value':修剪}
    return {'field':字段,'format':格式化,'parse':解析}

class 设置表单模型:
    """在一份设置命名空间上暂存编辑，保存时一次写入。"""
    def __init__(自身,作用域,规格表,密钥表=None):
        """记下作用域、节字段与只写控件。"""
        自身.作用域=作用域
        自身.规格表={项['field']:项 for 项 in 规格表}
        自身.密钥表={项['field']:项 for 项 in (密钥表 or [])}
        自身.暂存={}
        自身.监听集合=set()
        自身.基线=None
        自身.退订=作用域.subscribe(自身.发布)
        自身.保存中=False
        自身.失败=False

    def 绑定(自身,投影):
        """槽组件经快照选择器读的仓。"""
        仓=创建快照存储(投影())
        def 刷新():
            仓.set(投影())
        自身.监听集合.add(刷新)
        return 仓

    def 外壳(自身):
        """卡片共用的宿主态与保存预览。"""
        快照=自身.作用域.getSnapshot()
        计划=自身.计划()
        非法=False
        for 项 in 计划:
            if 'run' not in 项 and 'op' not in 项:
                非法=True
                break
        return {
            'available':快照.get('status')=='ready',
            'writable':bool(快照.get('writable')),
            'dirty':len(计划)>0,
            'invalid':非法,
            'saving':自身.保存中,
            'failed':自身.失败,
        }

    def 字段(自身,字段):
        """控件草稿、覆盖徽章与非法态。"""
        暂=自身.暂存.get(字段)
        if 字段 in 自身.密钥表:
            return {'text':'' if 暂 is None else 暂['text'],'overridden':False,'invalid':False}
        规格=自身.取规格(字段)
        if 暂 is None:
            return {'text':规格['format'](自身.节值(字段)),'overridden':自身.已存(字段),'invalid':False}
        写入={'kind':'clear'} if 暂['clear'] else 规格['parse'](暂['text'])
        return {
            'text':暂['text'],
            'overridden':写入 is not None and 写入.get('kind')=='set',
            'invalid':写入 is None,
        }

    def 动作(自身):
        """槽位注入的编辑、复位、保存、丢弃。"""
        def 编辑(字段,文本):
            自身.入暂(字段,{'text':文本,'clear':False})
        def 复位字段(字段):
            自身.入暂(字段,{'text':自身.取规格(字段)['format'](自身.基值(字段)),'clear':True})
        def 丢弃():
            if len(自身.暂存)==0 and not 自身.失败:
                return
            自身.暂存.clear()
            自身.基线=None
            自身.失败=False
            自身.发布()
        return {'edit':编辑,'resetField':复位字段,'save':自身.保存,'discard':丢弃}

    def 保存(自身):
        """写入全部暂存，再按宿主接受结果重播。"""
        计划=自身.计划()
        快照=自身.作用域.getSnapshot()
        if len(计划)==0 or 自身.保存中 or not 快照.get('writable'):
            return
        for 项 in 计划:
            if 'run' not in 项 and 'op' not in 项:
                return
        自身.保存中=True
        自身.失败=False
        自身.发布()
        try:
            操作表=[项['op'] for 项 in 计划 if 'op' in 项]
            修订=None if 自身.基线 is None else 自身.基线.get('revision')
            落地=len(操作表)==0 or 自身.作用域.mutate(操作表,修订)
            if hasattr(落地,'等待'):
                落地=落地.等待()
            if not 落地:
                自身.失败=True
                return
            for 项 in 计划:
                if 'run' in 项:
                    附加=项['run']()
                    if hasattr(附加,'等待'):
                        附加=附加.等待()
                    落地=附加 and 落地
            if 落地:
                自身.暂存.clear()
                自身.基线=None
            自身.失败=not 落地
        except Exception:
            自身.失败=True
        finally:
            自身.保存中=False
            自身.发布()

    def 拆除(自身):
        """释放已接受值订阅。"""
        自身.退订()
        自身.监听集合.clear()

    def 计划(自身):
        """保存将执行的写入；非法草稿占位且挡住保存。"""
        计划=[]
        for 字段,暂 in 自身.暂存.items():
            if 字段 in 自身.密钥表:
                值=暂['text'].strip()
                if 值!='':
                    写=自身.密钥表[字段]['write']
                    计划.append({'field':字段,'run':lambda 文=值,函=写:函(文)})
                continue
            规格=自身.取规格(字段)
            if 暂['clear']:
                if 自身.已存(字段):
                    计划.append({'field':字段,'op':{'op':'unset','path':[字段]}})
                continue
            if 暂['text']==规格['format'](自身.节值(字段)):
                continue
            写入=规格['parse'](暂['text'])
            if 写入 is None:
                计划.append({'field':字段})
            elif 写入['kind']=='clear':
                计划.append({'field':字段,'op':{'op':'unset','path':[字段]}})
            else:
                计划.append({'field':字段,'op':{'op':'set','path':[字段],'value':写入['value']}})
        return 计划

    def 入暂(自身,字段,编辑):
        if 自身.基线 is None:
            自身.基线=自身.作用域.getSnapshot()
        自身.暂存[字段]=编辑
        自身.失败=False
        自身.发布()

    def 取规格(自身,字段):
        if 字段 not in 自身.规格表:
            raise RuntimeError('插件卡片没有字段 '+字段)
        return 自身.规格表[字段]

    def 节值(自身,字段):
        值=自身.作用域.getSnapshot().get('value')
        if not isinstance(值,dict):
            return None
        return 值.get(字段)

    def 基值(自身,字段):
        值=自身.作用域.getSnapshot().get('base')
        if not isinstance(值,dict):
            return None
        return 值.get(字段)

    def 已存(自身,字段):
        用户=自身.作用域.getSnapshot().get('user')
        return isinstance(用户,dict) and 字段 in 用户

    def 发布(自身):
        for 监听 in list(自身.监听集合):
            监听()
