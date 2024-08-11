import tkinter as tk
from tkinter import ttk #frameのため必要
from tkinter.font import Font
import pyperclip
# Import the pyperclip library
import unicodedata #全角文字列計算
import itertools #for p in itertools.permutations(testAry):を使うため
#icon作成用に
import sys
import os
#charWidth計算用
#import charAlphabetWidth
#以下は辞書型と呼ばれる変数　辞書(dict)　https://www.tohoho-web.com/python/list.html
#全ての要素や値を参照するには、items(), keys(), valus(), items() 
import charAlphabetWidth
#debug
#import time

#文字幅、全角は固定で@と同じ長さから少しだけ小さい値にする、その他は上記辞書から
#改行文字にあたる半角スペースと半角ハイフンは真っ当な詠唱の時はどうも長さ０になってそう
ZENKAKU_WIDTH = 4093
MAX_LINE_WIDTH = 100000 #全角文字1行24文字、半角の@が1行24文字、全角が改行文字の都合上、大きさぶれてそう

#定数
NEWLINE1_POSION_LEN = 1
#おそらく65文字以上から謎の見切れが発生するはず
CHECK_LENGTH1 = 65
#10行まで調査対象とする。11行目以降は判定しないし、警告も出す。文字長限界は100　実際は意味ある構成101文字もできたがレアケースなので考慮しない
MAX_LINE = 10
MAX_LENGTH = 105 #ver2.7から限界突破考慮して105までに
#Modifyボタン押下時の組み換えの点数方式
FIRST_NEWLINE_SPACE = 4
FIRST_NEWLINE_ZENKAKU = 3
FIRST_NEWLINE_HOSEI = 2
FIRST_NEWLINE_CONMMA = 1
FIRST_NEWLINE_MIKIRE = 0 #調整はできるパターンはあったが、見切れた場合
#処理を何がしか抜けたい時の文言
SKIP = "SKIP"
#改行可能文字は、2023/10/01 半角スペース とマイナス棒- 全角文字より全角スペースと全角ハイフン‐
NewLineTP = (' ','-')
NEWLINE_MARK_NOT = 0
NEWLINE_MARK_HANKAKU = 1
NEWLINE_MARK_ZENKAKU = 2
NEWLINE_MARK_HANKAKU_SPACE = 3

#共通変数
#ボタンを押すたびにコロコロ画面が動いていたのでボタン押下直後の画面サイズを記録し
#処理終了後にサイズをセットして、画面再構成することで、画面がちらついたり、動かなくなった
#root.resizableも試したが、画面がちらついたので却下
wWidth = 0
wHeight = 0
#前の値を保存しておくtext changeやmodifyなどで突っ込まれる予定
bk_user_input = ""
finalFirstPos = 0
finalMikire = 0
combDelimiter = ","
combModify = 0
user_inputLength = 0

#def redo(event=None):
#Ctrl+yでRedo
#txt.edit_redo()
#redoは使用回数制限とか、redo出来ないときのエラー調整必要
def on_clear():
    keepWindowSize()
    txt.delete(1.0, tk.END)
    label_memo.config(text=f"詠唱を消去しました", foreground="black")
    button_modify['state'] = tk.NORMAL
    for tag in txt.tag_names():
     txt.tag_delete(tag)
    #文字数0固定
    label_charcount.config(text=f"入力文字数:0", foreground="black")
    label_widthcount.config(text=f" 1行目文字幅:0", foreground="black")
    label_widthcount2.config(text=f" 2行目文字幅:0", foreground="black")
    keepWindowSize()

def copy_to_clipboard():
    keepWindowSize()
    user_input = txt.get(1.0, tk.END)
    pyperclip.copy(user_input.replace("\n", ""))
    label_memo.config(text=f"クリップボードへコピーしました。なお改行は全て削除してコピーしています", foreground="black")
    #改行はこれで排除できるが、\nを実際に打ちたい場合はそれも巻き添えになる
    keepWindowSize()

def changeAuto(event=None):
    #実際に作業するとしたらon_text_changeと同じ処理になる
    #あのメソッドはテキスト内容が変わっていないと動作しないので、強制的に動かすようにする
    on_text_change(chkbox.get())
    
#自動補正の状態を見て補正する
#補正内容はシンプルに、単語の途中の全角文字が見切れ位置となり、その位置の１文字先が見切れ文字ではない場合や区切り文字ではない場合
#区切り文字の１つ先などに改行位置を挿入したほうが実際のゲームで入力しやすかったので、自動補正機能を作った。
#半角スペースを見切れ位置のすぐあとに入力して、見切れ位置を自動調整する
#補正できる場合は補正した値、補正できない場合は引数で受け取った値をそのまま返す
#posの次の文字が見切れ文字であるかを判定して、文字幅限界の適切な区切り位置を返す
def getAutoModDelimiterIdx(pos,body):
    #postの位置が本文より先にある場合は処理をしない
    body = Zenkaku(body)
    if lengthDoubleByteStr(body) <= pos + 2:
        return 0
    
    #次の区切り位置までIndexを勧めて、文字幅を確認する
    workBody = Zenkaku(body[pos:])
    delimiter = delimiter_dict.get(combobox_delimiter.get(),",")
    
    #そもそも残っている文字列に区切り文字がないなら本件の補正はできない
    delimiterCount = workBody.count(delimiter)
    if delimiterCount == 0:
        return 0
    
    #チェックは後ろから行う
    for i in range(len(workBody)-1, -1, -1):
        #全角文字との兼ね合いでfindが取得するIndexと実際の値がずれる。
        #なので１文字ずつ読み込んだ文字が区切り文字であるか判断して、文字幅チェックをする
        if workBody[i] == delimiter:
            #debug
            #print(f"in delimiter:{body[pos + i + 1]}")
            if MAX_LINE_WIDTH > strWidth(body[:pos + i + 2]) and body[pos + i + 1] == delimiter:
                #debug
                #print(f"body[:pos + i + 2]:{body[:pos + i + 2]}")
                return i + 2
            if MAX_LINE_WIDTH > strWidth(body[:pos + i + 1]):
                #debug
                #print(f"body[:pos + i + 1]:{body[:pos + i + 1]}")
                return i + 1
            
    #該当する区切り位置がなかったり、区切り位置がそもそもない場合は補正０で返す
    return 0
    
