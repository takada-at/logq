���르�ꥺ��
===============

## ���δ�ñ��
�������ϥ������Ф�����ӱ黻�Ҥȡ�and, or, not�ˤ�äƹ�������롣

```
(cols[1]=="hoge" or (cols[2]=="fuga" and cols[4]=="poyo")) or (cols[2]=="hogera" and cols[5]=="piyo")
```

logq�Ǥϡ��ޤ��������������ñ�����롣

����ʳ��Ǥϡ�1�İʾ��and������or�Ƿ�Ф줿���ˤ��롣

```
(cols[1]=='hoge') or (cols[2]=='fuga' and cols[4]=='poyo') or (cols[2]=='hogera' and cols[5]=='piyo')
```

�����ʳ��Ǥϡ����磻�󡦥ޥ��饹����ˡ��Ŭ�Ѥ�������ʤ��ñ������

(�ܺ٤Ͼʤ�)


## ��Ｐ��ơ��֥���Ѵ�
�����ʳ��Ǿ�Ｐ�ϡ�1�İʾ��and������or�Ƿ�Ф줿���ˤʤäƤ��롣

�ʲ���ɽ�γƹԤ�and����б����Ƥ��롣

|     |cols[1]|cols[2]|cols[4]|cols[5]|
|:----|:-----|:------|:-------|:------|
|���1 |=hoge |       |        |       |
|���2 |      |=fuga  |=poyo   |       |
|���3 |      |=hogera|        | =piyo |

�������ϰʲ���¹Ԥ���Ф�����

* �ƥ������б����뼰��õ����
* ����¹Ԥ��롣
    * ���Ԥ������
        * �ơ��֥뤫�餽�ιԤ���
        * ���٤ƤιԤ���������С������ϼ��Ԥ˽����
    * �����������
        * �⤷���μ����ԤκǸ�μ��Ǥ���С������������˽����
        * �Ǹ�μ��Ǥʤ���м��μ���õ�����ʤ���м��Υ�����

���Υ��르�ꥺ��ϰʲ��Τ褦��3�Ĥ�ɽ�Ȥ���ɽ���Ǥ��롣

* ���ߤξ��֡ߺ��ɤ�Ǥ��륫��फ�顢Ŭ�Ѥ��٤�������ꤹ��ɽ
* ���ߤξ��֡ߺ��ɤ�Ǥ��륫��फ�顢���������Ǥ��ä��������ܤ��٤����֤���ꤹ��ɽ
* ���ߤξ��֡ߺ��ɤ�Ǥ��륫��फ�顢�������ԤǤ��ä��������ܤ��٤����֤���ꤹ��ɽ

* ���֤ϰʲ���2�Ĥˤ�äƷ�ޤ�
    * �ƹԤξ���
        * �ƹԤμ����ҤȤĤǤ⼺�Ԥ����False���ޤ����Ԥ��Ƥ��ʤ����True��
    * �����β����ܤμ���
        * ���֡ߥ����ˤ�äơ���դ�Ŭ�Ѥ��٤�������ޤ�褦�ˤ��뤿��ˡ�Ʊ���������Ф���ʣ���μ�����������̤ξ��֤���դ�

�㤨�о��ɽ�ϰʲ��Τ褦�ʾ������ܤˤʤ롣1��Ƚ��������2��Ƚ�꼺��

���ƥ�����ϡ�(����������ξ��֡����Ը�ξ���)

|state |cols[1]    |cols[2]       |cols[4]       |cols[5]       |
|:-----|:----------|:-------------|:-------------|:-------------|
|0     |=hoge,[1],3|              |              |              |
|1     |           |              |              |              |
|2     |           |              |              |              |
|3     |           |=fuga,5,4     |=poyo,[1],4   |              |
|4     |           |=hogera,4,[2] |              |=piyo,[1],[2] |
|5     |           |=hogera,3,6   |              |=piyo,[1],[2] |
|6     |           |              |=poyo,[1],[2] |              |

