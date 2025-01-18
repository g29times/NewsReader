import os
import voyageai
from typing import List, Union
import logging
from typing import List, Dict, Any, Optional, Tuple

# 配置日志
logger = logging.getLogger(__name__)

# 初始化 Voyage 客户端
voyage = voyageai.Client(api_key=os.getenv('VOYAGE_API_KEY'))

# 嵌入模型配置
EMBED_MODES = ["voyage-3", "voyage-3-lite", "voyage-multilingual-2"]  # 1024 512 1024
DEFAULT_MODEL = EMBED_MODES[2]  # 默认使用多语言模型

import voyageai
import numpy as np
import json
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)
from src.utils.knn import k_nearest_neighbors

# TODO 
    # 1 隐藏API 
    # 1 加参数可选模型 *
    # 2 LOG日志归档 
    # 3 数据入库PINGCAP
voyage = voyageai.Client(api_key=os.getenv('VOYAGE_API_KEY'))
# voyage = voyageai.Client(api_key='<your secret key>')
# https://docs.voyageai.com/docs/embeddings
embed_modes=["voyage-3", "voyage-3-lite", "voyage-multilingual-2"] # 1024 512 1024
embed_model=embed_modes[2]
rerank_models=["rerank-1", "rerank-lite-1"]
rerank_model=rerank_models[1]