def on_modify():
    global bk_user_input
    global finalFirstPos
    global finalMikire
    global combDelimiter
    global combModify
    global user_inputLength
    #熟語「short hair」などをカンマ','で区切って認識し、文字を入れ替える
    keepWindowSize()
    user_input = txt.get(1.0, tk.END) #tkinterのTextのgetはIndex指定しないと取れない
    bk_user_input = user_input
    #ボタンやラベル、タグを初期化
    label_memo.config(text=f"", foreground="black")
    button_modify['state'] = tk.DISABLED
    input_length = lengthDoubleByteStr(user_input.replace("\n", ""))
    user_inputLength = input_length
    label_charcount.config(text=f"入力文字数:{input_length}", foreground="black")
    label_widthcount.config(text=f" 1行目文字幅:Error", foreground="black")
    label_widthcount2.config(text=f" 2行目文字幅:Error", foreground="black")
    if input_length <= CHECK_LENGTH1:
        label_memo.config(text=f"{CHECK_LENGTH1+1}文字以上が修正対象となります。そのままテキストを使用してください", foreground="red")
        keepWindowSize()
        return

    #タグは再作成するので毎回削除
    for tag in txt.tag_names():
     txt.tag_delete(tag)

    user_input_no_line = user_input.replace("\n", "")
    #初期化
    firstPosition = 0
    secondPosition = 0
    #combobox_modifyから現在地を取得
    fixedWordCount = combModify
    #見切れ文字を何にするか取得 何らかのエラーで辞書から取得できない時は半角カンマにする
    delimiter = combDelimiter
    #debug
    #print(f"combModify:{combModify}")
    #print(f"delimiter:{delimiter}")
    #区切り文字は最初の入力テキストを配列分割するときしか使わず
    #それ以降は全て','で区切りを置き換える。これは文字列幅の関係上、そうなる

    #目的は65文字以下、85文字以下の２パターンで語順を変えたりして、
    #特定文字位置に半角スペースや全角文字が来るように自動調整する
    #fixedWordCountに入れた熟語数分を先頭に固定して、その他を入れ替える
    #熟語はカンマ区切りで判定するのでshort hairなども１熟語扱いとする
    #全角文字なども意味ある熟語は必ず半角カンマ区切りであることを仕様とする
    tempAry = user_input_no_line.split(delimiter)
    #熟語数が少なすぎる場合はエラー、最低３つ
    if len(tempAry) <= 2:
        label_memo.config(text=f"詠唱の熟語数が少なすぎます。区切り文字を見直してください", foreground="red")
        keepWindowSize()
        return
    #固定したい熟語数対して、2つ以上熟語がなければエラー
    if len(tempAry) <= fixedWordCount + 1:
        label_memo.config(text=f"固定したい熟語数に対して、入れ替え可能な熟語数が少なすぎます", foreground="red")
        keepWindowSize()
        return
    #配列化した後、単語前後にある半角スペースや全角スペースはトリムする。単語中央はトリムしない
    #使うときは再びカンマ付文字に戻すのと全角混じり文字を計算できるようにと、
    #全角文字混じりで文字を取得できるようZenkakuクラスを導入して突っ込む
    #２次元目の配列の値は(Zenkakuクラス文字列、全角を考慮した文字長数)という構成
    totalLength = 0
    for n in range(len(tempAry)):
     temp = str.strip(tempAry[n])
     tempLength = lengthDoubleByteStr(temp)
     tempAry[n] = temp
     totalLength += tempLength + 1
    totalLength -= 1 #最後の文字列にはカンマをつけないので削る
    #以下はスペース補正が何回できるか計測
    spaceCount = MAX_LENGTH - totalLength
    #文字列を構成していく、まずは固定文字列がある場合はそれを除外する
    fixed_body = ""
    #固定単語に指定されたものは配列から削除する
    for x in range(fixedWordCount-1,-1,-1):
        #逆順で削除しないと配列が詰まるバグが怖いので
        fixed_body = tempAry.pop(x) + ',' + fixed_body #値を取得しつつ削除
    #固定長の文字列が文字幅限界を超えたら、警告
    width = strWidth(fixed_body)
    if isinstance(width,int) == False:
        label_memo.config(text=f"「{width}」は本ツールで使用できない文字となります", foreground="red")
        keepWindowSize()
        return
    if width >= MAX_LINE_WIDTH:
        label_memo.config(text=f"固定したい熟語の合計文字幅が長すぎます。テキストの調整をお願いします", foreground="red")
        keepWindowSize()
        return
    #0やマイナスになった場合は語順入れ替えしかできない
    #49文字目に半角スペースが入るよう調整する
    #アルゴリズムはまず、先頭側の文字列を足していき、都合よく該当文字位置が半角スペースや全角文字になるかを判定していく
    #それが見つからない場合はカンマで区切れるか探す
    #上記で見つからない場合は調整不可能としてエラー
    #それらチェックを終えたら、文字幅チェックを行う。文字幅チェックに引っかかったら、1行目は単語を1つ分、2行目に押し付ける
    #2行目が文字幅オーバーした場合は、単語区切り位置から見切れる
    #処理順は以下
    #1.語順を入れ替えるだけで、都合よく単語＋単語の区切りの真ん中スペースで入るものがあるか探す
    #2.全角文字が都合よく入るパターンがないか
    #3.半角スペースで調整して入らないか。もしここで調整できないなら、調整の結果、入るパターンがなかったと警告文字
    #itertools.permutationsで先に全文字列パターンを生成する方法でやったほうがわかりやすいので
    #時間はかかるがやってみる
    #候補を格納する配列を用意
    #検索で面倒を避けたいので1次元配列を3つ用意して疑似3次元配列扱いにする
    #最初に語順入れ替えだけで見きれない、改行位置を探したものを確保する
    #また見切れるパターンしかない場合は、元の詠唱をそのまま使ったパターンで見切れを表現できるようにする
    candidateStr = "" #詠唱を格納
    candidateRank = -1 #優先度のランクを格納、高い値が優先、同率順位の場合は先に格納された方を優先
    #点数を割り当てる方式にして、より高い点数が最終候補になるようにする
    #第一改行位置に半角があるが最高点
    #次が全角文字
    #どちらもなければ、カンマがあること
    #どれもなければ修正不可能としてエラー
    modUserInput = str.strip(fixed_body + ','.join(tempAry))
    #あとで使うため、現在の文字幅を取得する
    modUserWidth = strWidth(modUserInput)
    #先に半角スペースや全角文字があるか確認。そうしないとカンマのみの時に膨大な配列を処理して積む
    #半角スペースが見つからない場合は全角文字を探す
    isAllConmma = True #カンマフラグ、改行地点がカンマしか候補がないとき True
    for char in modUserInput:
        #全角文字などの２バイト文字は'F','W','A'のいずれかに当てはまるとする
        if chkNewLineChar(char) > NEWLINE_MARK_NOT:
            isAllConmma = False
            break
    #まずご順入れ替えだけで、改行文字に当たるか確認する
    #debug
    #start = time.time()
    #count = 0
    if isAllConmma == False:
        workOverWidthAry = []
        for y in itertools.permutations(tempAry):
            #文字列の組み合わせから改行位置を探る
            #一行目から探して、適切な位置が見つかるか探す。見つからない場合は0で帰ってくる
            #マイナス数値で帰ってきたら計測できない文字が帰ってきたことになるので警告して終わり
            all_body = str.strip(fixed_body + ','.join(y))
            zenkakuStr = Zenkaku(all_body)
            preFirstPosition = getLimitWidthPosition(zenkakuStr,MAX_LINE_WIDTH,modUserWidth)
            if preFirstPosition == 0:
                continue
            firstLine = zenkakuStr[:preFirstPosition+1] #sliceのときは 0index:数値の手前のindex　で斬るので、indexとしてのfirstPositionは+1する
            #既に計測済みの改行位置、文字列で見切れパターンだったら以後の処理はしない
            if firstLine in workOverWidthAry:
                #debug
                #print(f"alreadyChk1:{firstLine}")
                #count += 1
                continue
            #tupleでデータを貰う
            firstTp = reAdjustNewLinePosition(firstLine,preFirstPosition)
            #firstPosition = reAdjustNewLinePosition(firstLine,firstPosition)
            if firstTp[0] == 0:
                continue
            #2行目が閾値を超える文字幅にならなかったらOK
            if modUserWidth - firstTp[1] < MAX_LINE_WIDTH:
                firstPosition = firstTp[0]
                #見切れがなかったら、即時有効と判断して抜ける
                candidateStr = zenkakuStr
                if zenkakuStr[firstPosition] in NewLineTP:
                    candidateRank = FIRST_NEWLINE_SPACE
                else:
                    candidateRank = FIRST_NEWLINE_ZENKAKU
                break
            #見切れパターンの文字列は記録しておき、同じパターンは以後も見切れるとして飛ばす
            workOverWidthAry.append(zenkakuStr[:preFirstPosition+1])
        #for y in itertools.permutations(tempAry):
    #if isAllConmma == False:
    #語順入れ替えで終わっている、見切れているもの以外があるなら計算不要
    #何も問題が無いときは以下で通り、tempBodyだけ修正した内容に変わる
    finalRank = -1
    finalBody = user_input_no_line
    if FIRST_NEWLINE_SPACE == candidateRank or FIRST_NEWLINE_ZENKAKU == candidateRank:
        finalRank = candidateRank
        finalBody = candidateStr
    else:
        #単純な語順入れ替えで終わらないなら以下対応
        #１．カンマしか区切りを認識できないなら、補正できるか確認
        #２．カンマ以外の区切りがあるなら先にそちらをスペース補正して入るか確認
        #そもそも補正できないなら終わり
        if spaceCount > 0:
            workOverWidthAry = []
            #ここから先は保存する必要がないので、配列を格納せず、変数に単純文字列などで保存する
            for z in itertools.permutations(tempAry):
                #文字列joinで半角スペースが入るパターンを探す
                wordBody = fixed_body + ",".join(z)
                wordBody = Zenkaku(wordBody) #最後が半角カンマなので必ず削除する
                preFirstPosition = getLimitWidthPosition(wordBody,MAX_LINE_WIDTH,modUserWidth)
                if preFirstPosition == 0:
                    continue
                #既に計測済みの改行位置、文字列で見切れパターンだったら以後の処理はしない
                if wordBody[:preFirstPosition+1] in workOverWidthAry:
                    #debug
                    #print(f"alreadyChk2:{wordBody[:preFirstPosition+1]}")
                    #count += 1
                    continue
                #半角スペースを入れるべき、半角カンマを探す
                conmmaPos = 0
                for i in range(preFirstPosition,1,-1):
                    #，位置を探す。findだと、Zenkakuクラスの位置からずれるので
                    if wordBody[i] == ",":
                        conmmaPos = i
                        break
                #conmmaPosの最初の位置の後に、半角スペースを挿入して、見切れ検証を行う。ただしカンマがない場合は飛ばす
                if conmmaPos == 0:
                    continue
                #conmmaPosから半角スペースを挿入する。改行位置はカンマ後にずれるので、それも補正
                firstPosition = conmmaPos+1
                firstLine = wordBody[:conmmaPos+1] + ' '
                #文字幅計算して一旦、超えてなければ見切れ判定まで行う
                if modUserWidth - strWidth(wordBody[:conmmaPos+1]) < MAX_LINE_WIDTH:
                    secondLine = wordBody[conmmaPos+1:]
                    finalBody = firstLine + secondLine
                    if isAllConmma:
                        finalRank = FIRST_NEWLINE_CONMMA
                    else:
                        finalRank = FIRST_NEWLINE_HOSEI
                    break   
                #見切れパターンの文字列は記録しておき、同じパターンは以後も見切れるとして飛ばす
                workOverWidthAry.append(wordBody[:preFirstPosition+1])       
             #for z in itertools.permutations(tempAry):
    #finalRankに値が入らない場合は見切れパターンしかなかったことになるので、修正候補なしで抜ける
    #debug
    #print(f"count:{count}")
    #end = time.time()
    #time_diff = end - start  # 処理完了後の時刻から処理開始前の時刻を減算する
    #print(time_diff)  # 処理にかかった時間データを使用
    message = "詠唱の修正が終了しました"
    color = "black"
    if FIRST_NEWLINE_SPACE == finalRank:
        message = "スペースまたはハイフンを区切りにして、" + message
    elif FIRST_NEWLINE_ZENKAKU == finalRank:
        message = "全角文字を区切りにして、" + message
    elif FIRST_NEWLINE_HOSEI == finalRank:
        message = "語順入れ替えと半角スペースで補正して、" + message
    elif FIRST_NEWLINE_CONMMA == finalRank:
        message = "語順入れ替えと区切り文字に半角スペースで補正して、" + message
    else:
        message = "修正候補が見つかりませんでした。入力するテキストを調整してください"
        color = "red"
    #チェックは終わったので結果を更新する
    label_memo.config(text=message, foreground=color)
    txt.delete(1.0, tk.END)
    button_modify['state'] = tk.NORMAL
    #文字数計算はアクションごとに行う
    input_length = lengthDoubleByteStr(finalBody)
    label_charcount.config(text=f"入力文字数:{input_length}", foreground="black")
    if finalRank > -1:
        txt.insert(0., finalBody)
        checkTextNewline(finalBody + '\n', lengthDoubleByteStr(finalBody), firstPosition, 0)
    else:
        #改行されていた場合は入れ直しが面倒、一旦何行目にプットするかをsplit使って捌く
        tempLineAry = bk_user_input.split('\n')
        maxLen = len(tempLineAry) if len(tempLineAry) < MAX_LINE else MAX_LINE
        txt.insert(0., tempLineAry[0])
        for i in range(1,maxLen):
            #tempLineAry[i] = tempLineAry[i].strip()
            #debug
            #print(f"tempLineAry[i]:{tempLineAry[i]}")
            if len(tempLineAry[i]) > 0:
                #txtLineNum = 1.0 + i
                #２行目からの挿入はtxt.insert(2.0,text)と打っても入らず、すでに２行目がないとできないので代わりの入れ方をする
                #https://teratail.com/questions/333059
                txt.insert('end','\n'+tempLineAry[i])#二行目に挿入したい
        checkTextNewline(bk_user_input, lengthDoubleByteStr(bk_user_input), finalFirstPos, finalMikire)
    #2023/11/23 1行目の文字幅を計測して表示
    label_widthcount.config(text=f" 1行目文字幅:{strWidth(finalBody[:firstPosition+1])}", foreground="black")
    label_widthcount2.config(text=f" 2行目文字幅:{strWidth(finalBody[firstPosition+1:-1])}", foreground="black")
    keepWindowSize()
    bk_user_input = finalBody
    user_inputLength = input_length
    #debug
    #print(f"finalRank:{finalRank}")
    #print(f"firstLine:{finalBody[:firstPosition+1]}")
    #print(f"firstLineW:{strWidth(finalBody[:firstPosition+1])}")
    #print(f"secondLine:{finalBody[firstPosition:]}")
    #print(f"secondLineW:{strWidth(finalBody[firstPosition:])}")

