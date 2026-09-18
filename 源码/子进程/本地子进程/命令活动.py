"""私有 shell 生命周期文件；普通输出从不授权终端回收。"""
import os,re,tempfile#路径、状态解析与临时目录

__all__=('命令活动','准备命令活动',)#仅中文公开名

状态模式=re.compile(r'^(\d+):(\d+):(idle|busy)\n?\Z')#状态行

def 单引号(值):
    """单引号 shell 转义。"""
    return "'"+值.replace("'","'\\''")+"'"#转义

class 命令活动:
    """一次普通交互 shell 的可选启动集成与修订跟踪。"""
    def __init__(自身,目录,参数表,环境):
        """记下私有目录、启动参数与环境。"""
        自身.目录=目录#私有目录
        自身.参数表=参数表#argv
        自身.环境=环境#env
        自身.修订=0#修订号
        自身.已观察=''#已观察记录
        自身.已失效=None#失效前记录
        自身.状态='unknown'#活动状态

    def 失效(自身):
        """在投递输入或前台信号前使提示证据失效。"""
        自身.已失效=自身._读取()#记下当前
        自身.修订+=1#抬修订
        自身.状态='unknown'#未知

    def 检查(自身,进程号):
        """读取最新顶层 shell 跃迁。"""
        记录=自身._读取()#读状态
        if 记录!=自身.已观察:#新记录
            自身.已观察=记录#记下
            自身.修订+=1#抬修订
        匹配=状态模式.match(记录)#解析
        if 记录==自身.已失效 or 匹配 is None or 匹配.group(1)!=str(进程号):#失效或不匹配
            自身.状态='unknown'#未知
        else:#命中
            自身.状态=匹配.group(3)#idle/busy
        return {'state':自身.状态,'revision':自身.修订}#活动

    def 拆除(自身):
        """进程静止后删除私有启动与状态文件。"""
        for 根,目录表,文件表 in os.walk(自身.目录,topdown=False):#自底向上
            for 名 in 文件表:#文件
                try:#删
                    os.unlink(os.path.join(根,名))#删文件
                except OSError:#忽略
                    pass#继续
            for 名 in 目录表:#目录
                try:#删
                    os.rmdir(os.path.join(根,名))#删目录
                except OSError:#忽略
                    pass#继续
        try:#删根
            os.rmdir(自身.目录)#删根
        except OSError:#忽略
            pass#继续

    def _读取(自身):
        """读状态文件。"""
        try:#读
            with open(os.path.join(自身.目录,'state'),'r',encoding='utf-8') as 文件:#打开
                return 文件.read()#内容
        except OSError:#不可用
            return ''#空