# "谁更像林黛玉？" | instruct 黛宝晴64薛62 best | large 黛宝薛79晴78 | voyage 黛宝薛77晴75
# "红楼梦, 谁更像林黛玉？" | instruct 黛74宝70晴67薛65 best | large 黛81宝81袭80晴80 | voyage 黛81宝80薛77晴76
# "红楼梦, 林家" | instruct 精读本71黛70林家68宝67 | large 林家82夏金桂80黛78精读本77宝77 best | voyage 夏金桂79黛78宝78林家77
# "薛蝌" | large 小说-6 精读本-4 | voyage 小说-2 精读本-5
# "贾府" | Ground Truth: （精读本）281, 有一个重要的情节, 贾宝玉
# "林家" | Ground Truth: 有一个重要的情节, 林黛玉
topic_default = "红楼梦"
query_default = "贾府" # "谁和贾宝玉关系最亲密？" 为贾元春画大观园
# query = "林黛玉" # 林家 "谁更像林黛玉？"
# query = "薛宝钗" # "谁更像薛宝钗？" "晴雯和袭人谁更像薛宝钗？" "袭人和晴雯谁更像薛宝钗？"
k_default = 3
# This will automatically use the environment variable VOYAGE_API_KEY.
# Alternatively, you can use voyage = voyageai.Client(api_key="<your secret key>")
my_documents = [
    "晴雯 霁月难逢，彩云易散。心比天高，身为下贱。风流灵巧招人怨。寿天多因诽谤生，多情公子“空牵念”。① 霁月难逢，彩云易散 - “霁月”，明净开朗的境界，旧时称赞人品行高尚，胸怀洒落，就说如“光风霁月” ； 雨后新叫 “霁”，寓“晴”字。“彩云” 喻美好；云呈彩叫 “霁”，这两句说像晴雯这样的人极为难得，因而也就难于为阴暗、污浊的社会所容，她的周围环境正如册子上所画的，只有“满纸乌云而已。”② 心比天高，身为下贱 - 是说晴雯虽身为丫鬟，却从不肯低三下四地奉迎讨好主子，没有阿谀献媚的奴才像，这样的性格是她不幸命运的根源。③ 风流灵巧招人怨 - 传统道德提“女子无才便是德”，要求安分守己，不必风流灵巧，尤其是奴仆，如果模样标致、倔强不驯、必定会招来一些人的嫉恨。④ 寿夭 - 短命夭折。 晴雯被迫害而死时仅16岁。⑤ 多情公子 - 指贾宝玉。撕扇子作千金一笑晴雯给宝玉拿扇子，失手摔坏了扇子，宝玉好心相劝，晴雯却却故意讥讽袭人；袭人来劝和，又遭到晴雯更加犀利的讽刺，以致宝玉要赶走晴雯，后在全体丫鬟和黛玉的劝和下作罢。不久，宝玉游园见到小憩的晴雯，责其与袭人叫板，宝玉、晴雯言归于好，晴雯认为撕扇子有趣，宝玉便赠扇给她撕，觉得用几把扇子换美人一笑十分值得。她不仅撕了一大堆名扇，还将宝玉、麝月的都撕了。勇补雀金袭贾母给了宝玉一件极为珍贵的雀金袭，宝玉穿着它去给舅舅拜寿，不小心把这雀金袭烧了一个顶针大的小洞。麝月就打发老嬷嬷找能工巧匠织补，结果没有一个人敢揽这活，都不认得这是什么袭皮，怎么织补。只有晴雯识得此物，且只有她一人能织补此物。为解宝玉之忧，重病的晴拼命挣扎织补金雀袭，一针一线，一直做到凌晨4点多；当最后一针补好时，只见晴雯“哎呦”了一声，就声不由主睡下了。晴雯之死晴雯在患了重病的情况下，为了宝玉，“病补雀金袭”，加重病情，后又因王善宝家的在王夫人处搬弄是非，使得晴雯被赶出大观园，后忧愤成疾，不久病逝。晴雯之死的重点在一个“屈”字。作者写宝玉去看望晴雯，晴雯悲愤地对宝玉说：“只是一件，我死了也不甘心的，我虽生得比别人略好些，并没有私情蜜勾引你怎样，如何一口死咬定了我是个狐狸精？我太不服，今日既已耽了虚名，而且临死，不是我说一句后悔的话，早知如此，当日也另有个道理”。晴有林风，晴雯性格当中最可宝贵的一面，和黛玉非常相像，就是她有一种比较自觉的人格意识和朦胧的平等意识。曹雪芹在介绍十二钗的册子时，将晴雯置于首位，是有心的安排，是作者的偏爱。",
    "袭人 枉自温柔和顺，空云似桂如兰；堪羡优伶有福，谁知公子无缘。• 枉自温柔和顺 - 指袭人白白地用“温柔和顺”的姿态去博得主子们的好感。• 空云似桂如兰 - “似桂如兰” ，暗点其名。宝玉从宋代陆游《村居书喜》诗“花气袭人知骤暖” （小说中改“骤” 为 “昼” ）中取 “袭人” 二字为她取名，而兰桂最香，所以举此，但“空云” 二字则是对香的否定。• 堪羡优伶有福 - 在这里常用调侃的味道。优伶，旧称唱戏艺人为优伶。这里指蒋玉菡。• 谁知公子无缘 - 作者在八十回后原写袭人在宝玉落到饥寒交迫的境地之前，早已嫁给了蒋玉菡，只留麝月一人在宝玉身边，所以诗的后面两句才这样说。袭人原来出身贫苦，幼小时因为家里没饭吃，老子娘要饿死，为了换得几两银子才卖给贾府当了丫头。可是她在环境影响下所逐渐形成的思想和性格却和晴雯相反。她的所谓“温柔和顺” ，颇与薛宝钗的 “随分从时” 相似，合乎当时的妇道标准和礼法对奴婢的要求。这样的女子，从封建观点看，当然称得上“似桂如兰”。晴雯虽“身为下贱” 却“心比天高”，性如烈火，敢怒敢为，哪怕因此得罪主子，招至大祸也在所不惜。袭人则温顺驯服，并设身处地为主人着想，惟恐不能恪守职任。晴雯原本比袭人起点高，她虽然身世堪怜，十来岁上被卖到赖家，已记不得家乡父母，想来中间不知被转卖了多少道，但因生得伶俐标致，得到贾母喜爱，像个小宠物一样带在身边，稍大又下派到宝玉房里，虽然因资历问题，薪水不如袭人，却是贾母心中准姨娘的重点培养对象，前途相当可观。而袭人自以为是贾母给了宝玉的，贾母对这个丫头并没有多大兴趣，只当她是个锯了嘴的葫芦，不过比一般的丫鬟格外尽心尽力罢了。倘若把晴雯和的袭人人生比喻成一场牌，晴雯的牌明显起的比袭人好，外形才艺都属上乘，还在上级心里挂了号，袭人则一手的小零牌，几乎看不到未来。袭为副钗，袭人个性与宝钗相似，整天劝宝玉读书，学习“仕途经济” ，最终受到王夫人的赏识，却是 “枉自温柔和顺 ，空云似桂如兰”。作者在判词中用“枉自” “空云” “堪羡” “谁知” ，除了暗示她将来的结局与初愿相违外，还带有一定的嘲讽意味。",
    "香菱 根并荷花一茎香，平生遭际实堪伤；自从两地生孤木，致使香魂返故乡。① 根并荷花一茎香 - 暗点其名。香菱本名英莲，莲就是荷，菱与何同生一池，所以说根在一起，书中香菱曾释自己的名字说，“不独菱花，就连荷叶莲蓬都是有一股清香的。” （八十回）② 遭际 - 遭遇③ 自从两地生孤木，致使香魂返故乡 - 这是说自从薛蟠娶夏金桂为妻之后，香菱就被迫害～而死。 “两地生枯木”，两个土字加上一个木字，是金桂的“桂” 字。“魂返故乡”，指死。册上所画也是这个意思。香菱是甄士隐的女儿，她一生的遭遇极不幸，名为甄英莲，其实就是“真应怜”。出生乡宦家庭，3岁即被人偷走，十几岁时被呆霸王薛蟠强买为妾。按照曹雪芹本来的构思，她是被夏金桂迫害而死的。可是，到了程高本序书中却让香菱一直活下去，在第一百零三回中写夏金桂在汤里下毒，谋害香菱，结果反倒毒死了自己，以为只有这样写坏心肠的人的结局，才足以显示 “天理昭彰，自害自身”。 把曹雪芹的意图改变成一个饱含着惩恶扬善教训的离奇故事，实在是弄巧成拙。至于写到夏金桂死后，香菱被扶正，当上正夫人，更是一显然不符曹雪芹的本意的。曹雪芹塑造的香菱，娇憨天真、纯洁温和、得人怜爱。香菱虽遭厄运的磨难，却依然浑融天真，毫无心机，她总是笑嘻嘻地面对人的一切，她恒守着温和专一的性格。当薛蟠在外寻花问柳被人打得臭死，香菱哭得眼睛都肿了，她为自己付出珍贵的痴情。 薛蟠外出做生意，薛宝钗把她带入大观园来住，她有机会结识众姑娘，为了掲示香菱书香人家的气质，曹雪芹还安排了香菱学诗的故事。“香菱拿了诗，回至蘅芜苑中，诸事不顾，只向灯下一首一首的读起来。宝钗连催她数次睡觉，她也不睡。”“如此茶无心，坐卧不定。”“只在池边树下，或坐在山石上出神，或蹲在地下抠土，来往的人都诧异。”“至三更以后上床卧，两眼鳏鳏，直到五更方才朦胧睡去了。”学诗专注投入，乃至痴迷的境界。香菱学诗，她先拜黛玉为师，并在黛玉的指导下细细品味王维的诗，其次是一边读杜甫诗，一边尝试作诗，几经失败，终于成功，梦中得句，写出了 “精华欲掩料应难，影自娟娟魄自寒” “博得嫦娥应借问，缘何不使永团圆” 的精彩诗句，赢得众人赞赏，被补为《海堂诗社》的社员。曹雪芹在百草千花、万紫千红的大观中特意植入一朵暗香的水菱。这时香菱短暂的温馨画面，给了读者一份小小的安慰。",
    
    "贾宝玉 贾宝玉奉命应写 《有凤来仪》《蘅芷清芬》《怡红快绿》《杏帘在望》四首。其中《杏帘在望》 是林黛玉帮他写的。（因见宝玉大费神思，为省他精神而代作，元春认为代作这首是三首之冠）《怡红快绿》中的“绿玉” 改为 “绿蜡”，是宝钗提醒的。（因宝钗揣测出元春不喜 “绿玉”。偏是她才会如此留心啊。）“宝玉挨打”后宝钗与黛玉的不同探望方式（34回）宝钗托药而来，（光明正大之态，意欲让大家注意到她对宝玉的关切心思） 流露真情时懂得自我控制，内敛而不外露。对于宝玉挨打，她以为事出有因，并借机规劝宝玉走仕途经济之路。黛玉在无人时悄悄来看宝玉，她的深情表现在她的无声之泣及简单的言辞里。写 “桃儿一般的” 眼睛，可见哭泣时间之长与伤心之。但又极不愿别人看到她对宝玉的关心。黛玉的关切完全是真情流露，相比之下，宝钗关切多半是表面文章。黛玉在人生观上与宝玉相同，因为她能抛弃世俗的功利，她看宝玉，送去的是一颗真心，她从不说“那些混帐话”，也不劝宝玉走仕途之路，既便她叫宝玉 “你从此可都改了罢”，也是为宝玉的安危着想。林黛玉与薛宝钗，一个是寄人篱下的孤女，一个是皇家大商人的千金； 一个天真率直，一个城府极深；一个孤立无援，一个有多方支持；一个作叛逆者知己，一个为卫道而说教 。脂砚斋曾有过“钗黛合一” 说，作者将她俩三首诗中并提，除了因为她们在小说中的地位相当外，至少还可以通过贾宝玉对她们的不同态度的比较，以显示钗黛的命运遭遇虽则不同，其结果都是一场悲剧。“对作者来说，或许人世间的美好幸福是不能全得的。 有所取，就有所舍；有所得，就有所失。林黛玉和薛宝钗各有千秋，好像两人合在一起才最完美。如果他们是两个人，就永远不完美。在作者幻想的世界里，在判词当中，她们变成了合在一起的生命形态。”",
    
    "薛宝钗 可叹停机德，堪怜咏絮才!玉带林中挂，金簪雪里埋。①可叹停机德 - 据说薛宝钗，意思是虽然有着合乎孔孟之道标准的那种贤妻良母的品德，可惜徒劳无功。 “停机德”，出《后汉书 • 列女传 • 乐羊子妻》。 故事说： 乐羊子远出寻师求学，因为想家，只过了一年就回家了。他的妻子就拿刀割断了织布机上的绢，以此来比学业中断，规劝他继续求学，谋取功名，不要半途而废。④ 金簪雪里埋 - 这句说薛宝钗，前三字暗点其名； “雪” 谐 “薛”，金簪比 “宝钗”。本是光耀头面的首，竟埋在寒冷的雪堆里，这是对一心想当宝二奶奶的薛宝钗的冷落处境的写照。【花名签酒令八首之】牡丹 - 艳冠群芳（宝钗）• 任是无情也动人（牡丹 端庄、典雅，象征富贵，有大家闺秀之感，薛宝钗就和牡丹一样，大方端庄，追求富贵。花签上的诗句切合宝钗性情冷淡而又能处处得人好的性格特点。）临江仙（薛宝钗的柳絮词）白玉堂前春解舞，东风卷得均匀，蜂围蝶阵乱纷纷。几曾随逝水？岂必委芳尘？万缕千丝终不改，任他随聚随分。 韶华休笑本无根。好风凭借力，送我上青云。   18回中贾妃在游大观园时命贾宝玉等众兄妹各题一匾一诗，贾宝玉奉命应写四首，其中有一首是林黛玉帮他写的，有一首是宝钗提醒他修改的。终生误（宝钗）都道是金玉良姻，俺只念木石前盟。空对着，山中高士晶莹雪； 终不忘，世外仙姝寂寞林。叹人间，美中不足今方信： 纵然是，齐眉举案，到底意难平。这首曲子写贾宝玉婚后仍不忘怀死去的林黛玉，写薛宝钗徒有 “金玉良姻” 的虚名而实际上则终身寂寞。曲名《终身误》就包含这个意思。",
    "林黛玉 林黛玉是和贾宝玉关系最亲密的人。可叹停机德，堪怜咏絮才!玉带林中挂，金簪雪里埋。② 堪怜咏絮才 - 这句说林黛玉，意思说如此聪明有才华的女子，她的命运值得同情。 “咏絮才”，用晋代谢道韫的故事： 有一次，天下大雪，谢道韫的叔父谢安对雪吟句说 “白雪纷纷何所似？” 道韫的哥哥谢朗答道： “撒盐空中差可拟” 谢道韫接着说： “未若柳絮因风起” 谢安一听大为赞赏。见 《世说新语》。③ 玉带林中挂 - 这句说林黛玉，前三字倒读即谐其名。从册里的画 “两株枯木（双木为“林” ），木上悬着一围玉带看，可能又寓宝玉 “悬” 念 “挂”，牵挂死去的黛玉的意思。【花名签酒令八首之】芙蓉 - 风露清愁（黛玉）• 莫怨东风当自嗟（芙蓉清丽、纯洁动人，作者将林黛玉喻作芙蓉，暗指她有出水芙蓉般纯真的天性，美丽、孤傲。禁不起 “狂风” 摧折，亦即暗示她后来受不了贾府事变 “狂风” 的袭击，终于泪尽而逝。“当自嗟”，说明作者固然同情黛玉的不幸，但也深深惋惜她过于脆弱。望凝眉一个是阆苑仙葩，一个是美玉无瑕。若说没奇缘，今生偏又遇着他； 若说有奇缘，如何心事终虚化？ 一个枉自嗟呀，一个空劳牵挂。一个是水中月，一个是镜中花。想眼中能有多少泪珠儿，怎禁得秋流到冬尽、 春流到复！这首曲子写宝、黛的爱情理想因变故而破灭，写林黛玉的泪尽而逝，曲名《枉凝眉》，意思是悲愁有何用？也即曲中所说的 “枉自嗟呀” 。 凝眉，皱眉，悲愁的样子。宝玉曾赠黛玉表字 “颦颦”。黛玉之死第九十六回 瞒消息凤姐设奇谋，泄机关颦儿迷本性。第九十七回 林黛玉焚稿断痴情，薛宝钗出闺成大礼。第九十八回 苦绛珠魂归离恨天，病神瑛泪洒相思地。黛玉弥留之际，直声叫道： “宝玉，宝玉，你好…” 有无限未尽之意。宝玉，宝玉，你好糊涂！宝玉，宝玉，你好狠心！宝玉，宝玉，你好绝情！宝玉，宝玉，你好自为之！宝玉，宝玉，你好好保重…",
    "贾元春 画： 一张弓，弓上挂着一个香橼。（画中画的似乎与宫闱事有关，因为“弓 ” 可谓 “宫”。“ 橼 ” 可谐 “元”。）二十年来辨是非，榴花开处照宫闱。三春争及初春景，虎兔相逢大梦归。",
    "贾探春 才自清明志自高，生于末世运偏消；清明涕泣江边望，千里东风一梦遥。",
    "史湘云 富贵又何为，襁褓之间父母违；展眼吊斜晖，湘江水逝楚云飞。",
    "妙玉 欲洁何曾洁，云空未必空；可怜金玉质，终陷淖泥中。",
    "贾迎春 子系中山狼，得志便猖狂；金闺花柳质，一载赴黄粱。",
    "贾惜春 勘破三春景不长，缁衣顿改昔年妆；可怜绣户侯门女，独卧青灯古佛旁。",
    "王熙凤 凡鸟偏从末世来，都知爱慕此生才；一从二令三人木，哭向金陵事更哀。",
    "贾巧姐 势败休云贵，家亡莫论亲；偶因济村妇，巧得遇恩人。",
    "李纨 桃李春风结子完，到头谁似一盆兰；如冰水好空相妒，枉与他人作笑谈。",
    "秦可卿 - 在现实中引领宝玉进入梦境的人。袅娜柔情。情天情海幻情身，情既相逢必主淫；漫言不肖皆荣出，造衅开端实在宁。",
]

