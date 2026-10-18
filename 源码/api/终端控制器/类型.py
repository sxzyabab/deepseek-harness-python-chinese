'浏览器终端身份、元数据和屏幕流帧。本文件只有数据说明，运行时不造值'

# WebTerminalId：一个会话、一次宿主寿命里的终端身份
# TerminalRetentionFrame：{'type':'retained'}
# TerminalShell：path、args、name
# TerminalEnvironment：cwd、maxInputBytes、maxBufferedBytes、maxCols、maxRows、scrollback
# WebTerminalInfo：id、title、shell、cwd、cols、rows、state、exitCode，失败时可有 error
#   state 取 running、exited、failed
# TerminalCreateRequest：id、cols、rows，可选 shellPath
# TerminalInput：
#   {'type':'write','sequence':序号,'data':文本}
#   {'type':'resize','sequence':序号,'cols':列,'rows':行}
# TerminalFrame：
#   {'type':'snapshot','sequence':序号,'screen':屏幕,'info':信息,'writable':可否写,'inputWindow':可选}
#   {'type':'output','sequence':序号,'data':文本}
#   {'type':'state','info':信息,'writable':可否写}
#   {'type':'ack','sequence':序号,'refusal':可选}
# 远程错误细节：
#   terminal/unavailable 空对象
#   terminal/control-unavailable 的 reason 为 read-only 或 not-running
#   terminal/limit-reached 的 limit 为数量
#   terminal/view 的 issue 为 missingTerminal、inputFull、attachmentEnded、invalidOutput、terminalLimit