#文字幅限界から、適切な改行位置まで後退する
#def reAdjustNewLinePosition(body,index,debug=False):
def reAdjustNewLinePosition(body,index):
    #改行位置を文字幅計算も含めて取り出す
    #body 対象文字列 受け取り後即時Zenkakuクラスにする
    #index 改行チェックをする起点
    #戻り値はtupleでIndexと文字幅を返す
    body = Zenkaku(body)
    position = index
    #positionがbodyのLenより小さくない場合は補正
    if lengthDoubleByteStr(body) <= index:
        position = lengthDoubleByteStr(body) - 1
    for i in range(position,1,-1):
        #if debug:
            #print(f"reAdjustChar:{body[i]}:")
        #改行位置以外では計測しない
        mark = chkNewLineChar(body[i])
        if mark > NEWLINE_MARK_NOT:
            #改行位置が見つかったらそこで確認、半角系改行文字は自分の幅を無視して計算
            tempWidth = strWidth(body[:i+1])
            if mark == NEWLINE_MARK_HANKAKU_SPACE:
                if tempWidth - charAlphabetWidth.ALPHABET.get(body[i]) < MAX_LINE_WIDTH:
                    return (i,tempWidth)
            else:
                if tempWidth < MAX_LINE_WIDTH:
                    return (i,tempWidth)
    #切れ目がなかったら計測不能
    return (0,0)