def get_my_documents():
    return my_documents

# 封装 voyageai 核心API
# class VectorTools:
#     def __init__(self, documents=None, query=None):
#         self.documents = documents if documents is not None else []
#         # self.query = query if query is not None else ""
    
#     def get_doc_embeddings(self):
#         print(f"---------------- `{len(self.documents)}` ----------------")
#         # 这里是将文档列表转换为嵌入向量的逻辑
#         embeddings = voyage.embed(self.documents, model=embed_model, input_type="document").embeddings
#         return embeddings

# 将文档列表转换为嵌入向量  voyageai 限制batch数量：128
def get_doc_embeddings(documents):
    print(f"---------------- voyageai embedding {len(documents)} docs ----------------")
    all_embeddings = []
    batch_size = 128
    for i in range(0, len(documents), batch_size):
        batch_docs = documents[i:i+batch_size] # 获取当前批次的文档
        # 调用 voyage API 获取当前批次的 embeddings
        try:
          batch_embeddings = voyage.embed(batch_docs, model=embed_model, input_type="document").embeddings
          all_embeddings.extend(batch_embeddings) # 将当前批次的 embeddings 加入到总的 embeddings 列表中
        except Exception as e:
          print(f"Error during batch embedding: {e}")
    return all_embeddings # np.array(all_embeddings) # 将结果转换为 numpy 数组，方便后续处理
    # embeddings = voyage.embed(documents, model=embed_model, input_type="document").embeddings
    # return embeddings

