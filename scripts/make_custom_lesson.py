#!/usr/bin/env python3
"""Generate a beginner-friendly custom Immersion Reader lesson.

Theme: a day in the life of an AI engineer, written with basic English.
Covers four domains lightly: GitHub terms, computer terms, AI terms,
and daily English. Every sentence is short; zh gives a detailed guide.
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "examples" / "custom" / "segments.json"

STOPWORDS = set(
    """a an the and or but if then than that this these those it its is are was were be been being am
    do does did done doing have has had having will would can could should may might must shall not no
    nor so to of in on at by for with from as about into over after before between out against during
    without within above below under again once because while until too very just more most much many
    some any each both few other another such only own same up down off he she they we you i his her
    their our your my me him them us who whom which what when where why how there here also all
    s t don ll re ve d m o y""".split()
)

SEGMENTS = [
    {
        "id": "seg-01",
        "en": (
            "Every morning, we have a short meeting. We call it a standup. "
            "In the standup, I tell my team what I did yesterday. "
            "I also say what I will do today. "
            "The meeting is short, only ten minutes. "
            "It helps everyone know the plan."
        ),
        "tts": (
            "Every morning, we have a short meeting. We call it a standup. "
            "In the standup, I tell my team what I did yesterday. "
            "I also say what I will do today. "
            "The meeting is short, only ten minutes. "
            "It helps everyone know the plan."
        ),
        "zh": (
            "每天早上，我们开一个短会，叫「站会」。站会里，我告诉团队我昨天做了什么，"
            "再说今天要做什么。会议很短，只有十分钟。它让每个人都知道计划。"
            "讲解：standup=站会，team=团队，yesterday=昨天，plan=计划。"
            "固定搭配 have a meeting=开会，tell someone something=告诉某人某事。"
        ),
        "hard": [
            {"w": "standup", "type": "term", "def": "站会;每天早上的简短例会"},
            {"w": "team", "type": "word", "def": "团队;一起工作的人"},
            {"w": "plan", "type": "word", "def": "计划;打算做的事"},
        ],
    },
    {
        "id": "seg-02",
        "en": (
            "Today I will work on a chat feature. "
            "This feature lets users talk to a computer program. "
            "I make a new branch before I write code. "
            "A branch is a copy of the code. "
            "I write my code in the branch. "
            "When I finish, I push the code to GitHub. "
            "GitHub is a website for sharing code."
        ),
        "tts": (
            "Today I will work on a chat feature. "
            "This feature lets users talk to a computer program. "
            "I make a new branch before I write code. "
            "A branch is a copy of the code. "
            "I write my code in the branch. "
            "When I finish, I push the code to GitHub. "
            "GitHub is a website for sharing code."
        ),
        "zh": (
            "今天我要做一个聊天功能。这个功能让用户能和电脑程序对话。写代码前，我新建一个分支。"
            "分支就是代码的一个副本。我在分支里写代码。写完后，把代码推送到 GitHub。"
            "GitHub 是一个分享代码的网站。"
            "讲解：feature=功能，branch=分支，push=推送（把代码上传），"
            "GitHub=代码托管网站。句形 make a copy of X=做 X 的副本。"
        ),
        "hard": [
            {"w": "feature", "type": "term", "def": "功能;产品里的一个能力"},
            {"w": "branch", "type": "term", "def": "分支;代码的副本"},
            {"w": "push", "type": "term", "def": "推送;把代码上传"},
            {"w": "GitHub", "type": "term", "def": "代码托管网站"},
        ],
    },
    {
        "id": "seg-03",
        "en": (
            "My code is ready now. "
            "I open a pull request on GitHub. "
            "A pull request asks other people to check my code. "
            "This is called a review. "
            "The computer also checks my code. "
            "It runs the tests. "
            "If a test fails, I fix the code and try again. "
            "Then the test is green."
        ),
        "tts": (
            "My code is ready now. "
            "I open a pull request on GitHub. "
            "A pull request asks other people to check my code. "
            "This is called a review. "
            "The computer also checks my code. "
            "It runs the tests. "
            "If a test fails, I fix the code and try again. "
            "Then the test is green."
        ),
        "zh": (
            "我的代码写好了。我在 GitHub 上开一个 pull request（简称 PR）。"
            "PR 就是请别人来检查我的代码，这叫 review（评审）。电脑也会检查代码，跑测试。"
            "如果测试失败，我修改代码再试。然后测试就变绿了（通过了）。"
            "讲解：review=评审/审查，test=测试，fail=失败，fix=修复，"
            "green=绿色的，在程序里代表「通过」。"
        ),
        "hard": [
            {"w": "pull request", "type": "term", "def": "拉取请求;请人检查代码"},
            {"w": "review", "type": "term", "def": "评审;检查代码"},
            {"w": "test", "type": "word", "def": "测试;检查是否正常"},
            {"w": "fail", "type": "word", "def": "失败;没通过"},
        ],
    },
    {
        "id": "seg-04",
        "en": (
            "A teammate reviews my code. "
            "He finds a small problem. "
            "He writes a comment under my code. "
            "I read it and say thank you. "
            "Good feedback helps us find problems early. "
            "Then we agree and merge the code. "
            "Merge means put my code into the main branch. "
            "Now the feature is in the project."
        ),
        "tts": (
            "A teammate reviews my code. "
            "He finds a small problem. "
            "He writes a comment under my code. "
            "I read it and say thank you. "
            "Good feedback helps us find problems early. "
            "Then we agree and merge the code. "
            "Merge means put my code into the main branch. "
            "Now the feature is in the project."
        ),
        "zh": (
            "队友评审我的代码，发现一个小问题，就在代码下面写了条评论。我读后说谢谢。"
            "好的反馈帮我们早点发现问题。然后我们达成一致，把代码 merge（合并）起来。"
            "合并就是把我的代码放进主干分支。现在这个功能就在项目里了。"
            "讲解：comment=评论，feedback=反馈，early=早地，"
            "merge=合并，main branch=主干分支，project=项目。"
        ),
        "hard": [
            {"w": "comment", "type": "word", "def": "评论;写的意见"},
            {"w": "feedback", "type": "word", "def": "反馈;别人的意见"},
            {"w": "merge", "type": "term", "def": "合并;把代码并到一起"},
            {"w": "main branch", "type": "term", "def": "主干分支;主代码线"},
        ],
    },
    {
        "id": "seg-05",
        "en": (
            "In the afternoon, I work on the AI part. "
            "The chat program uses a big language model. "
            "A language model is a program that reads and writes text. "
            "I write a prompt. "
            "A prompt is the instruction I give to the model. "
            "I tell it: be friendly, answer in English. "
            "Sometimes the model says something wrong. "
            "I add more examples to help it."
        ),
        "tts": (
            "In the afternoon, I work on the A I part. "
            "The chat program uses a big language model. "
            "A language model is a program that reads and writes text. "
            "I write a prompt. "
            "A prompt is the instruction I give to the model. "
            "I tell it: be friendly, answer in English. "
            "Sometimes the model says something wrong. "
            "I add more examples to help it."
        ),
        "zh": (
            "下午我做 AI 的部分。聊天程序用一个很大的语言模型。语言模型就是能读写文字的电脑程序。"
            "我写一个 prompt（提示词），就是给模型的指令。我告诉它：要友好，用英文回答。"
            "有时模型会说错话，我就多加点例子帮它。"
            "讲解：AI=人工智能，language model=语言模型，prompt=提示词/给 AI 的指令，"
            "instruction=指令，example=例子。句形 answer in English=用英语回答。"
        ),
        "hard": [
            {"w": "language model", "type": "term", "def": "语言模型;能读写的 AI"},
            {"w": "prompt", "type": "term", "def": "提示词;给 AI 的指令"},
            {"w": "instruction", "type": "word", "def": "指令;告诉做什么"},
            {"w": "example", "type": "word", "def": "例子;示范"},
        ],
    },
    {
        "id": "seg-06",
        "en": (
            "Before we put the feature online, I check the logs. "
            "Logs are the records the program writes. "
            "They tell me if something is wrong. "
            "I also watch the error rate. "
            "Error rate is how many requests fail. "
            "If the error rate is low, we are safe. "
            "Then we deploy the feature. "
            "Deploy means put the feature online for everyone."
        ),
        "tts": (
            "Before we put the feature online, I check the logs. "
            "Logs are the records the program writes. "
            "They tell me if something is wrong. "
            "I also watch the error rate. "
            "Error rate is how many requests fail. "
            "If the error rate is low, we are safe. "
            "Then we deploy the feature. "
            "Deploy means put the feature online for everyone."
        ),
        "zh": (
            "把功能上线前，我检查日志。日志是程序写下的记录，能告诉我哪里出了问题。"
            "我还盯着错误率，就是请求失败的占比。错误率低就说明安全。"
            "然后我们部署这个功能，就是把它上线给所有人用。"
            "讲解：log=日志/运行记录，error=错误，rate=比率，low=低，"
            "deploy=部署/上线，request=请求，online=在线。"
        ),
        "hard": [
            {"w": "log", "type": "term", "def": "日志;程序写的记录"},
            {"w": "error rate", "type": "term", "def": "错误率;失败的比例"},
            {"w": "deploy", "type": "term", "def": "部署;上线发布"},
            {"w": "online", "type": "word", "def": "在线的;连上网的"},
        ],
    },
    {
        "id": "seg-07",
        "en": (
            "At the end of the day, we have a short review. "
            "We talk about what went well. "
            "We also talk about what was hard. "
            "Then we pick one small change for next week. "
            "I write my notes in English. "
            "Writing in English every day is good practice. "
            "Slowly, it gets easier. "
            "That is how I improve."
        ),
        "tts": (
            "At the end of the day, we have a short review. "
            "We talk about what went well. "
            "We also talk about what was hard. "
            "Then we pick one small change for next week. "
            "I write my notes in English. "
            "Writing in English every day is good practice. "
            "Slowly, it gets easier. "
            "That is how I improve."
        ),
        "zh": (
            "一天结束前，我们开个短复盘。聊聊哪些做得顺利，哪些比较难。"
            "然后为下周选一个小改进。我用英文写笔记。每天用英文写作是很好的练习。"
            "慢慢就变得更容易了，我就是这样进步的。"
            "讲解：review=回顾/复盘，well=很好地，hard=困难的，pick=挑选，"
            "notes=笔记，practice=练习，slowly=慢慢地，improve=进步。"
            "句形 at the end of the day=一天结束时，talk about X=谈论 X。"
        ),
        "hard": [
            {"w": "well", "type": "word", "def": "好地;顺利地"},
            {"w": "pick", "type": "word", "def": "挑选;选择"},
            {"w": "practice", "type": "word", "def": "练习;反复做"},
            {"w": "improve", "type": "word", "def": "进步;变得更好"},
        ],
    },
]

CHUNKS = [
    {"t": "have a meeting", "cn": "开会", "eg": "We have a meeting at nine every day."},
    {"t": "work on a feature", "cn": "做一个功能", "eg": "I work on a feature this week."},
    {"t": "open a pull request", "cn": "开一个 PR", "eg": "Please open a pull request after the test."},
    {"t": "check the code", "cn": "检查代码", "eg": "Can you check the code for me?"},
    {"t": "say thank you", "cn": "说谢谢", "eg": "I read the comment and say thank you."},
    {"t": "put online", "cn": "上线;放到网上", "eg": "We put the feature online tomorrow."},
]

PATTERNS = [
    {"t": "I work on X.", "cn": "我在做 X。例如：I work on the AI part."},
    {"t": "This is called X.", "cn": "这就叫 X。例如：This is called a review."},
    {"t": "X means Y.", "cn": "X 的意思是 Y。例如：Merge means put the code together."},
    {"t": "It helps everyone X.", "cn": "它帮助每个人 X。例如：It helps everyone know the plan."},
]

TRANSFER_TASKS = [
    {
        "genre": "standup_update",
        "task": (
            "Write 3 short sentences in English about your day, like a standup. "
            "Say what you did and what you will do. Try to use have a meeting, "
            "work on a feature, and say thank you."
        ),
        "hint_chunks": ["have a meeting", "work on a feature", "say thank you"],
    },
]

LEXICON = {
    "morning": {"def": "早晨", "ipa": "/ˈmɔr.nɪŋ/"},
    "short": {"def": "短的", "ipa": "/ʃɔrt/"},
    "meeting": {"def": "会议", "ipa": "/ˈmi.tɪŋ/"},
    "call": {"def": "称呼;打电话", "ipa": "/kɔl/"},
    "standup": {"def": "站会", "ipa": "/ˈstænd.ʌp/"},
    "tell": {"def": "告诉", "ipa": "/tel/"},
    "did": {"def": "做(do的过去式)", "ipa": "/dɪd/"},
    "also": {"def": "也", "ipa": "/ˈɔl.soʊ/"},
    "today": {"def": "今天", "ipa": "/təˈdeɪ/"},
    "only": {"def": "只有;仅仅", "ipa": "/ˈoʊn.li/"},
    "ten": {"def": "十", "ipa": "/ten/"},
    "minutes": {"def": "分钟", "ipa": "/ˈmɪn.ɪts/"},
    "helps": {"def": "帮助", "ipa": "/helps/"},
    "everyone": {"def": "每个人", "ipa": "/ˈev.ri.wʌn/"},
    "know": {"def": "知道", "ipa": "/noʊ/"},
    "plan": {"def": "计划", "ipa": "/plæn/"},
    "chat": {"def": "聊天", "ipa": "/tʃæt/"},
    "feature": {"def": "功能", "ipa": "/ˈfi.tʃər/"},
    "lets": {"def": "让;允许", "ipa": "/lets/"},
    "users": {"def": "用户们", "ipa": "/ˈju.zərz/"},
    "talk": {"def": "交谈", "ipa": "/tɔk/"},
    "computer": {"def": "电脑", "ipa": "/kəmˈpju.tər/"},
    "program": {"def": "程序", "ipa": "/ˈproʊ.ɡræm/"},
    "make": {"def": "做;制造", "ipa": "/meɪk/"},
    "branch": {"def": "分支", "ipa": "/bræntʃ/"},
    "copy": {"def": "副本;复制", "ipa": "/ˈkɑ.pi/"},
    "write": {"def": "写", "ipa": "/raɪt/"},
    "finish": {"def": "完成", "ipa": "/ˈfɪn.ɪʃ/"},
    "push": {"def": "推送", "ipa": "/pʊʃ/"},
    "GitHub": {"def": "代码托管网站", "ipa": "/ˈɡɪt.hʌb/"},
    "website": {"def": "网站", "ipa": "/ˈweb.saɪt/"},
    "sharing": {"def": "分享", "ipa": "/ˈʃer.ɪŋ/"},
    "ready": {"def": "就绪的;准备好了", "ipa": "/ˈred.i/"},
    "open": {"def": "打开", "ipa": "/ˈoʊ.pən/"},
    "asks": {"def": "请求;问", "ipa": "/æsks/"},
    "other": {"def": "其他的", "ipa": "/ˈʌð.ər/"},
    "people": {"def": "人们", "ipa": "/ˈpi.pəl/"},
    "called": {"def": "被叫做", "ipa": "/kɔld/"},
    "review": {"def": "评审;回顾", "ipa": "/rɪˈvju/"},
    "runs": {"def": "运行", "ipa": "/rʌnz/"},
    "tests": {"def": "测试们", "ipa": "/tests/"},
    "fails": {"def": "失败", "ipa": "/feɪlz/"},
    "fix": {"def": "修复", "ipa": "/fɪks/"},
    "again": {"def": "再一次", "ipa": "/əˈɡen/"},
    "green": {"def": "绿色的;通过的", "ipa": "/ɡriːn/"},
    "teammate": {"def": "队友", "ipa": "/ˈtim.meɪt/"},
    "finds": {"def": "发现", "ipa": "/faɪndz/"},
    "problem": {"def": "问题", "ipa": "/ˈprɑ.bləm/"},
    "under": {"def": "在…下面", "ipa": "/ˈʌn.dər/"},
    "read": {"def": "阅读", "ipa": "/riːd/"},
    "thank": {"def": "感谢", "ipa": "/θæŋk/"},
    "you": {"def": "你", "ipa": "/ju/"},
    "feedback": {"def": "反馈", "ipa": "/ˈfid.bæk/"},
    "early": {"def": "早地", "ipa": "/ˈɝ.li/"},
    "agree": {"def": "同意", "ipa": "/əˈɡri/"},
    "merge": {"def": "合并", "ipa": "/mɝdʒ/"},
    "means": {"def": "意味着;意思是", "ipa": "/miːnz/"},
    "put": {"def": "放", "ipa": "/pʊt/"},
    "main": {"def": "主要的", "ipa": "/meɪn/"},
    "project": {"def": "项目", "ipa": "/ˈprɑ.dʒekt/"},
    "afternoon": {"def": "下午", "ipa": "/ˌæf.tərˈnun/"},
    "big": {"def": "大的", "ipa": "/bɪɡ/"},
    "language": {"def": "语言", "ipa": "/ˈlæŋ.ɡwɪdʒ/"},
    "model": {"def": "模型", "ipa": "/ˈmɑ.dəl/"},
    "text": {"def": "文本;文字", "ipa": "/tekst/"},
    "prompt": {"def": "提示词", "ipa": "/prɑmpt/"},
    "instruction": {"def": "指令", "ipa": "/ɪnˈstrʌk.ʃən/"},
    "give": {"def": "给", "ipa": "/ɡɪv/"},
    "friendly": {"def": "友好的", "ipa": "/ˈfrend.li/"},
    "answer": {"def": "回答", "ipa": "/ˈæn.sər/"},
    "sometimes": {"def": "有时", "ipa": "/ˈsʌm.taɪmz/"},
    "says": {"def": "说", "ipa": "/sez/"},
    "wrong": {"def": "错误的", "ipa": "/rɔŋ/"},
    "more": {"def": "更多的", "ipa": "/mɔr/"},
    "check": {"def": "检查", "ipa": "/tʃek/"},
    "logs": {"def": "日志们", "ipa": "/lɔɡz/"},
    "records": {"def": "记录们", "ipa": "/ˈrek.ərdz/"},
    "writes": {"def": "写", "ipa": "/raɪts/"},
    "watch": {"def": "观察;看", "ipa": "/wɑtʃ/"},
    "error": {"def": "错误", "ipa": "/ˈer.ər/"},
    "rate": {"def": "比率", "ipa": "/reɪt/"},
    "how": {"def": "多么;怎样", "ipa": "/haʊ/"},
    "many": {"def": "许多", "ipa": "/ˈmen.i/"},
    "requests": {"def": "请求们", "ipa": "/rɪˈkwests/"},
    "low": {"def": "低的", "ipa": "/loʊ/"},
    "safe": {"def": "安全的", "ipa": "/seɪf/"},
    "deploy": {"def": "部署;上线", "ipa": "/dɪˈplɔɪ/"},
    "online": {"def": "在线的", "ipa": "/ˈɑn.laɪn/"},
    "end": {"def": "末尾;结束", "ipa": "/end/"},
    "about": {"def": "关于", "ipa": "/əˈbaʊt/"},
    "went": {"def": "去(go的过去式)", "ipa": "/went/"},
    "well": {"def": "好地", "ipa": "/wel/"},
    "hard": {"def": "困难的", "ipa": "/hɑrd/"},
    "pick": {"def": "挑选", "ipa": "/pɪk/"},
    "next": {"def": "下一个", "ipa": "/nekst/"},
    "notes": {"def": "笔记们", "ipa": "/noʊts/"},
    "writing": {"def": "写作;书写", "ipa": "/ˈraɪ.tɪŋ/"},
    "every": {"def": "每一个", "ipa": "/ˈev.ri/"},
    "good": {"def": "好的", "ipa": "/ɡʊd/"},
    "slowly": {"def": "慢慢地", "ipa": "/ˈsloʊ.li/"},
    "easier": {"def": "更容易的", "ipa": "/ˈi.zi.ər/"},
    "improve": {"def": "进步", "ipa": "/ɪmˈpruv/"},
    "add": {"def": "添加;增加", "ipa": "/æd/"},
    "change": {"def": "改变;改动", "ipa": "/tʃeɪndʒ/"},
    "checks": {"def": "检查", "ipa": "/tʃeks/"},
    "day": {"def": "一天", "ipa": "/deɪ/"},
    "english": {"def": "英语", "ipa": "/ˈɪŋ.ɡlɪʃ/"},
    "examples": {"def": "例子们", "ipa": "/ɪɡˈzæm.pəlz/"},
    "find": {"def": "找到;发现", "ipa": "/faɪnd/"},
    "gets": {"def": "变得;得到", "ipa": "/ɡets/"},
    "help": {"def": "帮助", "ipa": "/help/"},
    "new": {"def": "新的", "ipa": "/nu/"},
    "now": {"def": "现在", "ipa": "/naʊ/"},
    "one": {"def": "一;一个", "ipa": "/wʌn/"},
    "part": {"def": "部分", "ipa": "/pɑrt/"},
    "problems": {"def": "问题们", "ipa": "/ˈprɑ.bləmz/"},
    "reads": {"def": "阅读", "ipa": "/riːdz/"},
    "reviews": {"def": "评审;回顾", "ipa": "/rɪˈvjuz/"},
    "small": {"def": "小的", "ipa": "/smɔl/"},
    "something": {"def": "某事物", "ipa": "/ˈsʌm.θɪŋ/"},
    "try": {"def": "尝试", "ipa": "/traɪ/"},
    "uses": {"def": "使用", "ipa": "/ˈju.zɪz/"},
    "week": {"def": "星期;周", "ipa": "/wiːk/"},
    "yesterday": {"def": "昨天", "ipa": "/ˈjes.tər.deɪ/"},
}


def normalize_ipa(ipa: str) -> str:
    return ipa.replace("ɒ", "ɑ").replace("əʊ", "oʊ").replace("ː", "")


def content_words() -> set[str]:
    words: set[str] = set()
    for seg in SEGMENTS:
        for token in re.findall(r"[a-z][a-z'-]*", seg["en"].lower()):
            if token not in STOPWORDS and len(token) > 2:
                words.add(token)
    return words


def build() -> dict:
    total_words = sum(len(seg["en"].split()) for seg in SEGMENTS)
    segments = [{"id": s["id"], "en": s["en"], "tts": s["tts"], "zh": s["zh"], "hard": s["hard"]} for s in SEGMENTS]
    data = {
        "meta": {
            "title": "From Pull Request to Merge: A Day in the Life of an AI Engineer",
            "title_zh": "从 PR 到合并：AI 工程师的一天（零基础版）",
            "source": "Custom lesson: beginner-friendly GitHub + computer + AI + daily English",
            "url": "",
            "kind": "article",
            "lang": "en",
            "study_card": {
                "word_count": total_words,
                "segment_count": len(segments),
                "difficulty": "入门",
                "estimated_days": 2,
                "main_practice": "跟读 + 精读 + 中文讲解对照",
                "value_points": [
                    "用最短句式认识 GitHub 词汇: standup / branch / push / merge",
                    "认识 3 个 AI 常用词: model / prompt / deploy",
                    "每天用 3 句英文做站会练习",
                ],
                "suggested_pace": "第 1 天 逐句听读 §1-4 · 第 2 天 逐句听读 §5-7 + 读中文讲解 + 做站会任务",
            },
        },
        "voice": {"engine": "edge", "voice": "en-US-AndrewNeural", "rate": "-20%", "speed": 0.8},
        "segments": segments,
        "chunks": CHUNKS,
        "patterns": PATTERNS,
        "transfer_tasks": TRANSFER_TASKS,
        "lexicon": {w: {**e, "ipa": normalize_ipa(e["ipa"])} if e.get("ipa") else e for w, e in LEXICON.items()},
    }
    return data


def main() -> int:
    data = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"segments: {len(data['segments'])}  words: {data['meta']['study_card']['word_count']}")
    print(f"lexicon entries: {len(LEXICON)}  content words: {len(content_words())}")
    print(f"written: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