def getLimitWidthPosition(body,limitWidth,tempWidth):
    #文字幅合計の適切な位置まで文字列を進める
    #bodyに文字列。原則、この関数には文字幅合計を超えた文字列しか来ない
    body = Zenkaku(body)
    length = lengthDoubleByteStr(body)
    #limitWidthを下回るまで後退する
    zFlg = False #全角フラグ、全角は２Indexで1つの文字なので
    for i in range(length-1,1,-1):
        if zFlg:
            zFlg = False
            continue
        #文字列最後が改行文字の場合は含めず文字幅計算
        #2023/11/04 どうも半角スペース以外は改行位置の文字を計算に含めていそう
        mark = chkNewLineChar(body[i])
        if mark > NEWLINE_MARK_NOT:
            if mark == NEWLINE_MARK_HANKAKU_SPACE:
                tempWidth -= charAlphabetWidth.ALPHABET.get(body[i])
            if tempWidth < limitWidth:
                return i
            if mark == NEWLINE_MARK_HANKAKU:
            	tempWidth -= charAlphabetWidth.ALPHABET.get(body[i])
            if mark == NEWLINE_MARK_ZENKAKU:
                tempWidth -= ZENKAKU_WIDTH
                zFlg = True
        else:
            if tempWidth < limitWidth:
                return i
            tempWidth -= charAlphabetWidth.ALPHABET.get(body[i])
    return 0