# 将查询字符串转换为嵌入向量
def get_query_embedding(query):
    print(f"---------------- voyageai embedding query: `{query}` ----------------")
    embedding = voyage.embed([query], model=embed_model, input_type="query").embeddings[0]
    return embedding

# def get_text_embedding(text: str, model: str = DEFAULT_MODEL) -> List[float]:
#     """获取单个文本的嵌入向量
    
#     Args:
#         text: 输入文本
#         model: 使用的模型名称
        
#     Returns:
#         文本的嵌入向量
#     """
#     try:
#         embedding = voyage.embed(text, model=model).embeddings[0]
#         return embedding
#     except Exception as e:
#         logger.error(f"获取文本嵌入向量失败: {str(e)}")
#         return []

# def get_doc_embeddings(documents: Union[List[str], str], model: str = DEFAULT_MODEL) -> List[List[float]]:
#     """获取文档列表的嵌入向量
    
#     Args:
#         documents: 文档列表或单个文档
#         model: 使用的模型名称
        
#     Returns:
#         文档列表的嵌入向量列表
#     """
#     try:
#         # 确保输入是列表形式
#         if isinstance(documents, str):
#             documents = [documents]
            
#         # 批量获取嵌入向量
#         response = voyage.embed(documents, model=model)
#         return response.embeddings
        
