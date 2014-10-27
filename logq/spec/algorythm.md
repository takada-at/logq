アルゴリズム
===============

## 条件の簡単化
検索条件はカラムに対する比較演算子と、and, or, notによって構成される。

```
(cols[1]=="hoge" or (cols[2]=="fuga" and cols[4]=="poyo")) or (cols[2]=="hogera" and cols[5]=="piyo")
```

logqでは、まずこの論理式を簡単化する。

第一段階では、1つ以上のand式が、orで結ばれた形にする。

```
(cols[1]=='hoge') or (cols[2]=='fuga' and cols[4]=='poyo') or (cols[2]=='hogera' and cols[5]=='piyo')
```

第二段階では、クワイン・マクラスキー法を適用し、さらなる簡単化を試す。

(詳細は省く)


## 条件式をテーブルに変換
この段階で条件式は、1つ以上のand式が、orで結ばれた形になっている。

以下の表の各行はand節に対応している。

|     |cols[1]|cols[2]|cols[4]|cols[5]|
|:----|:-----|:------|:-------|:------|
|条件1 |=hoge |       |        |       |
|条件2 |      |=fuga  |=poyo   |       |
|条件3 |      |=hogera|        | =piyo |

検索時は以下を実行すればいい。

* 各カラムに対応する式を探す。
* 式を実行する。
    * 失敗した場合
        * テーブルからその行を削除
        * すべての行が削除されれば、検索は失敗に終わる
    * 成功した場合
        * もしその式が行の最後の式であれば、検索は成功に終わる
        * 最後の式でなければ次の式を探す。なければ次のカラムへ

このアルゴリズムは以下のような3つの表として表現できる。

* 現在の状態×今読んでいるカラムから、適用すべき式を決定する表
* 現在の状態×今読んでいるカラムから、式が成功であった場合に遷移すべき状態を決定する表
* 現在の状態×今読んでいるカラムから、式が失敗であった場合に遷移すべき状態を決定する表

* 状態は以下の2つによって決まる
    * 各行の状態
        * 各行の式がひとつでも失敗すればFalse。まだ失敗していなければTrue。
    * カラムの何番目の式か
        * 状態×カラムによって、一意に適用すべき式が決まるようにするために、同じカラムに対して複数の式がある場合は別の状態を割りふる

例えば上の表は以下のような状態遷移になる。1は判定成功、2は判定失敗

※各セル内は、(式、成功後の状態、失敗後の状態)

|state |cols[1]    |cols[2]       |cols[4]       |cols[5]       |
|:-----|:----------|:-------------|:-------------|:-------------|
|0     |=hoge,[1],3|              |              |              |
|1     |           |              |              |              |
|2     |           |              |              |              |
|3     |           |=fuga,5,4     |=poyo,[1],4   |              |
|4     |           |=hogera,4,[2] |              |=piyo,[1],[2] |
|5     |           |=hogera,3,6   |              |=piyo,[1],[2] |
|6     |           |              |=poyo,[1],[2] |              |

![状態遷移]('algorythm.png')

## 状態遷移表のつくり方
検索条件から状態遷移表を作るアルゴリズムをまとめる。

|     |cols[1]|cols[2]|cols[4]|cols[5]|
|:----|:-----|:------|:-------|:------|
|条件1 |=hoge |       |        |       |
|条件2 |      |=fuga  |=poyo   |       |
|条件3 |      |=hogera|        | =piyo |

条件内のand節は3つある。また、cols[2]に適用すべき式が2つあるので、可能な状態の集合は以下のようになる。

|条件1 | 条件2 | 条件3   |式インデックス|
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
|成功確定 | 成功確定 | 成功確定 | 成功確定 |
|失敗確定 | 失敗確定 | 失敗確定 | 失敗確定 |

ただし実際には使われない状態もある。

状態遷移表作成のための疑似コードは以下のようになる。

```
# 初期状態、成功確定状態、失敗確定状態
start = 0
success = 1
fail = 2
# 式のリストを作っておく
exprlist = makeexplist()
# 各行の状態。すべての行をTrueにして初期化
rowstate = makerowstate()

expr_table = new Table()
success_table = new Table()
fail_table = new Table()
que = [(start, rowstate, exprlist[0])]
while que:
    state, rowstate, expr = que.popleft()
    # 行と列を取得
    col = expr.col
    row = expr.row
    # 式のIDを式決定表に入れる
    expr_table[col, state] = expr.id
    # 失敗の場合
    # 新しい行状態を作成
    newrowstate = rowstate.fail(row)
    # 失敗した行をすべて引いた上で、この式より下か右にある式を検索
    nexpr = exprlist.nextexpr(newrowstate, expr)
    if nexpr:
        # 現在の行状態とインデックスに対応する、新しい状態を作成。
        nstate = new_state(rowstate, nexpr.index)
        # 新しい状態を失敗後の状態として表に記入し、キューに入れる
        # 失敗後の状態をキューに入れる
        que.append((nstate, newrowstate, nexpr))
    else:
        # 次がないので、失敗後の状態は失敗確定状態となる
        fail_table[col, state] = fail

    # 成功の場合
    # 同じ行で、これより右に式があるか検索
    nexpr = exprlist.findright(expr)
    if not nexpr:
         # この行にこれ以上式がないので成功すれば、成功確定となる
         success_table[col, state] = success
    else:
         # 次に評価する式を探す
         # 現在の行状態で、この式より下か右にある式を検索
         nexpr = exprlist.nextexpr(rowstate, expr)
         # 現在の行状態とインデックスに対応する、新しい状態を作成。
         nstate = new_state(rowstate, nexpr.index)
         # 新しい状態を成功後の状態として表に記入し、キューに入れる
         success_table[col, state] = nstate
         que.append((nstate, rowstate, npos))
```