def 准备命令活动(规格,环境,平台):
    """为普通、非登录交互启动准备可选的 Bash 或 Zsh 集成。"""
    if 规格.get('shellActivity') is not True or 平台=='win32':#未启用或 Windows
        return None#不支持
    参数表=规格.get('argv') or []#参数
    if len(参数表)!=2 or 参数表[1]!='-i':#非简单 -i
        return None#不支持
    壳名=os.path.basename(参数表[0])#shell 名
    if 壳名!='bash' and 壳名!='zsh':#非 bash/zsh
        return None#不支持
    目录=tempfile.mkdtemp(prefix='dsh-shell-')#私有目录
    状态=单引号(os.path.join(目录,'state'))#状态路径
    守卫=单引号(os.path.join(目录,'guards'))#守卫路径
    try:#写启动文件
        if 壳名=='bash':#Bash
            配置=os.path.join(目录,'bashrc')#rc
            with open(配置,'x',encoding='utf-8') as 文件:#独占写
                文件.write('\n'.join([#片段
                    '[[ ! -r ~/.bashrc ]] || builtin source ~/.bashrc',
                    'if (( BASH_VERSINFO[0] > 4 || (BASH_VERSINFO[0] == 4 && BASH_VERSINFO[1] >= 4) )) && [[ ! $(declare -p PROMPT_COMMAND PS0 2>/dev/null) =~ declare\\ -[^[:space:]]*r ]]; then',
                    '  __dsh_shell_pid=$BASHPID; __dsh_shell_sequence=0',
                    '  __dsh_shell_idle() {',
                    '    local result=$?',
                    '    if [[ $BASHPID == "$__dsh_shell_pid" ]]; then',
                    '      (( ++__dsh_shell_sequence ))',
                    '      local activity=idle',
                    f'      builtin trap -p >| {守卫}',
                    f'      [[ ! -s {守卫} ]] || activity=unknown',
                    f'      builtin printf \'%s:%s:%s\\n\' "$BASHPID" "$__dsh_shell_sequence" "$activity" >| {状态}',
                    '    fi',
                    '    return "$result"',
                    '  }',
                    '  if [[ $(declare -p PROMPT_COMMAND 2>/dev/null) == "declare -a "* ]]; then',
                    '    PROMPT_COMMAND+=(__dsh_shell_idle)',
                    '  else',
                    '    PROMPT_COMMAND="${PROMPT_COMMAND}"$\'\\n\'"__dsh_shell_idle"',
                    '  fi',
                    f'  PS0+={单引号(f"$(builtin printf \'%s:%s:busy\' \"$__dsh_shell_pid\" \"$__dsh_shell_sequence\" >| {状态})")}',
                    'fi',
                    '',
                ]))#写完
            return 命令活动(目录,[参数表[0],'--rcfile',配置,'-i'],环境)#带 rcfile
        with open(os.path.join(目录,'.zshenv'),'x',encoding='utf-8') as 文件:#Zsh
            原点=环境.get('ZDOTDIR')#原 ZDOTDIR
            文件.write('\n'.join([#片段
                'unset ZDOTDIR' if 原点 is None else f'ZDOTDIR={单引号(原点)}',
                '[[ ! -r ${ZDOTDIR:-$HOME}/.zshenv ]] || builtin source "${ZDOTDIR:-$HOME}/.zshenv"',
                'typeset -g __dsh_shell_pid=$$ __dsh_shell_sequence=0',
                '__dsh_shell_activity() {',
                '  (( ZSH_SUBSHELL == 0 && $$ == __dsh_shell_pid )) || return',
                '  (( ++__dsh_shell_sequence ))',
                f'  builtin printf \'%s:%s:%s\\n\' "$$" "$__dsh_shell_sequence" "$1" >| {状态}',
                '  return 0',
                '}',
                '__dsh_shell_idle() {',
                f'  {{ builtin trap; zle -F; }} >| {守卫}',
                '  if [[ $CONTEXT != start || -n $BUFFER ]]; then __dsh_shell_activity busy',
                f'  elif [[ -s {守卫}'+' || -n ${(k)functions[(I)TRAP*]} ]]; then __dsh_shell_activity unknown',
                '  else __dsh_shell_activity idle; fi',
                '}',
                '__dsh_shell_busy() { __dsh_shell_activity busy }',
                '__dsh_shell_init() {',
                '  autoload -Uz add-zle-hook-widget add-zsh-hook',
                '  add-zle-hook-widget line-init __dsh_shell_idle',
                '  add-zle-hook-widget line-finish __dsh_shell_busy',
                '  add-zsh-hook preexec __dsh_shell_busy',
                '  precmd_functions=(${precmd_functions:#__dsh_shell_init})',
                '}',
                'typeset -ga precmd_functions',
                'precmd_functions+=(__dsh_shell_init)',
                '',
            ]))#写完
        下一环境=dict(环境)#拷贝
        下一环境['ZDOTDIR']=目录#改目录
        return 命令活动(目录,参数表,下一环境)#Zsh
    except Exception:#写失败
        命令活动(目录,[],{}).拆除()#清理
        raise#再抛