#     except Exception as e:
#         logger.error(f"获取文档嵌入向量失败: {str(e)}")
#         return []

# Retrieval 使用KNN召回 TODO 研究 最终的召回效果是KNN影响的吗?
def knn_algo(query, k, doc_embeddings):
    # Get the embedding of the query
    # query_embedding = VectorTools(query).get_query_embedding()
    query_embedding = get_query_embedding(query)

    # dev 取唯一 Compute the similarity
    # Voyage embeddings are normalized to length 1, therefore dot-product and cosine similarity are the same.
    # similarities = np.dot(documents_embeddings, query_embedding)
    # retrieved_id = np.argmax(similarities)
    # print("---------------- LOG ----------------")
    # print(my_documents[retrieved_id])
    # print("---------------- LOG ----------------")

    # 创建VectorTools类的实例，并传入文档列表
    # doc_embeddings = VectorTools(documents=my_documents).get_doc_embeddings()

    # 取多个 Use the k-nearest neighbor algorithm to identify the top-k documents with the highest similarity
    retrieved_embds, retrieved_embd_indices, top_k_scores = k_nearest_neighbors(
        query_embedding=query_embedding,
        documents_embeddings=doc_embeddings,
        k=k
    )
    retrieved_docs_with_scores = [(my_documents[index], score) for index, score in zip(retrieved_embd_indices, top_k_scores)]
    return retrieved_docs_with_scores