def strWidth(body):
    #bodyは普通のstring lengthDoubleByteStr
    #計測できない文字がきたら文字列で返す
    total = 0
    body = Zenkaku(body)
    length = lengthDoubleByteStr(body)
    zFlg = False #全角フラグ、全角は２Indexで1つの文字なので
    hankakuCharAry = []
    for i in range(0,length):
        if zFlg:
            zFlg = False
            continue
        #全角文字だった場合はチェックできない
        #dictの中に入っていないものは文字幅測定できない
        #取得はget関数　d.get('key4', 100)　存在しないKeyの場合は第ニ引数100が戻る
        if unicodedata.east_asian_width(body[i]) in 'FWA':
            total += ZENKAKU_WIDTH
            #全角の場合はフラグON
            zFlg = True
        else:
            #同じ文字列で全角以外はまとめて計算させる
            #全角文字は無視可能なので、先にcount機能で計算する
            #getでFalseで帰ってきたら新規登録
            if body[i] in hankakuCharAry:
                continue
            else:
                hankakuCharAry.append(body[i])
    #溜まった半角も自分、検索を行って、倍加計算する
    for char in hankakuCharAry:
        width = charAlphabetWidth.ALPHABET.get(char,False)
        if width == False:
            return char #想定外の半角英数記号が来てしまった場合は文字そのままで返す
        total += width * body.count(char)
        #debug
        #print(f"width:{width}")
        #print(f"count:{body.count(char)}")
    return total

def on_text_change(event=None):
    global bk_user_input
    global finalFirstPos
    global finalMikire
    global user_inputLength
    user_input = txt.get(1.0, tk.END) #tkinterのTextのgetはIndex指定しないと取れない
    if event != True: #Trueが入っている場合は強制的に処理をする
        if user_input == bk_user_input:
            return
    finalFirstPos = 0
    finalMikire = 0
    #ボタンやラベル、タグを初期化
    label_memo.config(text=f"", foreground="black")
    button_modify['state'] = tk.DISABLED
    #タグは再生性するので毎回削除
    for tag in txt.tag_names():
     txt.tag_delete(tag)

    #改行は2文字判定となっているが、Ai Art Impostorで貼付け時は基本、改行していないので、全部はずす
    #弊害として、ユーザーが改行したいと意識して入れた文字まではずしちゃう
    user_input_no_line = user_input.replace("\n", "")
    input_length = lengthDoubleByteStr(user_input_no_line)
    user_inputLength = input_length
    #文字数計算はアクションごとに行う
    label_charcount.config(text=f"入力文字数:{input_length}", foreground="black")
    label_widthcount.config(text=f" 1行目文字幅:Error", foreground="black")
    label_widthcount2.config(text=f" 2行目文字幅:Error", foreground="black")
    chkChar = strWidth(user_input_no_line)
    if isinstance(chkChar,int) == False:
        label_memo.config(text=f"「{chkChar}」は本ツールで使用できない文字となります", foreground="red")
        keepWindowSize()
        bk_user_input = user_input
        return
    input_length = lengthDoubleByteStr(user_input_no_line)
    user_inputLength = input_length

    #入力文字数が改行除いてMAX_LENGTH文字超えになっていた場合は以後の処理をせず、メッセージでユーザーへ処理を促す
    #逆にチェックするほどの文字数量ではないため、以降の処理を飛ばす
    if input_length <= CHECK_LENGTH1:
        bk_user_input = user_input
        return
    if input_length > MAX_LENGTH:
        label_memo.config(text=f"文字数が{input_length}です。{MAX_LENGTH}文字以下にしてください", foreground="red")
        bk_user_input = user_input
        return
    #2023/10/14 text change にmodifyボタンの機能を移動　初期入力の見切れはこちらで判定する
    #最終的な改行位置を控える
    rawFirstPosition = 0
    rawSecondPosition = 0
    #現在入力済みのテキストのままで、条件を満たせるか確認する
    #条件を満たせたら、以後のチェックはせず終了
    #1行目の改行位置の起点は文字列長半分、改行位置は50文字目を中心に前後2文字くらいなので＋補正をする
    #そのまま計算するので、改行以外はそのままにする
    #2023/10/14 改行位置について、どうあがいても文字列半分でもないし、
    #これは文字幅の長さでぶった切っている？　あと全角文字も０幅としてカウントいているかな？
    #検証すると限界文字幅までまず1行目が確保したのち、2行目が決まっていそう
    #その時、ぶったぎったところが改行文字でなければ後ろにずれる形のようだ
    userWidth = strWidth(user_input_no_line)
    #debug
    #print(f"rawUserWidth:{userWidth}")
    rawFirstPosition = getLimitWidthPosition(user_input_no_line,MAX_LINE_WIDTH,userWidth)
    #debug
    #print(f"rawFirstPos:{rawFirstPosition}")
    rawZenkakuStr = Zenkaku(user_input_no_line)
    rawFirstLine = rawZenkakuStr[:rawFirstPosition+1]
    firstTp = reAdjustNewLinePosition(rawFirstLine,rawFirstPosition)
    rawFirstPosition = firstTp[0]
    firstWidth = firstTp[1]
    
    #ここで自動補正がONの場合、補正するかどうか検討する
    if chkbox.get():
        hoseiPos = getAutoModDelimiterIdx(rawFirstPosition,rawZenkakuStr)
        if hoseiPos > 0:
             #改行位置をずらした位置に半角スペースを挿入 挿入した関係で他の文字もずれるので修正する 面倒だがこの処理に入った時点で１つまたは２つずれる。
             #だがスペースを挿入する位置は元の区切り位置のインデックスから操作するので、１つずれる場合は元のインデックスそのままでカットして、２つずれる場合はそれに＋１される状態にしないといけない
             rawFirstPosition = rawFirstPosition + hoseiPos
             user_input = rawZenkakuStr[:rawFirstPosition] + " " + rawZenkakuStr[rawFirstPosition:] + "\n" #後処理の都合でどうしても改行を２回入れる必要がある
             user_input_no_line = user_input.replace("\n", "")
             userWidth = strWidth(user_input_no_line)
             firstWidth = strWidth(rawZenkakuStr[:rawFirstPosition])
             input_length = lengthDoubleByteStr(user_input_no_line)
             user_inputLength = input_length
             txt.delete(1.0, tk.END)
             txt.insert(1.0, user_input)
             
    keepWindowSize()
    if rawFirstPosition > 0:
        #最初期の位置が取れたら計算する
        secondLine = rawZenkakuStr[rawFirstPosition+1:]
        #文字列全体で文字幅限界を超えないなら、即時OKで計測不
        secondLength =lengthDoubleByteStr(secondLine)
        rawSecondPosition = secondLength - 1
        if userWidth - firstWidth < MAX_LINE_WIDTH:
            #見切れも発生していないので、このままOK
            label_memo.config(text=f"入力したテキストのままで問題ございません", foreground="black")
            checkTextNewline(user_input, input_length, rawFirstPosition, -1)
        else:
            secondTp = reAdjustNewLinePosition(secondLine,rawSecondPosition)
            finalMikirePos = rawFirstPosition + secondTp[0] + 1
            message = f"{finalMikirePos}文字以降の文字列は見切れる予測です。"
            label_memo.config(text=message, foreground="red")
            pythonIndex = -1
            properIndex = -1
            for char in rawZenkakuStr:
                pythonIndex += 1
                if unicodedata.east_asian_width(char) in 'FWA':
                     hoseiCount = 2
                elif char == "\n":
                     hoseiCount = 0
                else:
                     hoseiCount = 1
                properIndex += hoseiCount
                if properIndex >= finalMikirePos:
                    finalFirstPos = rawFirstPosition
                    finalMikire = pythonIndex
                    break
            #checkTextNewline(rawZenkakuStr + '\n', lengthDoubleByteStr(rawZenkakuStr), finalFirstPos, finalMikire)
            checkTextNewline(user_input + '\n', lengthDoubleByteStr(rawZenkakuStr), finalFirstPos, finalMikire)
        button_modify['state'] = tk.NORMAL
        label_widthcount.config(text=f" 1行目文字幅:{firstWidth}", foreground="black")
        label_widthcount2.config(text=f" 2行目文字幅:{userWidth - firstWidth}", foreground="black")
    else:
        label_memo.config(text=f"見切り判定できません。テキストを修正またはModifyを押して調整してください", foreground="red")
    bk_user_input = user_input
    keepWindowSize()

