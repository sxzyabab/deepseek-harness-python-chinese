from ...异常 import 聊天错误
from .节点工厂 import 聊天节点

__all__=['系统消息定义','请求提示定义']


def 请求提示锚(匹配项,先前,是初始):
    '请求的系统提示放在它可见消息串的开头。同一步里已有锚就留在事件自己的位置'
    位置=匹配项.get('location') if isinstance(匹配项.get('location'),dict) else {}
    事件=匹配项.get('event') if isinstance(匹配项,dict) else {}
    if 位置.get('kind')!='step':
        return 事件.get('seq')
    if 先前 is None and not 是初始:
        return 事件.get('seq')
    回合=位置.get('turn') if isinstance(位置.get('turn'),dict) else {}
    步=位置.get('step') if isinstance(位置.get('step'),dict) else {}
    if isinstance(先前,dict) and 先前.get('turn')==回合.get('turn') and 先前.get('step')==步.get('step'):
        return 事件.get('seq')
    if 步.get('step')==1:
        回合起=回合.get('start') if isinstance(回合.get('start'),dict) else None
        步起=步.get('start') if isinstance(步.get('start'),dict) else None
        if isinstance(回合起,dict) and 回合起.get('seq') is not None:
            return 回合起.get('seq')
        if isinstance(步起,dict) and 步起.get('seq') is not None:
            return 步起.get('seq')
        return 事件.get('seq')
    步起=步.get('start') if isinstance(步.get('start'),dict) else None
    if isinstance(步起,dict) and 步起.get('seq') is not None:
        return 步起.get('seq')
    return 事件.get('seq')


def 稳定请求提示锚(上下文,匹配项,先前,是初始):
    '已经画过的提示留在这一页的锚上'
    当前表=上下文.get('current')
    当前=当前表.get('chat') if hasattr(当前表,'get') else None
    if isinstance(当前,dict) and 当前.get('kind')=='system-prompt':
        return 当前.get('anchorSeq')
    return 请求提示锚(匹配项,先前,是初始)


def 系统消息定义(检视):
    '聊天目标上的系统提示。每条非空追加都有卡片，替换交给请求提示定义'
    def 匹配(事件):
        '系统消息，以及非追加的表面操作'
        if 事件.get('type')=='system/message' or ('surfaceOp' in 事件 and 事件.get('surfaceOp')!='append'):
            return {'id':str(事件.get('seq')),'role':'start'}
        return None

    def 开始(上下文,匹配项,读取器):
        '实时块不能当系统提示'
        事件=匹配项.get('event') if isinstance(匹配项,dict) else None
        if isinstance(事件,dict) and 事件.get('type')=='assistant/live-chunk':
            raise 聊天错误('system-message requires a durable event')
        先前=读取器.previous('system-message')
        先前态=先前.get('state') if isinstance(先前,dict) else None
        return 检视(先前态,事件)

    def 更新(上下文,匹配项=None):
        '系统提示状态不再改'
        return 上下文.get('state')

    def 建视图(上下文):
        '非空追加才画卡片。更新留在自己的位置，初始卡片放在步骤输入之前'
        状态=上下文.get('state') if isinstance(上下文.get('state'),dict) else None
        引入=状态.get('introduced') if isinstance(状态,dict) else None
        起点=上下文.get('start') if isinstance(上下文.get('start'),dict) else None
        起点事件=起点.get('event') if isinstance(起点,dict) else None
        if (
            not isinstance(引入,dict)
            or 引入.get('text')==''
            or not isinstance(起点事件,dict)
            or 起点事件.get('type')!='system/message'
            or 起点事件.get('surfaceOp')!='append'
        ):
            return None
        if 引入.get('update'):
            锚=引入.get('seq')
        else:
            锚=请求提示锚(起点,None,True)
        数据={'text':引入.get('text')}
        if 引入.get('update'):
            数据['update']=True
        return 聊天节点(上下文,'system-prompt',锚,数据)

    return {
        'kind':'system-message',
        'target':'chat',
        'match':匹配,
        'start':开始,
        'update':更新,
        'buildViewNode':建视图,
    }