# Retrieval 使用ANN召回 # TODO
def ann_algo(query, k, doc_embeddings):
    query_embedding = get_query_embedding(query)
    

# Reranking 外部调用
def rerank(query, documents, top_k=k_default):
    print("---------------- RERANK START ----------------")
    logger.info(f"Reranking with query: {query[:20]}, top_k: {top_k}")
    documents_reranked = voyage.rerank(query, documents or my_documents, model=rerank_model, top_k=top_k)
    for r in documents_reranked.results:
        if len(r.document) > 20:
            logger.info(f"Document: {r.document[:20]}")
        else:
            logger.info(f"Document: {r.document}")
        logger.info(f"Relevance Score: {r.relevance_score}")
        logger.info(f"Index: {r.index}")
    print("---------------- RERANK END ----------------")
    return [r.document for r in documents_reranked.results]

# Rerank实现
def rerank_with_voyage(query: str, documents: List[str], top_k: int = None) -> List[Dict[str, float]]:
    """使用voyage-ai的rerank功能对文档进行重排序
    Args:
        query: 查询文本
        documents: 待重排序的文档列表
        top_k: 返回结果数量，默认返回所有结果
    Returns:
        List[Dict[str, float]]: 重排序结果列表，每个元素包含index和score
    """
    try:
        print(f"---------------- voyageai reranking: `{query}` ----------------")
        # 调用voyage的rerank接口
        response = voyage.rerank(
            query=query,
            documents=documents,
            model=rerank_model,
            top_k=top_k
        )
        logger.info(f"Voyage rerank success: {query}, top_k: {top_k}")
        return response.results
    except Exception as e:
        logger.error(f"Voyage rerank failed: {str(e)}")
        return []