![��������]('algorythm.png')

## ��������ɽ�ΤĤ�����
������狼���������ɽ���륢�르�ꥺ���ޤȤ�롣

|     |cols[1]|cols[2]|cols[4]|cols[5]|
|:----|:-----|:------|:-------|:------|
|���1 |=hoge |       |        |       |
|���2 |      |=fuga  |=poyo   |       |
|���3 |      |=hogera|        | =piyo |

������and���3�Ĥ��롣�ޤ���cols[2]��Ŭ�Ѥ��٤�����2�Ĥ���Τǡ���ǽ�ʾ��֤ν���ϰʲ��Τ褦�ˤʤ롣

|���1 | ���2 | ���3   |������ǥå���|
|:-----|:------|:-------|:------|
| True | True  | True   | 0     |
| True | True  | True   | 1     |
|False | True  | True   | 0     |
|False | True  | True   | 1     |
|True | False  | True   | 0     |
|True | False  | True   | 1     |
|True | True  | False   | 0     |
|True | True  | False   | 1     |
|False | False  | True   | 0     |
|False | Flase  | True   | 1     |
|True | False  | False   | 0     |
|True | Flase  | False   | 1     |
|False | True  | False   | 0     |
|False | True  | False   | 1     |
|False | False  | False   | 0     |
|False | False | False   | 1     |
|�������� | �������� | �������� | �������� |
|���Գ��� | ���Գ��� | ���Գ��� | ���Գ��� |

�������ºݤˤϻȤ��ʤ����֤⤢�롣

��������ɽ�����Τ���ε��������ɤϰʲ��Τ褦�ˤʤ롣

```
# ������֡�����������֡����Գ������
start = 0
success = 1
fail = 2
# ���Υꥹ�Ȥ��äƤ���
exprlist = makeexplist()
# �ƹԤξ��֡����٤ƤιԤ�True�ˤ��ƽ����
rowstate = makerowstate()

expr_table = new Table()
success_table = new Table()
fail_table = new Table()
que = [(start, rowstate, exprlist[0])]
while que:
    state, rowstate, expr = que.popleft()
    # �Ԥ�������
    col = expr.col
    row = expr.row
    # ����ID�򼰷���ɽ�������
    expr_table[col, state] = expr.id
    # ���Ԥξ��
    # �������Ծ��֤����
    newrowstate = rowstate.fail(row)
    # ���Ԥ����Ԥ򤹤٤ư�������ǡ����μ���겼�����ˤ��뼰�򸡺�
    nexpr = exprlist.nextexpr(newrowstate, expr)
    if nexpr:
        # ���ߤιԾ��֤ȥ���ǥå������б����롢���������֤������
        nstate = new_state(rowstate, nexpr.index)
        # ���������֤��Ը�ξ��֤Ȥ���ɽ�˵����������塼�������
        # ���Ը�ξ��֤򥭥塼�������
        que.append((nstate, newrowstate, nexpr))
    else:
        # �����ʤ��Τǡ����Ը�ξ��֤ϼ��Գ�����֤Ȥʤ�
        fail_table[col, state] = fail

    # �����ξ��
    # Ʊ���Ԥǡ������걦�˼������뤫����
    nexpr = exprlist.findright(expr)
    if not nexpr:
         # ���ιԤˤ���ʾ弰���ʤ��Τ���������С���������Ȥʤ�
         success_table[col, state] = success
    else:
         # ����ɾ�����뼰��õ��
         # ���ߤιԾ��֤ǡ����μ���겼�����ˤ��뼰�򸡺�
         nexpr = exprlist.nextexpr(rowstate, expr)
         # ���ߤιԾ��֤ȥ���ǥå������б����롢���������֤������
         nstate = new_state(rowstate, nexpr.index)
         # ���������֤�������ξ��֤Ȥ���ɽ�˵����������塼�������
         success_table[col, state] = nstate
         que.append((nstate, rowstate, npos))
```