def selected_delimiter_change(event):
    global combDelimiter
    if combDelimiter != delimiter_dict.get(combobox_delimiter.get(),","):
        if user_inputLength > CHECK_LENGTH1:
            combDelimiter = delimiter_dict.get(combobox_delimiter.get(),",")
            button_modify['state'] = tk.NORMAL

def selected_modify_change(event):
    global combModify
    if combModify != module_fixed[int(combobox_modify.get())]:
        if user_inputLength > CHECK_LENGTH1:
            combModify = module_fixed[int(combobox_modify.get())]
            button_modify['state'] = tk.NORMAL

def checkTextNewline(user_input, input_length, firstChk, secondChk):
    #他のボタンからも処理を必要としたため、関数化
    #戻り値はなし、処理の結果は実際のwidgetに反映させる
    # 50文字を超える長さの場合は文字切れが起きるのでチェックする
    # Pythonを通常通り使うとIndexは1文字、全角半角区別せず1文字となっているので、
    # Ai Art Impostor向けでは全角は2文字判定しないといけないので、独自に計測が必要となる

    #改行が11以上あった場合は処理が難しくなるので、エラーとする。同時に各行がPythonベースで何文字ずつあるか計測、控えておく
    #再帰関数で作成しても良いが、そもそも10行も詠唱で使うことがない
    #secondChkに-1が入った場合はModifyからの処理ではないので、改行チェックを行う
    linesCountAry = [0,0,0,0,0,0,0,0,0,0]
    linesCount = -1
    linesIndexCount = -1
    indexCount = -1
    
    for char in user_input:
        indexCount += 1
        linesIndexCount += 1
        #最後の文字まできたら追加して終わり
        if len(user_input) == indexCount:
            linesCount += 1
            linesCountAry[linesCount] = linesIndexCount + 1
            break
        if char == "\n":
            linesCount += 1
            if linesCount >= MAX_LINE:
                label_memo.config(text=f"行は10行までにしてください", foreground="red")
                button_modify['state'] = tk.DISABLED
                return
            linesCountAry[linesCount] = linesIndexCount + 1
            linesIndexCount = -1 #改行されたので行頭に戻る意味も込めて-1
    
    #改行をはずして、全角を2文字としてカウントして、おそらく65文字以上の場合は改行位置確認の処理を入れたほうが良い
    if input_length > CHECK_LENGTH1:
        #ひとまず全角文字、半角文字、そして改行を区別しつつ適切なIndex位置を探すため文字カウントを増やしていく
        #pythonの通常lenによる改行も1文字扱いだった
        #最初は0Indexなので、加算方式のループ似合わせて、－１をセットする
        properIndex = -1
        #同時に通常PythonのIndex位置も現在、どこかカウントしていく
        pythonIndex = -1
        #改行位置の起点控える、常に小さいほうで保存
        delimiter1StartIndex = 0
        delimiter1EndIndex = 0
        #delimiter2StartIndex = 0
        #delimiter2EndIndex = 0
        #補正した値が半角なら１、全角なら２、改行は0とする
        hoseiCount = 0
        for char in user_input:
            pythonIndex += 1
            if unicodedata.east_asian_width(char) in 'FWA':
                hoseiCount = 2
            elif char == "\n":
                hoseiCount = 0
            else:
                hoseiCount = 1
            properIndex += hoseiCount
            #properIndex側が規定カウントに達したら控えておく、すでに計測済みだったら飛ばす
            if delimiter1StartIndex == 0 and properIndex >= firstChk:
                delimiter1StartIndex = pythonIndex
            if delimiter1EndIndex == 0 and properIndex >= firstChk + NEWLINE1_POSION_LEN:
                delimiter1EndIndex = pythonIndex
                #tuple型で適切な行数、Index位置を受け取る
                tp = calculateLineCount(linesCountAry,delimiter1StartIndex,delimiter1EndIndex,NEWLINE1_POSION_LEN)
                txt.tag_add("color1", formatTextTagIndex(tp[1],tp[0]), formatTextTagIndex(tp[3],tp[2]))
                #txt.tag_config("color1", foreground="red")
                txt.tag_config("color1", background="red")
                break
        if secondChk > 0:
            tp = calculateLineCount(linesCountAry,secondChk,len(user_input),len(user_input))
            txt.tag_add("color3", formatTextTagIndex(tp[1],tp[0]), formatTextTagIndex(tp[3],tp[2]))
            txt.tag_config("color3", background="yellow")