def 请求提示定义(检视):
    '请求头上的提示卡片。恢复和显式新串即使系统文本没变也留卡片'
    def 匹配(事件):
        '只认请求头'
        if 事件.get('type')=='request/header':
            return {'id':str(事件.get('seq')),'role':'start'}
        return None

    def 开始(上下文,匹配项,读取器):
        '用会话服务给的检视决定这张卡片出不出现'
        事件=匹配项.get('event') if isinstance(匹配项,dict) else None
        if not isinstance(事件,dict) or 事件.get('type')!='request/header':
            raise 聊天错误('request-prompt start requires request/header')
        先前记录=读取器.previous('request-prompt')
        先前=先前记录.get('state') if isinstance(先前记录,dict) else None
        系统记录=读取器.previous('system-message')
        系统态=系统记录.get('state') if isinstance(系统记录,dict) else None
        系统=系统态.get('effective') if isinstance(系统态,dict) else None
        位置=匹配项.get('location') if isinstance(匹配项.get('location'),dict) else {}
        if 位置.get('kind')=='step':
            回合=位置.get('turn') if isinstance(位置.get('turn'),dict) else {}
            步=位置.get('step') if isinstance(位置.get('step'),dict) else {}
            坐标={'turn':回合.get('turn'),'step':步.get('step')}
        else:
            坐标={}
        系统事件=None
        if isinstance(系统记录,dict) and isinstance(系统记录.get('matches'),list) and len(系统记录['matches'])>0:
            首=系统记录['matches'][0]
            if isinstance(首,dict):
                系统事件=首.get('event')
        检视结果=检视(先前.get('prompt') if isinstance(先前,dict) else None,事件,系统)
        变化=None
        if isinstance(检视结果,dict) and isinstance(检视结果.get('change'),dict):
            变化=检视结果['change'].get('kind')
        数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
        已被更新展示=(
            isinstance(系统,dict)
            and isinstance(系统事件,dict)
            and 系统事件.get('type')=='system/message'
            and 系统事件.get('surfaceOp')=='append'
            and (系统.get('update') or 先前 is None)
            and 系统.get('turn')==坐标.get('turn')
            and 系统.get('step')==坐标.get('step')
        )
        显示提示=(
            not 已被更新展示
            and (
                先前 is None
                or 数据.get('reason')!='change'
                or 数据.get('startsSeries') is True
                or 变化=='system'
                or 变化=='system-and-tools'
            )
        )
        结果={
            'anchorSeq':稳定请求提示锚(上下文,匹配项,先前,数据.get('reason')=='initial'),
            'showsPrompt':显示提示,
        }
        结果.update(坐标)
        if isinstance(检视结果,dict):
            结果.update(检视结果)
        return 结果

    def 更新(上下文,匹配项=None):
        '请求提示不再改'
        return 上下文.get('state')

    def 建视图(上下文):
        '要显示且系统文本非空才可见。已经是系统提示的当前节点在隐藏时也留着'
        状态=上下文.get('state')
        if not isinstance(状态,dict):
            return None
        当前表=上下文.get('current')
        当前=当前表.get('chat') if hasattr(当前表,'get') else None
        提示=状态.get('prompt') if isinstance(状态.get('prompt'),dict) else {}
        可见=状态.get('showsPrompt') is True and 提示.get('system')!=''
        if not 可见 and not (isinstance(当前,dict) and 当前.get('kind')=='system-prompt'):
            return None
        return 聊天节点(
            上下文,
            'system-prompt',
            状态.get('anchorSeq'),
            {'text':提示.get('system')},
            {'visibility':'visible' if 可见 else 'hidden'},
        )

    return {
        'kind':'request-prompt',
        'target':'chat',
        'match':匹配,
        'start':开始,
        'update':更新,
        'buildViewNode':建视图,
    }
