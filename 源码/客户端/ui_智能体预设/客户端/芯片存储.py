from ...存储 import 创建快照存储#快照仓
from ..异常 import 远程消息#失败句
from .设置存储 import 读名册,预设选项,等返回#名册

__all__=['芯片控制器']

初始={'options':[],'current':'','error':None,'busy':False,'introduce':False}#芯片初始快照

def 取预设(会话):
    '投影里的 agentPreset。只有字符串才算'
    if 会话 is None:#没有会话
        return None#无
    投影=会话.get('projectionValues')#投影
    if not isinstance(投影,dict):#没有
        return None#无
    值=投影.get('agentPreset')#预设
    if isinstance(值,str):#字符串
        return 值#标识
    return None#其它不算

class 芯片控制器:
    '暂存下一场会话的预设，会话还空白时立刻套上'
    def __init__(自身,上下文,当前会话,暂存选择=None):
        '记下依赖。暂存选择在同一页的芯片之间共用'
        自身.上下文=上下文#远程
        自身.当前会话=当前会话#此刻要交给谁
        自身.暂存选择=暂存选择 if 暂存选择 is not None else {'id':None,'introduce':False}#共用暂存
        自身.存储=创建快照存储(dict(初始))#快照
        自身.回退预设=''#宿主生效的默认
        自身.加载世代=0#只认最新一次读取
        自身.待选=None#进行中的 select

    def _合并(自身,补丁):
        '浅合并后整份换上'
        下一=dict(自身.存储.getSnapshot())#拷贝
        下一.update(补丁)#补丁
        自身.存储.set(下一)#换上

    def _清暂存(自身):
        '套用过或会话已经开始后，暂存不再有效'
        自身.暂存选择['id']=None#没有待套用
        自身.暂存选择['introduce']=False#不再介绍

    def 加载(自身):
        '读名册并打开到宿主默认。过期的读取不发布'
        自身.加载世代=自身.加载世代+1#新世代
        世代=自身.加载世代#钉住
        名册=读名册(自身.上下文)#名册
        if 世代!=自身.加载世代:#已被更新的读取盖掉
            return#丢掉
        错误=自身.存储.getSnapshot()['error']#可能是正在显示的拒绝
        if 名册['ok'] is not True:#读取失败
            if not isinstance(错误,dict):#对象拒绝留给芯片播报
                自身._合并({'error':名册['error']})#句子
            return#停
        预设列=名册['value']['presets']#行
        默认=''#宿主默认
        for 预设 in 预设列:#找默认
            if 预设.get('isDefault'):#是默认
                默认=预设['id']#标识
                break#停
        if 默认=='' and len(预设列)>0:#没有标默认就用第一份
            默认=预设列[0]['id']#第一份
        自身.回退预设=默认#记住
        会话=自身.当前会话()#当前
        暂存标识=自身.暂存选择.get('id')#暂存
        if 暂存标识 is not None:#先暂存
            当前=暂存标识#暂存
        elif 会话 is None:#还没有会话
            当前=自身.回退预设#默认
        else:#会话上已经有的
            已有=取预设(会话)#投影
            当前=已有 if 已有 is not None else ''#没有就空
        自身._合并({#发布
            'options':预设选项(预设列),#可选项
            'current':当前,#当前显示
            'error':错误 if isinstance(错误,dict) else None,#只留对象拒绝
            'introduce':自身.暂存选择.get('introduce') is True,#要不要介绍
        })
        自身.套用()#会话已经在就套上

    def 选定(自身,标识):
        '忙则忽略。先暂存，空白会话已经在就立刻套用'
        if 自身.存储.getSnapshot()['busy']:#正在套用
            return None#忽略
        自身.暂存(标识)#暂存
        return 自身.套用()#套用

    def 暂存(自身,标识,介绍=False):
        '只暂存，不立刻套用。创造模式从别的页面进来时用这个'
        自身.暂存选择['id']=标识#待套用
        自身.暂存选择['introduce']=介绍#要不要介绍
        自身._合并({'current':标识,'error':None,'introduce':介绍})#芯片先显示它

    def 确认拒绝(自身,拒绝):
        '吐司播完后确认。更新的一次拒绝不被动掉'
        if not isinstance(拒绝,dict):#不是这次对象
            return#不动
        if 自身.存储.getSnapshot()['error'] is 拒绝:#仍是这一次
            自身._合并({'error':拒绝['reason']})#留下原因句子

    def 空白会话标识(自身):
        '当前若仍是空白会话，返回它的标识'
        会话=自身.当前会话()#当前
        if 会话 is not None and 会话.get('blank') is True:#空白
            return 会话['id']#标识
        return None#不是

    def 同步空白会话(自身,期望会话标识,标识):
        '设置写完后，只有捕获的那场仍空白才套用'
        if 自身.待选 is not None:#还有一次选择没完
            等返回(自身.待选)#等它
        会话=自身.当前会话()#现在
        if 会话 is None or 会话.get('blank') is not True or 会话.get('id')!=期望会话标识:#已经不是那场
            return None#不用套
        自身.暂存(标识)#暂存
        return 自身.套用()#套用

    def 已介绍(自身):
        '芯片播完介绍后确认'
        if 自身.存储.getSnapshot()['introduce'] is not True:#没有在介绍
            return#不动
        自身.暂存选择['introduce']=False#共用暂存也清
        自身._合并({'introduce':False})#清

    def 套用(自身):
        '把暂存交给当前空白会话。列表变化和选定都会走到这里'
        if 自身.存储.getSnapshot()['busy']:#正在套用
            return None#列表更新不再重复
        暂存标识=自身.暂存选择.get('id')#暂存
        会话=自身.当前会话()#当前
        if 暂存标识 is None:#没有待套用
            当前=自身.回退预设 if 会话 is None else 取预设(会话)#显示
            if 当前 is None:#没有
                当前=''#空
            if 当前!=自身.存储.getSnapshot()['current']:#和画面不一致
                自身._合并({'current':当前})#对齐
            return None#没有切换
        if 会话 is None:#会话还没出现
            return None#留着暂存
        if 会话.get('blank') is not True or 取预设(会话)==暂存标识:#已经开始或已经是它
            自身._清暂存()#暂存没用了
            return None#不切换
        自身._清暂存()#先消费，失败时再按剩下的暂存显示
        def 拒绝(原因):
            '记下被拒的预设。显示回到之后的暂存，或会话上的预设'
            预设=None#选项
            for 选项 in 自身.存储.getSnapshot()['options']:#找
                if 选项['id']==暂存标识:#就是这份
                    预设=选项#用它的名字
                    break#停
            if 预设 is None:#名册里没有
                预设={'id':暂存标识}#只剩标识
            已有=取预设(会话)#会话上的
            后来=自身.暂存选择.get('id')#等待期间可能又暂存了
            if 后来 is not None:#有新暂存
                显示=后来#新的
            elif 已有 is not None:#会话上有
                显示=已有#会话的
            else:#都没有
                显示=''#空
            自身._合并({'error':{'reason':原因,'preset':预设},'current':显示})#拒绝
            return 原因#交给调用方
        try:#选择
            自身._合并({'busy':True,'error':None})#忙
            期约=自身.上下文.remote.agentPresets.select(会话['id'],暂存标识)#选择
            自身.待选=期约#给后来的同步等
            结果=等返回(期约)#结果
            if 结果.get('ok') is not True:#拒绝
                错误=结果.get('error')#错误
                细节=错误.get('details') if isinstance(错误,dict) else getattr(错误,'details',None)#细节
                if isinstance(细节,dict) and isinstance(细节.get('reason'),str):#有单独原因
                    拒绝文=细节['reason']#原因
                else:#否则用消息
                    拒绝文=远程消息(错误)#消息
                return 拒绝(拒绝文)#记下
            后来=自身.暂存选择.get('id')#等待期间的新暂存
            自身._合并({'current':后来 if 后来 is not None else 结果['value']})#落定
            return None#成功
        except Exception as 错误:#调用本身失败
            return 拒绝(远程消息(错误))#记下
        finally:#结束这一次
            自身.待选=None#放开
            自身._合并({'busy':False})#不再忙