def formatTextTagIndex(index,line):
    #tag_addのindexはFloatやDoubleなのだが、その文字数値の扱いがきつい
    #スタートが1.09と書かれて、エンドが10文字目だった場合 1.10となっている場合は良いが
    #1.00と1.06という書き方の場合、6文字目という認識にならず、エラーとなってしまうので、終わりが二桁になっていない場合は
    #どちらも一桁表記に変える
    #戻り地はtupleでstartIndexとendIndexを適切に加工する
    temp = ""
    if index < 10:
        temp = "{:.1f}".format(index * 0.1 + line)
    else:
        temp = "{:.2f}".format(index * 0.01 + line)
    return temp

def calculateLineCount(lines, pythonStartIndex, pythonEndIndex, hosei):
    #linesにはテキストに入力された行ごとのPythonから見た文字列最大長が格納されている
    #pythonIndexはパイソンのlenを使った時の文字長さに応じた、Indexとなる
    #ここからpythonIndexの値を満たす適切な行数を割り出す
    #適切な行数を割り出せたら行内の何番目になるか計算する
    #なお、StartとEndの行数がまたがる状態の場合も対応できるようにする
    tempTotalLength = 0
    startLine = 0
    startIndex =  0
    endLine = 0
    endIndex = 0
    for n in range(0,MAX_LINE):
        tempTotalLength += lines[n]
        if tempTotalLength >= pythonStartIndex and startLine == 0:
            startLine = n + 1
            #文字長は超えたので、次にpythonIndexが該当行のどこから始まるかも計測する
            startIndex = pythonStartIndex - (tempTotalLength - lines[n])
        if tempTotalLength >= pythonEndIndex:
            endLine = n + 1
            #startとendが同じ行だった場合は、startからendの値を計算できる
            if startLine == endLine:
                #endIndexが行末と同じだと改行になってしまうので-1する
                endIndex = startIndex + hosei
                if endIndex == lines[n]:
                    endIndex -= 1
                return startLine, startIndex, startLine, endIndex
            else:
                #startとendが跨いだ場合はそれぞれで情報を独自に保持する
                #スタート側はその行の文字列長最大-1まで確保、最後の文字は改行のため無視
                #startEnd = len(lines[startLine - 1]) - 1
                #エンド側はその行の最初からなので、０固定、よって戻り値は以下となる
                #あとはスタート同じ用にさを求める
                endIndex = pythonEndIndex - tempTotalLength + lines[n]
                return startLine, startIndex, endLine, endIndex

def lengthDoubleByteStr(text):
    """ 全角・半角を区別して文字列の長さを返す """
    count = 0
    for c in text:
        # 全角文字などの２バイト文字は'F','W','A'のいずれかに当てはまるとする
        if unicodedata.east_asian_width(c) in 'FWA':
            count += 2
        else:
            count += 1
    return count

#2023/10/15 文字幅による改行に全面シフトした結果、改行した位置の改行文字幅をカウントしないことにしたので、
#渡された引数が改行文字になるのかだけ判定する関数を作成
#且つ、改行文字の全角とそうじゃないかで分ける
def chkNewLineChar(char):
    if char in NewLineTP:
    	if char == " ":
    		return NEWLINE_MARK_HANKAKU_SPACE
    	else:
    		return NEWLINE_MARK_HANKAKU
    elif unicodedata.east_asian_width(char) in 'FWA':
        return NEWLINE_MARK_ZENKAKU
    else:
        return NEWLINE_MARK_NOT

#https://qiita.com/shiba54/items/d4636ec9aa571dee4c9b
def zen2han_index(text: str, for_slice: bool=False) -> list[int]:
    zenkaku = 0
    for hankaku, c in enumerate(text):
        yield zenkaku, hankaku
        zenkaku += 1
        if unicodedata.east_asian_width(c) in 'FWA':
            yield zenkaku, hankaku + (1 if for_slice else 0)
            zenkaku += 1


class Zenkaku(str):

    def __init__(self, *args, **kwargs):
        super().__init__()
        self._zen2han_index = dict(zen2han_index(self))
        self._zen2han_slice = dict(zen2han_index(self, for_slice=True))

    def __getitem__(self, index):
        if isinstance(index, int):
            if index < 0:
                index += len(self._zen2han_index)
            index = self._zen2han_index.get(index, index)
        elif isinstance(index, slice):
            start, stop = index.start, index.stop
            if isinstance(start, int) and start < 0:
                start += len(self._zen2han_slice)
            if isinstance(stop, int) and stop < 0:
                stop += len(self._zen2han_slice)
            index = slice(self._zen2han_slice.get(start, start),
                          self._zen2han_slice.get(stop, stop),
                          index.step)
        return super().__getitem__(index)

def resource_path(relative_path):
    try:
        #Retrieve Temp Path
        base_path = sys._MEIPASS
    except Exception:
        #Retrieve Current Path Then Error 
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def keepWindowSize():
    #画面のサイズ変更を防ぐメソッド、実行時にサイズが０なら現在のサイズを控える
    #そうでなければ、控えた値を使って、画面サイズを調整し、控え値を０に戻す
    global wWidth
    global wHeight
    if wWidth == 0:
        wWidth = root.winfo_width()
        wHeight = root.winfo_height()
    else:
        root.geometry(f"{wWidth}x{wHeight}")
        wWidth = 0
        wHeight = 0
    #高さも横幅に連動しているので、横幅だけチェックで良い

# Create the main window
root = tk.Tk()
root.title("Ai Art Impostor Check Incantation ver 2.8")
# incantationは呪文の意味、詠唱を直訳すると賛美歌を示すchantingかオペラ歌手の歌を意味するariaになってしまう

# iconとEXEマークの画像
#https://various-python.hatenablog.com/entry/2021/07/11/003749
#https://telecom-engineer.blog/blog/2023/02/19/pyinstaller/
#exeは
#https://qiita.com/takanorimutoh/items/53bf44d6d5b37190e7d1
#py -m pip install PyInstaller してpip入れて
#py -m PyInstaller AiArtImpostorCheckIncantation.py --onefile --icon=E:\Python\AiArtImpostor\AiArtImpostorCheckIncantation.ico --noconsole
#https://stackoverflow.com/questions/71006377/tkinter-icon-is-not-working-after-converting-to-exe
#py -m PyInstaller AiArtImpostorCheckIncantation.py --clean --onefile --icon=AiArtImpostorCheckIncantation.ico --add-data AiArtImpostorCheckIncantation.ico;. --noconsole
logo=resource_path('AiArtImpostorCheckIncantation.ico') #ソースコードと画像は同じディレクトリにある前提
root.iconbitmap(default=logo)