# 获取最终json结果 给外部调用
def query_doc(query=query_default, k=k_default, dev=False, dev_len=20, doc_embeddings=None):
    """
    query: 查询字符串
    k: 返回的文档数量
    dev: 是否开发模式 在控制台输出结果
    dev_len: 控制台输出的文档截断长度
    """
    if(doc_embeddings is None):
        doc_embeddings = get_doc_embeddings(my_documents)
    retrieved_docs_with_scores = knn_algo(query, k, doc_embeddings)

    # 使用字典推导式提取每个item的doc和score属性 
    if(dev): # 开发模式 仅打印
        print("---------------- QUERY DOC START ----------------")
        for doc, score in retrieved_docs_with_scores:
            print(f"Score: {score}, Document: {doc[:dev_len]}")
        print(f"model: {str(embed_model)}, query: {query}, doc size: {str(len(my_documents))}")
        print("---------------- QUERY DOC END ----------------")
    else: # 生产模式 返回json
        items_dict = [{'doc': item[0], 'score': item[1]} for item in retrieved_docs_with_scores]
        # 将包含所需属性的字典列表转换为JSON字符串
        result = {'items': items_dict, 'query': query, 'model': embed_model}
        result_json = json.dumps(result, ensure_ascii=False)
        print("doc size: " + str(len(my_documents)))
        print("model: " + str(embed_model))
        return result_json

# main
if __name__ == "__main__":
    # 测试
    print()
    print(get_query_embedding("你好"))