"""确定性工具结果修剪的词汇类型。仅类型——运行时解析与修剪住在配置与包根。"""
工具结果修剪配置字段=('thresholdChars','headChars','tailChars')#原始修剪配置：触发阈值、开头保留、结尾保留
已解析配置字段=('thresholdChars','headChars','tailChars')#已校验、分离、深不可变的修剪配置
修剪记账字段=('originalSeq','replacementSeq','callId','charsBefore','charsAfter')#一次落地表面替换所引用的源事件与大小记账
修剪结果字段=('pruned','charsRemoved')#一次稳定表面修剪遍的汇总结果