root.minsize(100, 100)
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

# Frame
frame1 = ttk.Frame(root, padding=10)
frame1.rowconfigure(1, weight=1)
frame1.columnconfigure(0, weight=1)
frame1.grid(sticky=(tk.N, tk.W, tk.S, tk.E))

# Frameを作成すると画面そのものに配置ができなくなるみたい
# Frameの上にボタンなどを配置する形

# Labbel 説明用
#label_automode = ttk.Label(
#    frame1, text='自動補正▶')
#label_automode.grid(row=0, column=0, columnspan=1, sticky=(tk.N, tk.E))

# CheckBox
#チェックボックス、自動補正のON/OFFのみ
chkbox = tk.BooleanVar()
chkbox.set(False)
checkbox_auto = ttk.Checkbutton(frame1, text='◀改行位置自動補正', variable=chkbox, command=changeAuto)
checkbox_auto.grid(
    row=0, column=0, columnspan=2, sticky=(tk.N, tk.W))

# Labbel 説明用
label_delimiter = ttk.Label(
    frame1, text='熟語の区切り文字▶')
label_delimiter.grid(row=0, column=2, columnspan=1, sticky=(tk.N, tk.E))

# ComboBox
#ドロップダウンリスト、熟語の区切りとして使用する文字
# 表示タイトル⇛値 に対応する辞書データ
# data = {"A": 1, "B": 2, "C": 3}
delimiter_dict = {',(半角カンマ)':',', '、(全角句読点)':'、', '　(全角スペース)':'　'}
labels = list(delimiter_dict.keys())

combobox_delimiter = ttk.Combobox(frame1, width=16, height=1, state="readonly", values=labels)
combobox_delimiter.grid(
    row=0, column=3, columnspan=1, sticky=(tk.N, tk.E))
combobox_delimiter.set(',(半角カンマ)')
combobox_delimiter.bind('<<ComboboxSelected>>', selected_delimiter_change)

# Labbel 説明用
label_modify = ttk.Label(
    frame1, text='先頭から語順を固定する熟語数▶')
label_modify.grid(row=0, column=4, columnspan=1, sticky=(tk.N, tk.E))

# ComboBox
#ドロップダウンリスト、Modifyボタンで先頭からいくつ熟語を固定化するかを指定する
#一応想定は0-5で
module_fixed = (0,1,2,3,4,5)
combobox_modify = ttk.Combobox(frame1, width=2, height=1, state="readonly", values=module_fixed)
combobox_modify.grid(
    row=0, column=5, columnspan=1, sticky=(tk.N, tk.E))
combobox_modify.set(0)
combobox_modify.bind('<<ComboboxSelected>>', selected_modify_change)

# Button
#テキストを修正するボタン
button_modify = ttk.Button(
    frame1, text='Modify',
    command=on_modify)
#commandが直接lammdaと書かれていればCMD側に文字列を直接表記させる
button_modify.grid(
    row=0, column=6, columnspan=1, sticky=(tk.N, tk.E))

# Button
#テキストをクリップボードへ
#テキストを一括クリア
button_copy = ttk.Button(
    frame1, text='Copy',
    command=copy_to_clipboard)
#commandが直接lammdaと書かれていればCMD側に文字列を直接表記させる
button_copy.grid(
    row=0, column=7, columnspan=1, sticky=(tk.N, tk.E))


# Text
txt = tk.Text(frame1, height=11, width=50, undo=True)
f1 = Font(family='Helvetica', size=16)
txt.configure(font=f1)
txt.insert(1.0, "こちらに詠唱を貼り付ける、または書き込んでください")
txt.grid(row=1, column=0, columnspan=7, sticky=(tk.N, tk.W, tk.S, tk.E))

# Bind the on_text_change function to the KeyRelease event
txt.bind('<KeyRelease>', on_text_change)
#txt.bind('<Control-Key-y>', redo)

# Scrollbar
scrollbar = ttk.Scrollbar(
    frame1,
    orient=tk.VERTICAL,
    command=txt.yview)
txt['yscrollcommand'] = scrollbar.set
scrollbar.grid(row=1, column=7, columnspan=1, sticky=(tk.N, tk.S, tk.W))

#現在の文字数（全角文字２バイト計算）を表示する
f2 = Font(family='Helvetica', size=14, weight='bold')
label_charcount = ttk.Label(
    frame1, text='入力文字数：0', font=f2)
label_charcount.grid(
    row=2, column=0, columnspan=1, sticky=(tk.N, tk.W))
label_widthcount = ttk.Label(
    frame1, text=' 1行目文字幅：0', font=f2)
label_widthcount.grid(
    row=2, column=1, columnspan=3, sticky=(tk.N, tk.W))
label_widthcount2 = ttk.Label(
    frame1, text=' 2行目文字幅：0', font=f2)
label_widthcount2.grid(
    row=2, column=4, columnspan=3, sticky=(tk.N, tk.W))

# Button
#テキストを一括クリア
button_clear = ttk.Button(
    frame1, text='Clear',
    command=on_clear)
#commandが直接lammdaと書かれていればCMD側に文字列を直接表記させる
#なお、誤作動を防ぐため、画面下側にクリアボタンを配置する
button_clear.grid(
    row=2, column=7, columnspan=1, sticky=(tk.E))

#ボタン実行結果を表示させるラベルメモ
f2 = Font(family='Helvetica', size=14, weight='bold')
label_memo = ttk.Label(
    frame1, text='ここにシステムメッセージが表示されます', font=f2)
label_memo.grid(
    row=3, column=0, columnspan=8, sticky=(tk.N, tk.W))
#Frame内の位置を指定
#https://watlab-blog.com/2020/07/18/tkinter-frame-pack-grid/
# widgetの配置を設定
#frame1.pack(side=tk.LEFT, anchor=tk.NW)

# Run the main event loop
root.geometry("750x250")
root.mainloop()