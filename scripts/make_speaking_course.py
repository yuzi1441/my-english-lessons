#!/usr/bin/env python3
"""Generate the year-long speaking course: one continuous story per day, built on that day's vocabulary.

Design contract (unchanged from the 30-day original):
- Vocabulary is the main line: every one of the day's 18 items (6 computer, 6 daily, 6 GitHub)
  appears verbatim in the day's spoken English, verified before anything is written.
- The story is continuous: a fixed cast (Alex, mentor Maria, teammates Leo and Priya) moves
  through monthly chapter arcs; each day gets its own opening, life beat, and closing hook.
- Difficulty climbs day by day: tier bands come from course.json; speech rate rises with tiers.
- Every English sentence is authored together with its exact Chinese translation.

Content files (per course id):
- content/month-NN.vocab.json   authored vocabulary (consumed via make_vocabulary_course)
- content/month-NN.story.json   30 bilingual plot frames + optional lexicon/lemmas/routing hints
Output:
- examples/courses/<id>/days/day-NNN/segments.json
- lessons/week/courses/<id>/index.html  (course home, grouped by month)
"""

from __future__ import annotations

import argparse
import bisect
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from lesson_quality import word_audio_slug  # noqa: E402
from make_vocabulary_course import (  # noqa: E402
    VERB_STARTS,
    build_course as build_vocab_course,
    load_content_month_files,
    load_course_config,
    speech_text,
)

# terms that begin with a verb-looking word but are noun phrases
NP_ALWAYS = {
    "process", "retry", "retry limit", "request", "open source", "open question",
    "clean state", "clone URL", "pull request template", "request for comments",
}

# terms verified as verb + object/modifier phrases
VP_COMPOUNDS = {
    "clone a repository", "download the code", "run a program", "execute code", "stop a process",
    "save a snapshot", "make a commit", "create a branch", "switch branches", "process data",
    "push changes", "pull changes", "fetch updates", "sync with remote", "fix a bug",
    "open an issue", "close an issue", "install software", "uninstall a program",
    "open a pull request", "request a review", "save to disk", "free up space", "approve changes",
    "request changes", "leave a comment", "resolve a conversation", "take out the trash",
    "wash the dishes", "clean the room", "pick up groceries", "finish the chores", "do the laundry",
    "merge branches", "resolve a conflict", "accept incoming change", "complete the merge",
    "make an appointment", "cancel an appointment", "confirm the time", "check details",
    "fork a repository", "watch a repository", "resolve a domain", "add a label", "remove a label",
    "assign an issue", "mention a teammate", "subscribe to an issue", "unsubscribe from updates",
    "send a request", "receive a response", "mark as ready", "convert to draft", "parse data",
    "sign out", "revoke a token", "restore data", "restrict pushes", "start a container",
    "publish a release", "amend a commit", "revert a commit", "reset a branch", "discard changes",
    "restore a file", "catch an exception", "handle an error", "squash and merge", "rebase and merge",
    "squash commits", "rebase a branch", "verify the answer", "link to documentation",
    "cite a source", "link a commit", "update immediately",
    "reproduce an error", "restart the computer",
}

# plural-form noun terms: singular "be" frames would break agreement
PLURAL_NPS = {"draft changes", "system settings"}

# mass / abstract terms read ungrammatically with a definite article
ARTLESS = {
    "source code", "code hosting", "continuous integration", "open source",
    "data flow", "training data", "structured data", "linear history",
    "machine learning", "secret scanning", "JSON", "CSV", "debugging",
}

SPEAKERS = ["Maria", "Leo", "Priya"]

# When both daily items of a scene share the same wording (repeated drill phrases),
# a two-person exchange would echo; narrate it as one heard line plus a repeat.
ECHO_SOLE = {
    1: [
        ('{spk} says, "{d1}" I repeat it.', '{spk}说："{d1z}"我跟着重复了一遍。'),
        ('I hear, "{d1}" then I say it too.', '我听到："{d1z}"然后我也说了一遍。'),
    ],
    2: [
        ('{spk} says, "{d1}" and I repeat it twice.', '{spk}说："{d1z}"我重复了两遍。'),
        ('First I hear, "{d1}" then I say it myself.', '我先听到："{d1z}"然后自己说了一遍。'),
    ],
    3: [
        ('{spk} says, "{d1}" and I repeat it until it feels natural.', '{spk}说："{d1z}"我反复练习，直到说起来自然。'),
        ('We both use the same words today: "{d1}"', '我们今天都用了同一句话："{d1z}"'),
    ],
    4: [
        ('{spk} says, "{d1}" and I repeat it to make it stick.', '{spk}说："{d1z}"我又重复了一遍，好把它记牢。'),
        ('The phrase of the day is "{d1}" and I use it twice.', '今天的重点句型是"{d1z}"，我用了两次。'),
    ],
    5: [
        ('{spk} says, "{d1}" and I write it down word by word.', '{spk}说："{d1z}"我一字一句记了下来。'),
        ('The phrase today is "{d1}" and I use it again in my summary.', '今天的短语是"{d1z}"我在总结里又用了一遍。'),
    ],
    6: [
        ('{spk} repeats, "{d1}" and I nod along, already taking notes.', '{spk}又说了一遍："{d1z}"我跟着点头，笔记已经跟上。'),
        ('We both use "{d1}" in our updates, and the room notices the echo.', '我们在汇报里都用到了"{d1z}"全场都注意到了这个呼应。'),
    ],
    7: [
        ('{spk} stresses, "{d1}" and I take careful note without any paper at all.', '{spk}强调："{d1z}"我不需要纸笔就记在了心里。'),
        ('The phrase "{d1}" appears twice today, and both times it was exactly the right words.', '"{d1z}"这个说法今天出现了两次，两次都是对的词。'),
    ],
    8: [
        ('{spk} confirms, "{d1}" and I agree out loud, so the doubt leaves the room.', '{spk}确认："{d1z}"我大声表示同意，怀疑就这样离开了房间。'),
        ('I repeat the key phrase once more, "{d1}" and it finally feels like mine.', '我又把关键句说了一遍："{d1z}"这一次它终于像是我自己的话了。'),
    ],
}


# ---------------------------------------------------------------------------
# Difficulty tiers: bands come from course.json so month one keeps its exact
# original 4-tier progression and later tiers span the remaining year.
# ---------------------------------------------------------------------------

TIER_META = {
    1: {"name": "入门短句", "rate": "-22%", "speed": 0.82,
        "pace": "先盲听 · 逐句跟读 · 看着中文说出英文",
        "practice": "听短句 · 跟读 · 替换成自己的话"},
    2: {"name": "基础表达", "rate": "-16%", "speed": 0.86,
        "pace": "先猜大意 · 听读 2 遍 · 遮住中文复述",
        "practice": "听完整段 · 跟读 · 用连接词复述"},
    3: {"name": "连贯叙述", "rate": "-10%", "speed": 0.90,
        "pace": "先盲听全篇 · 精读从句 · 复述剧情",
        "practice": "听细节 · 解释因果 · 连贯复述"},
    4: {"name": "专业场景", "rate": "-5%", "speed": 0.95,
        "pace": "先听更新要点 · 记下风险词 · 模拟汇报",
        "practice": "听专业表达 · 提炼观点 · 做一次英文汇报"},
    5: {"name": "日常职场", "rate": "-4%", "speed": 0.96,
        "pace": "先听要点 · 记下关键动词 · 复述场景",
        "practice": "听工作表达 · 模仿语气 · 复述给同事"},
    6: {"name": "工作交流", "rate": "-2%", "speed": 0.98,
        "pace": "先听结构 · 记下连接词 · 口头总结",
        "practice": "听会议表达 · 提炼观点 · 做口头总结"},
    7: {"name": "进阶职场", "rate": "-1%", "speed": 0.99,
        "pace": "先听讨论脉络 · 记下立场词 · 模拟讨论",
        "practice": "听专业讨论 · 提炼观点 · 参与一次讨论"},
    8: {"name": "专业汇报", "rate": "+0%", "speed": 1.0,
        "pace": "先听汇报结构 · 记下数据词 · 模拟汇报",
        "practice": "听完整汇报 · 提炼观点 · 做一次完整英文汇报"},
}

DEFAULT_TIER_BANDS = [[1, 7], [8, 14], [15, 21], [22, 45], [46, 115], [116, 210], [211, 290], [291, 365]]


def make_tier_of(bands: list[list[int]]):
    starts = [band[0] for band in bands]

    def tier_of(day: int) -> int:
        return max(1, min(len(bands), bisect.bisect_right(starts, day)))

    return tier_of


# ---------------------------------------------------------------------------
# Bilingual sentence templates. Each English template is authored together
# with its exact Chinese translation; slots are filled from course data.
# Tiers 1-4 are the original 30-day pools; tiers 5-8 continue the ladder.
# ---------------------------------------------------------------------------

NP_POOL = {
    1: [
        ("I look at {np}.", "我看着{z}。"),
        ("This is {np}.", "这是{z}。"),
        ("I see {np}.", "我看到了{z}。"),
        ("{np_cap} is new to me.", "{z}对我来说很新。"),
        ("Maria shows me {np}.", "Maria 给我看了{z}。"),
        ("I point to {np}.", "我指着{z}。"),
    ],
    2: [
        ("Maria explains {np} to me.", "Maria 给我讲解{z}。"),
        ("I learn about {np} because it is useful.", "我学习{z}，因为它很有用。"),
        ("Now I understand {np}.", "现在我理解了{z}。"),
        ("I write a short note about {np}.", "我给{z}写了一条简短的笔记。"),
        ("I ask one question about {np}.", "我问了一个关于{z}的问题。"),
        ("Leo shows me an example of {np}.", "Leo 给我看了一个{z}的例子。"),
        ("I hear {np} in the meeting and write it down.", "我在会上听到{z}，把它记了下来。"),
        ("I read the short guide about {np} twice.", "我把关于{z}的简短说明读了两遍。"),
    ],
    3: [
        ("Before the meeting, I review {np} one more time.", "开会前，我又复习了一遍{z}。"),
        ("The team talks about {np} at the standup.", "团队在站会上讨论了{z}。"),
        ("When I get stuck, I ask Maria about {np}.", "卡住的时候，我就向 Maria 请教{z}。"),
        ("I compare my notes about {np} with Priya's.", "我把关于{z}的笔记和 Priya 的对照了一下。"),
        ("Priya and I spend a few minutes on {np}.", "Priya 和我在{z}上花了几分钟。"),
        ("After lunch, I check {np} again.", "午饭后，我又检查了一遍{z}。"),
        ("I add {np} to my notes with one example.", "我把{z}和一个例子一起记进了笔记。"),
        ("Leo walks me through {np} step by step.", "Leo 一步一步带我过了{z}。"),
        ("We keep a short checklist for {np}.", "我们为{z}准备了一张简短的检查单。"),
        ("I reread the section about {np} after lunch.", "午饭后我重读了关于{z}的章节。"),
    ],
    4: [
        ("I walk a new teammate through {np}.", "我带一位新队友过了一遍{z}。"),
        ("I double-check {np} before the review.", "评审之前，我再核对一遍{z}。"),
        ("I suggest that we check {np} first.", "我建议我们先检查{z}。"),
        ("During the review, I ask one question about {np}.", "评审时，我就{z}提了一个问题。"),
        ("I reread my notes about {np} after lunch.", "午饭后我重读了关于{z}的笔记。"),
        ("I add {np} to my checklist for tomorrow.", "我把{z}加进了明天的清单。"),
        ("We spend a few minutes on {np} at the standup.", "站会上我们花了几分钟讨论{z}。"),
        ("I keep one real example of {np} in my notes.", "我在笔记里留了一个{z}的真实例子。"),
        ("Before I reply, I look at {np} once more.", "回复之前，我又看了一遍{z}。"),
        ("I go through {np} with Priya and note her advice.", "我和 Priya 过了一遍{z}，记下了她的建议。"),
    ],
    5: [
        ("I add {np} to my study notes before I forget it.", "我趁还没忘，把{z}记进了学习笔记。"),
        ("I go over {np} one more time before lunch.", "午饭前我又过了一遍{z}。"),
        ("There is a short paragraph about {np} in the guide.", "指南里有一小段关于{z}的介绍。"),
        ("I ask one good question about {np} in the meeting.", "会上关于{z}，我问了一个好问题。"),
        ("My notes about {np} look clearer this week.", "这周我关于{z}的笔记清楚多了。"),
        ("I spend ten quiet minutes on {np} after the standup.", "站会之后，我安安静静花了十分钟在{z}上。"),
        ("Sam asks me about {np}, and I explain the basics.", "Sam 问起{z}，我讲了讲基础。"),
        ("I keep one real example of {np} in my notebook.", "我在笔记本里留了一个{z}的真实例子。"),
    ],
    6: [
        ("In today's standup, I mention {np} and what comes next.", "今天的站会上，我提到{z}和接下来的安排。"),
        ("We agree to give {np} one more careful look this week.", "我们说好这周再把{z}仔细看一次。"),
        ("I connect {np} to the ticket so nothing gets lost.", "我把{z}关联到工单上，免得遗漏。"),
        ("Priya suggests a cleaner way to think about {np}.", "Priya 提出了一个更清晰的{z}思考方式。"),
        ("While the details are fresh, I write down {np}.", "趁细节还新鲜，我把{z}写了下来。"),
        ("The guide now has a short section on {np}.", "指南里现在有关于{z}的简短章节。"),
        ("I compare my notes about {np} with Priya's.", "我把关于{z}的笔记和 Priya 的对照了一下。"),
        ("At the review, we spend ten minutes on {np}.", "评审时，我们花了十分钟在{z}上。"),
    ],
    7: [
        ("During the design review, I raise one careful question about {np}.", "设计评审中，我就{z}提出了一个审慎的问题。"),
        ("Our mentor walks me through how {np} evolved on this team.", "导师带我梳理了{z}在这个团队里的演变。"),
        ("Before deciding, I reread my notes about {np} twice.", "做决定之前，我把关于{z}的笔记重读了两遍。"),
        ("I prepare a one-page brief about {np} so meetings start from facts.", "我准备了一页关于{z}的简报，好让会议从事实出发。"),
        ("The team names one clear owner for {np}.", "团队为{z}指定了明确的负责人。"),
        ("I compare two views on {np} and write both down honestly.", "我比较了关于{z}的两种观点，诚实地都记了下来。"),
        ("I add {np} to the meeting agenda with three supporting facts.", "我把{z}连同三条支撑事实加进了议程。"),
        ("We spend the first ten minutes of the review on {np}.", "评审的前十分钟，我们都用在了{z}上。"),
    ],
    8: [
        ("I present {np} with a timeline, the data, and one clear ask.", "我用时间线、数据和一条明确的诉求来汇报{z}。"),
        ("We align on {np} early, so execution never has to guess.", "我们尽早就{z}对齐，让执行无需猜测。"),
        ("My report covers {np}, the risks behind it, and the cost of waiting.", "我的报告涵盖{z}、背后的风险，以及等待的代价。"),
        ("I propose a measurable target for {np} this quarter.", "我为{z}提出了本季度一个可衡量的目标。"),
        ("We review {np} against the requirements, line by line.", "我们逐行对照需求检查了{z}。"),
        ("I close the discussion on {np} with a short summary.", "我用一段简短的总结为{z}的讨论收尾。"),
        ("The final deck includes {np} and what we learned from it.", "最终的材料里有{z}，以及我们从中学到的东西。"),
        ("I put {np} on the record so the reasoning stays visible.", "我把{z}记录在案，让推理过程保持可见。"),
    ],
}

VP_POOL = {
    1: [
        ("I {vp}.", "我{vz}。"),
        ("I {vp} slowly.", "我慢慢{vz}。"),
        ("Now I can {vp}.", "现在我会{vz}了。"),
        ("I try to {vp}.", "我试着{vz}。"),
        ("Maria asks me to {vp}.", "Maria 让我{vz}。"),
        ("I {vp} with Maria.", "我和 Maria 一起{vz}。"),
    ],
    2: [
        ("Today I {vp} for the first time.", "今天我第一次{vz}。"),
        ("I {vp}, and Maria checks it.", "我{vz}，Maria 来检查。"),
        ("I need to {vp} before lunch.", "午饭前，我需要{vz}。"),
        ("I {vp} carefully.", "我认真地{vz}。"),
        ("Leo shows me how to {vp}.", "Leo 教我怎样{vz}。"),
        ("I {vp} one small step at a time.", "我一步一步地{vz}。"),
    ],
    3: [
        ("After I {vp}, I tell the team.", "我{vz}之后，告诉了团队。"),
        ("I {vp} so the team can see the change.", "我{vz}，好让团队看到变化。"),
        ("Before I {vp}, I read the note.", "在{vz}之前，我先看了说明。"),
        ("When I {vp}, I follow the guide.", "我{vz}时，按照指南操作。"),
        ("I {vp}, and Priya watches the result.", "我{vz}，Priya 在旁边看结果。"),
        ("It takes me ten minutes to {vp}.", "我花了十分钟{vz}。"),
    ],
    4: [
        ("I {vp} and then explain the risk.", "我{vz}，然后解释了风险。"),
        ("We decide to {vp} after the review.", "评审之后，我们决定{vz}。"),
        ("If we {vp}, the result should be safe.", "如果我们{vz}，结果应该是安全的。"),
        ("I {vp}, and I record the reason.", "我{vz}，并记录了原因。"),
        ("The team agrees to {vp} before Friday.", "团队同意在周五之前{vz}。"),
        ("I {vp} while the others watch the dashboard.", "我{vz}，其他队友盯着仪表盘。"),
    ],
    5: [
        ("This morning, I {vp} before the first call.", "今天早上，第一次通话之前我先{vz}。"),
        ("I {vp} while the office is still quiet.", "趁办公室还安静，我{vz}。"),
        ("Maria watches while I {vp}.", "Maria 看着我{vz}。"),
        ("I {vp} twice, just to be sure.", "我{vz}了两遍，只为确定。"),
        ("It is finally my turn to {vp}.", "终于轮到我{vz}了。"),
        ("I {vp}, then I take a short break.", "我{vz}，然后休息了一下。"),
        ("Priya and I {vp} together after lunch.", "午饭之后，Priya 和我一起{vz}。"),
        ("I {vp} the way the guide suggests.", "我按照指南建议的方式{vz}。"),
    ],
    6: [
        ("In today's session, I {vp} with Priya's help.", "今天的工作里，我在 Priya 的帮助下{vz}。"),
        ("I {vp}, then I note one thing I learned.", "我{vz}，然后记下一条学到的东西。"),
        ("We agree that I will {vp} this week.", "我们说好这周由我来{vz}。"),
        ("I {vp} while Leo checks the other half.", "我{vz}，Leo 检查另一半。"),
        ("Before the review, I {vp} and prepare two questions.", "评审之前，我{vz}并准备了两个问题。"),
        ("I {vp} so the next person starts on solid ground.", "我{vz}，让下一个人的起点更扎实。"),
        ("The team decides that I should {vp} first.", "团队决定先由我来{vz}。"),
        ("I {vp}, and Leo writes down the numbers.", "我{vz}，Leo 把数字记了下来。"),
    ],
    7: [
        ("Early in the week, I {vp} and flag what worries me.", "这周一开始我就{vz}，标出让我担心的地方。"),
        ("I {vp} while keeping the main flow steady.", "我在保持主流程稳定的同时{vz}。"),
        ("Priya and I {vp} twice before the customer demo.", "客户演示之前，Priya 和我{vz}了两遍。"),
        ("I {vp} so the launch stays on schedule.", "我{vz}，好让上线不脱期。"),
        ("The team asks me to {vp} and write down each step.", "团队让我{vz}，并把每一步写下来。"),
        ("We agree to {vp} right after the release window.", "我们说好发布窗口一过就{vz}。"),
        ("I {vp} with the dashboard open the whole time.", "我全程开着仪表盘来{vz}。"),
        ("Before sign-off, I {vp} and check the numbers again.", "签字之前，我{vz}并再核对了一遍数字。"),
    ],
    8: [
        ("I {vp} and lay out the trade-offs without hiding any cost.", "我{vz}，并把取舍摆上台面，不隐瞒任何代价。"),
        ("We {vp} because the data clearly points that way.", "我们{vz}，因为数据明确指向那里。"),
        ("I {vp} under a tight deadline without lowering the bar.", "我在紧张的截止线前{vz}，没有降低标准。"),
        ("After the launch, I {vp} and collect honest feedback.", "上线之后，我{vz}并收集真实的反馈。"),
        ("I {vp} so the reasoning stays auditable years later.", "我{vz}，让多年后的推理依然可查。"),
        ("With the whole team, I {vp} and close the milestone with pride.", "我和整个团队一起{vz}，骄傲地关闭了这个里程碑。"),
        ("I {vp} once more, then present the numbers to the room.", "我再{vz}一遍，然后向全场展示数据。"),
        ("We {vp} exactly as the plan described, step by step.", "我们完全按照计划{vz}，一步一步来。"),
    ],
}

VP_LIFE_POOL = {
    1: [
        ("At home, I {vp}.", "在家里，我{vz}。"),
        ("In the evening, I {vp}.", "晚上，我{vz}。"),
        ("I {vp} every day.", "我每天都{vz}。"),
    ],
    2: [
        ("After work, I {vp}.", "下班后，我{vz}。"),
        ("Before bed, I {vp}.", "睡觉前，我{vz}。"),
        ("On my way home, I {vp}.", "回家路上，我{vz}。"),
    ],
    3: [
        ("When I get home, I {vp} first.", "到家后，我先{vz}。"),
        ("I {vp} while I listen to the news.", "我一边听新闻，一边{vz}。"),
        ("This week, I {vp} a little faster.", "这周，我{vz}得快了一些。"),
    ],
    4: [
        ("Even on busy days, I {vp} without rushing.", "即使在忙碌的日子，我也不慌不忙地{vz}。"),
        ("I {vp}, and then I plan the next morning.", "我{vz}，然后安排第二天早上。"),
        ("I {vp} and remind myself that rest matters too.", "我{vz}，也提醒自己休息同样重要。"),
    ],
    5: [
        ("In the evening, I {vp} and call a friend on my way.", "晚上，我{vz}，顺路给朋友打了个电话。"),
        ("I {vp} on the weekend when the city finally goes quiet.", "周末城市终于安静下来时，我{vz}。"),
        ("After dinner, I {vp} for half an hour before I open my laptop again.", "晚饭后，我{vz}半小时，然后才重新打开电脑。"),
    ],
    6: [
        ("I {vp} before the house wakes up, while the kettle is still quiet.", "家里人还没醒、水壶还安静的时候，我就{vz}了。"),
        ("On Friday night, I {vp} and let the week finally let go of me.", "周五晚上，我{vz}，让这一周终于放过我。"),
        ("I {vp} and keep the weekend simple enough to actually rest.", "我{vz}，让周末简单到可以真正休息。"),
    ],
    7: [
        ("Even after a long day, I {vp} for a few quiet minutes before dinner.", "即使忙碌了一整天，晚饭前我也会安静地花几分钟{vz}。"),
        ("On Sunday mornings, I {vp} on my balcony while the city still sleeps.", "周日早上，趁城市还在睡，我在阳台上{vz}。"),
        ("When it rains, I {vp} indoors and let the windows do the drumming.", "下雨的时候，我在室内{vz}，让窗户去打鼓。"),
    ],
    8: [
        ("I {vp} at the end of the week to reset my mind for whatever comes next.", "周末结束时，我{vz}，让头脑归零，迎接接下来的一切。"),
        ("This month, I {vp} with more confidence than the version of me who started all this.", "这个月，我{vz}得比出发时的那个我更有信心。"),
        ("I {vp} and give myself honest credit for the progress, not just the luck.", "我{vz}，诚实地肯定自己的进步，而不只是运气。"),
    ],
}

DLG_POOL = {
    1: [
        ('{spk} says, "{d1}" and I say, "{d2}"', '{spk}说："{d1z}"我说："{d2z}"'),
        ('I hear, "{d1}" then I answer, "{d2}"', '我听到："{d1z}"然后我回答："{d2z}"'),
        ('{spk} smiles and says, "{d1}" I answer, "{d2}"', '{spk}微笑着说："{d1z}"我回答："{d2z}"'),
    ],
    2: [
        ('{spk} says, "{d1}" so I answer, "{d2}"', '{spk}说："{d1z}"于是我回答："{d2z}"'),
        ('First {spk} says, "{d1}" then I reply, "{d2}"', '先是{spk}说："{d1z}"然后我回答："{d2z}"'),
        ('During our chat, {spk} says, "{d1}" I answer, "{d2}"', '聊天时，{spk}说："{d1z}"我回答："{d2z}"'),
    ],
    3: [
        ('When we meet, {spk} says, "{d1}" I reply, "{d2}"', '见面时，{spk}说："{d1z}"我回答："{d2z}"'),
        ('{spk} starts with "{d1}" and I continue with "{d2}"', '{spk}先说了"{d1z}"我接着说："{d2z}"'),
        ('At the table, {spk} says, "{d1}" I think, then answer, "{d2}"', '桌边，{spk}说："{d1z}"我想了想，回答："{d2z}"'),
    ],
    4: [
        ('Before we part, {spk} says, "{d1}" I answer, "{d2}"', '分开前，{spk}说："{d1z}"我回答："{d2z}"'),
        ('{spk} checks with me, "{d1}" I answer clearly, "{d2}"', '{spk}向我确认："{d1z}"我清楚地回答："{d2z}"'),
        ('At the end of the day, {spk} says, "{d1}" I reply, "{d2}"', '一天结束时，{spk}说："{d1z}"我回答："{d2z}"'),
    ],
    5: [
        ('We practise the dialogue: {spk} opens, "{d1}" I answer, "{d2}" and {spk} nods, "{cz}"', '我们练习这段对话：{spk}开场："{d1z}"我回答："{d2z}"{spk}点头说："{cz}"'),
        ('We drill it twice: {spk} starts, "{d1}" I reply, "{d2}" then {spk} smiles, "{cz}"', '我们练了两遍：{spk}起头："{d1z}"我回答："{d2z}"然后{spk}笑着说："{cz}"'),
        ('Role play with feedback: {spk} says, "{d1}" I try, "{d2}" and {spk} adds, "{cz}"', '角色扮演加反馈：{spk}说："{d1z}"我试着说："{d2z}"{spk}补充道："{cz}"'),
        ('Warm-up round: {spk} offers, "{d1}" I answer, "{d2}" and {spk} wraps up, "{cz}"', '热身一轮：{spk}给出："{d1z}"我回答："{d2z}"{spk}收尾道："{cz}"'),
    ],
    6: [
        ('Meeting rehearsal: {spk} opens, "{d1}" I respond, "{d2}" and {spk} confirms, "{cz}"', '会议彩排：{spk}开场："{d1z}"我回应："{d2z}"{spk}确认道："{cz}"'),
        ('Whiteboard practice: {spk} offers, "{d1}" I add, "{d2}" then {spk} sums up, "{cz}"', '白板练习：{spk}给出："{d1z}"我补充："{d2z}"然后{spk}总结："{cz}"'),
        ('Drill without notes: {spk} asks, "{d1}" I answer, "{d2}" and {spk} closes, "{cz}"', '脱稿演练：{spk}问："{d1z}"我回答："{d2z}"{spk}收束："{cz}"'),
        ('Pair run: {spk} starts, "{d1}" I follow, "{d2}" and {spk} replies, "{cz}"', '结对演练：{spk}起头："{d1z}"我跟上："{d2z}"{spk}回应："{cz}"'),
    ],
    7: [
        ('Review warm-up: {spk} raises, "{d1}" I answer, "{d2}" and {spk} grades it, "{cz}"', '评审热身：{spk}抛出："{d1z}"我带着数字回答："{d2z}"{spk}点评道："{cz}"'),
        ('Dry run: {spk} opens, "{d1}" I follow, "{d2}" plus one proposal, and {spk} accepts, "{cz}"', '干跑演练：{spk}开场："{d1z}"我接上："{d2z}"外加一个提案，{spk}接受道："{cz}"'),
        ('Practice debate: {spk} argues, "{d1}" I respond calmly, "{d2}" and {spk} concedes, "{cz}"', '练习辩论：{spk}主张："{d1z}"我平静地回应："{d2z}"{spk}承认道："{cz}"'),
        ('Mock review: {spk} probes, "{d1}" I answer from memory, "{d2}" and {spk} confirms, "{cz}"', '模拟评审：{spk}追问："{d1z}"我凭记忆回答："{d2z}"{spk}确认："{cz}"'),
    ],
    8: [
        ('Launch rehearsal: {spk} asks, "{d1}" I present, "{d2}" with the numbers ready, and {spk} signs off, "{cz}"', '上线彩排：{spk}问："{d1z}"我带着准备好的数字汇报："{d2z}"{spk}签字道："{cz}"'),
        ('Final dry run: {spk} summarises, "{d1}" I confirm, "{d2}" for the record, and {spk} closes, "{cz}"', '最终干跑：{spk}总结："{d1z}"我郑重确认："{d2z}"{spk}收尾道："{cz}"'),
        ('Board practice: {spk} probes, "{d1}" I respond without a pause, "{d2}" and {spk} nods, "{cz}"', '董事会练习：{spk}追问："{d1z}"我毫不迟疑地回应："{d2z}"{spk}点头道："{cz}"'),
        ('Last rehearsal: {spk} checks, "{d1}" I commit word for word, "{d2}" and {spk} smiles, "{cz}"', '最后一次彩排：{spk}核对："{d1z}"我逐字承诺："{d2z}"{spk}笑道："{cz}"'),
    ],
}

PATTERN_POOL = {
    1: [
        ("I practise the pattern out loud: {dl}", "我大声练习这个句型：{dlz}"),
        ("I say the new pattern twice: {dl}", "我把新句型读了两遍：{dlz}"),
        ("I read the pattern slowly: {dl}", "我慢慢读出这个句型：{dlz}"),
        ("Maria says the pattern, and I repeat it: {dl}", "Maria 说出这个句型，我跟着重复：{dlz}"),
    ],
    2: [
        ("Maria asks me to use the pattern: {dl}", "Maria 让我用上这个句型：{dlz}"),
        ("I repeat the pattern after Maria: {dl}", "我跟着 Maria 重复这个句型：{dlz}"),
        ("I write the pattern in my notebook: {dl}", "我把这个句型写在笔记本上：{dlz}"),
        ("The pattern of the day is {dl}", "今天的重点句型是{dlz}"),
    ],
    3: [
        ("I put the pattern into my own sentence: {dl}", "我把这个句型放进自己的句子里：{dlz}"),
        ("The team practises the pattern together: {dl}", "团队一起练习这个句型：{dlz}"),
        ("I use the pattern to ask a question: {dl}", "我用这个句型提了一个问题：{dlz}"),
        ("Leo corrects my use of the pattern: {dl}", "Leo 纠正了我对这个句型的用法：{dlz}"),
    ],
    4: [
        ("In my update, I use the pattern naturally: {dl}", "在汇报里，我自然地用上了这个句型：{dlz}"),
        ("I teach the pattern to a new teammate: {dl}", "我把这个句型教给一位新队友：{dlz}"),
        ("I build a full answer around the pattern: {dl}", "我围绕这个句型组织了一个完整的回答：{dlz}"),
        ("The pattern helps me sound clear and calm: {dl}", "这个句型让我听起来清楚又从容：{dlz}"),
    ],
    5: [
        ("I record the pattern in my own words and test it in a chat: {dl}", "我用自己的话记录这个句型，并在聊天里试了一下：{dlz}"),
        ("I try the pattern in a work chat and it lands well: {dl}", "我在工作聊天里试了这个句型，效果不错：{dlz}"),
        ("The pattern fits today's task better than the old one: {dl}", "这个句型比旧的那个更贴合今天的任务：{dlz}"),
        ("Priya uses the pattern back to me without noticing it: {dl}", "Priya 不知不觉间用同一个句型回应了我：{dlz}"),
    ],
    6: [
        ("I reuse the pattern in the standup and it keeps my update short: {dl}", "我在站会上复用了这个句型，它让我的汇报很简短：{dlz}"),
        ("The pattern holds two ideas together without any strain: {dl}", "这个句型毫不费力地把两个想法连在了一起：{dlz}"),
        ("I combine two small ideas with the pattern and save a paragraph: {dl}", "我用这个句型把两个小想法连起来，省下了一段话：{dlz}"),
        ("Leo says the pattern sounds natural, so it goes into the guide: {dl}", "Leo 说这个句型听起来很自然，于是它进了指南：{dlz}"),
    ],
    7: [
        ("I adapt the pattern for a harder question and it still holds: {dl}", "我把这个句型改造成一个更难的问题，它依然站得住：{dlz}"),
        ("The pattern carries the key point of my update without any noise: {dl}", "这个句型毫无噪音地承载了我汇报的要点：{dlz}"),
        ("I test the pattern with a real scenario before I trust it: {dl}", "在信任这个句型之前，我用真实场景检验了它：{dlz}"),
        ("The mentor refines the pattern with me until it sounds like ours: {dl}", "导师和我一起打磨这个句型，直到它听起来像我们自己的话：{dlz}"),
    ],
    8: [
        ("My presentation opens with the pattern and lands without a hitch: {dl}", "我的汇报用这个句型开场，全程毫无卡壳：{dlz}"),
        ("I turn the pattern into a policy note that others can quote: {dl}", "我把这个句型写成一份别人可以引用的规范说明：{dlz}"),
        ("The pattern holds up under hard questions, and I note that too: {dl}", "面对尖锐的问题这个句型依然站得住，我把这一点也记了下来：{dlz}"),
        ("I close the meeting with the pattern and a clear list of next steps: {dl}", "我用这个句型为会议收尾，并给出一份清晰的下一步清单：{dlz}"),
    ],
}

SCENE_CLOSE_POOL = {
    1: [
        ("I feel good today.", "我今天感觉很好。"),
        ("I learn one new thing.", "我学到了一件新东西。"),
        ("Maria helps me a lot.", "Maria 帮了我很多。"),
    ],
    2: [
        ("The day is busy, but I learn a lot.", "这天很忙，但我学到了很多。"),
        ("I understand a little more than yesterday.", "我比昨天多懂了一点。"),
        ("The team gives me good advice.", "团队给了我很好的建议。"),
    ],
    3: [
        ("The work is not easy, but I keep going.", "工作不容易，但我继续前进。"),
        ("I write down what I learned today.", "我记下了今天学到的东西。"),
        ("With the team's help, the problem becomes smaller.", "在团队的帮助下，问题变小了。"),
    ],
    4: [
        ("The day ends with a clear plan for tomorrow.", "这一天以一份清晰的明日计划结束。"),
        ("I check my notes and confirm the next step.", "我检查笔记，确认了下一步。"),
        ("The team agrees on the plan, and I record the decision.", "团队就计划达成一致，我记录了决定。"),
    ],
    5: [
        ("The task moves forward, and so does my confidence.", "任务在推进，我的信心也在成长。"),
        ("I end the day with fewer unknowns than I started with.", "这一天结束时，我心中的未知比开始时更少了。"),
        ("Small progress today prepares the bigger step tomorrow.", "今天的小进步为明天更大的跨越做准备。"),
    ],
    6: [
        ("The plan is written, the team is aligned, and tomorrow has a door.", "计划写好了，团队也一致了，明天有了一扇门。"),
        ("I close the ticket with a clear result and one lesson for next time.", "我带着清晰的结果关闭了工单，还为下次留了一课。"),
        ("Tomorrow builds on what we finished today, without any wasted steps.", "明天会建立在我们今天完成的工作之上，一步都不浪费。"),
    ],
    7: [
        ("The risk is named, owned, tracked, and a little smaller than yesterday.", "风险被点明、认领、跟踪，而且比昨天更小了一点。"),
        ("We end the week with something shipped and something properly learned this time.", "这一周结束时，我们交付了东西，这次也真正学到了东西。"),
        ("I can explain the decision to anyone on the team now, including the parts I fought for.", "现在我能向团队任何人解释这个决定，包括我坚持过的部分。"),
    ],
    8: [
        ("The launch reflects a month of steady work and a year of short sentences.", "这次上线凝聚了一个月的稳定投入，也凝聚了一年的短句练习。"),
        ("I own the outcome, the next step, and the story we will tell about both.", "我对结果负责，对下一步负责，也对我们将来讲述的故事负责。"),
        ("The team ships faster because we learned to speak clearly before we learned to code fast.", "团队交付得更快，因为我们先学会了把话说清楚，再学会把代码写快。"),
    ],
}

SEG3_INTRO = {
    1: ("Before I leave, I do one last thing.", "离开前，我做最后一件事。"),
    2: ("Before I leave, I finish one last task.", "离开前，我完成最后一项任务。"),
    3: ("Before I leave, I review what I did today.", "离开前，我回顾了今天做的事。"),
    4: ("Before I leave, I write a short summary for the team.", "离开前，我给团队写了一份简短的总结。"),
    5: ("Before I leave, I finish the last small task and tidy my desk.", "离开前，我完成最后一项小任务，整理好桌面。"),
    6: ("Before I leave, I wrap up the day's work and set out tomorrow's first task.", "离开前，我把今天的工作收尾，并摆好明天的第一件事。"),
    7: ("Before I leave, I note tomorrow's risks, name a clear owner for each of them, and set out the first task.", "离开前，我记下明天的风险，给每一项定好负责人，并摆好第一件事。"),
    8: ("Before I leave, I send a short wrap-up with numbers, names, and one thank-you.", "离开前，我给团队发一份简短总结，带上数字、名字和一句感谢。"),
}

SOLO_LINE = {
    1: ('{spk} {verb}, "{d1}"', '{spk}{verbz}："{d1z}"'),
    2: ('Then {spk} {verb}, "{d1}"', '接着{spk}{verbz}："{d1z}"'),
    3: ('At that moment, {spk} {verb}, "{d1}"', '这时，{spk}{verbz}："{d1z}"'),
    4: ('Before we move on, {spk} {verb}, "{d1}"', '继续之前，{spk}{verbz}："{d1z}"'),
    5: ('In the warm-up round, {spk} {verb}, "{d1}"', '热身环节里，{spk}{verbz}："{d1z}"'),
    6: ('In the meeting drill, {spk} {verb}, "{d1}"', '会议演练中，{spk}{verbz}："{d1z}"'),
    7: ('In the review drill, {spk} {verb}, "{d1}"', '评审演练中，{spk}{verbz}："{d1z}"'),
    8: ('In the launch rehearsal, {spk} {verb}, "{d1}"', '上线彩排中，{spk}{verbz}："{d1z}"'),
}

PATTERNS_BY_TIER = {
    1: [
        {"t": "I see the X.", "cn": "我看到了 X。"},
        {"t": "This is X.", "cn": "这是 X。"},
        {"t": "Now I can X.", "cn": "现在我会 X 了。"},
    ],
    2: [
        {"t": "First I X, then I Y.", "cn": "我先 X，然后 Y。"},
        {"t": "I X because Y.", "cn": "我 X，因为 Y。"},
        {"t": "Today I X for the first time.", "cn": "今天我第一次 X。"},
    ],
    3: [
        {"t": "Before I X, I Y.", "cn": "在 X 之前，我先 Y。"},
        {"t": "When I X, I Y.", "cn": "我 X 的时候，Y。"},
        {"t": "I X so the team can Y.", "cn": "我 X，好让团队 Y。"},
    ],
    4: [
        {"t": "If X fails, we need Y.", "cn": "如果 X 失败，我们需要 Y。"},
        {"t": "I suggest that we X first.", "cn": "我建议我们先 X。"},
        {"t": "X is done, but Y still needs Z.", "cn": "X 完成了，但 Y 还需要 Z。"},
    ],
    5: [
        {"t": "I X before Y.", "cn": "我在 Y 之前 X。"},
        {"t": "I X and then note the result.", "cn": "我 X，然后记下结果。"},
        {"t": "X helps the team move faster.", "cn": "X 能让团队更快前进。"},
    ],
    6: [
        {"t": "We agree on X before we Y.", "cn": "在 Y 之前，我们先就 X 达成一致。"},
        {"t": "I X and track it in the ticket.", "cn": "我 X，并在工单里跟踪。"},
        {"t": "X is planned, Y is next.", "cn": "X 已经排好，接下来是 Y。"},
    ],
    7: [
        {"t": "I X early so Y does not surprise us.", "cn": "我提前 X，免得 Y 让我们措手不及。"},
        {"t": "X is done; Y needs an owner.", "cn": "X 已完成；Y 还需要负责人。"},
        {"t": "We weigh X against Y before deciding.", "cn": "决定之前，我们用 Y 来权衡 X。"},
    ],
    8: [
        {"t": "X is live; Y tells us what to improve.", "cn": "X 已经上线；Y 告诉我们该改进什么。"},
        {"t": "I recommend X because Y.", "cn": "我建议 X，因为 Y。"},
        {"t": "X, Y, and Z: that is the whole plan.", "cn": "X、Y、Z：这就是全部计划。"},
    ],
}

TRANSFER_GENRES = ["standup_update", "slack_message", "design_note", "code_review_comment", "pr_description"]

# Offline dictionary entries for high-frequency story words beyond the day's 18.
STORY_LEXICON = {
    "team": "团队，一起工作的一群人", "meeting": "会议", "morning": "早上", "afternoon": "下午",
    "evening": "晚上", "today": "今天", "tomorrow": "明天", "yesterday": "昨天",
    "lunch": "午餐", "dinner": "晚餐", "break": "休息", "week": "周；星期",
    "month": "月", "day": "天；日子", "time": "时间", "job": "工作；职位",
    "work": "工作", "task": "任务", "plan": "计划", "step": "步骤",
    "help": "帮助", "question": "问题", "answer": "回答", "advice": "建议",
    "note": "笔记", "history": "历史；记录", "change": "改动；变化", "result": "结果",
    "reason": "原因", "risk": "风险", "decision": "决定", "guide": "指南",
    "error": "错误", "bug": "缺陷", "fix": "修复", "check": "检查",
    "test": "测试", "review": "评审；回顾", "update": "更新", "release": "发布；版本",
    "server": "服务器", "user": "用户", "code": "代码", "project": "项目",
    "computer": "电脑", "screen": "屏幕", "desk": "桌子", "office": "办公室",
    "friend": "朋友", "teammate": "队友", "mentor": "导师", "leader": "组长",
    "happy": "开心的", "tired": "累的", "nervous": "紧张的", "ready": "准备好的",
    "kind": "友善的", "clear": "清楚的", "careful": "仔细的", "safe": "安全的",
    "new": "新的", "first": "第一", "last": "最后的", "next": "下一个",
    "small": "小的", "big": "大的", "short": "短的", "long": "长的",
    "learn": "学习", "teach": "教", "practice": "练习", "repeat": "重复",
    "listen": "听", "smile": "微笑", "ask": "问；请求", "say": "说",
    "show": "展示", "explain": "解释", "record": "记录", "finish": "完成",
    "start": "开始", "leave": "离开", "arrive": "到达", "join": "加入",
    "merge": "合并", "push": "推送", "pull": "拉取", "commit": "提交",
    "branch": "分支", "deploy": "部署", "rollback": "回滚", "pipeline": "流水线",
    # high-frequency story words
    "maria": "Maria，Alex 的导师", "leo": "Leo，Alex 的队友", "priya": "Priya，Alex 的队友",
    "alex": "Alex，本课主角", "one": "一；一个", "two": "两；二", "write": "写",
    "now": "现在", "look": "看", "twice": "两次", "reply": "回答",
    "lot": "许多", "pattern": "句型；模式", "good": "好的", "later": "稍后",
    "point": "指；要点", "see": "看见", "need": "需要", "understand": "理解",
    "use": "使用", "depends": "取决于", "fails": "失败", "summary": "总结",
    "around": "围绕；大约", "discuss": "讨论", "document": "记录成文档", "suggest": "建议",
    "thing": "事情", "talk": "交谈", "compare": "比较", "detail": "细节",
    "agrees": "同意", "chat": "聊天", "try": "尝试", "learned": "学到的",
    "becomes": "变得", "standup": "站会", "ends": "结束", "confirm": "确认",
    "feel": "感觉", "gives": "给", "read": "读", "meet": "见面",
    "busy": "忙碌的", "little": "一点；小的", "story": "故事", "tells": "告诉",
    "useful": "有用的", "smaller": "更小的", "build": "构建", "clearly": "清楚地",
    "end": "结尾", "full": "完整的", "hear": "听到", "carefully": "认真地",
    "watch": "观察", "problem": "问题", "continue": "继续", "easy": "容易的",
    "going": "going to 表将要", "keep": "保持", "part": "部分", "slowly": "慢慢地",
    "make": "制作", "together": "一起", "home": "家", "friday": "周五",
    "table": "桌子；表格", "think": "想", "decide": "决定", "move": "前进；移动",
    "calm": "从容的", "sound": "听起来", "program": "程序", "late": "迟的",
    "included": "包含在内", "take": "拿；采取", "know": "知道", "back": "回来；向后",
    "monday": "周一", "road": "路", "chat program": "聊天程序", "dashboard": "仪表盘",
    "fire drill": "消防演习", "pharmacy": "药店", "medicine": "药", "bank": "银行",
    "charge": "扣款", "package": "包裹", "customer service": "客服", "deadline": "截止时间",
    "extension": "延期", "trade-offs": "取舍", "option": "选项", "presenter": "介绍人",
    "presentation": "介绍；演示", "menu": "菜单", "price": "价格", "notebook": "笔记本",
    "airport": "机场", "flight": "航班", "hotel": "酒店", "restaurant": "餐厅",
    "bus": "公交车", "way": "路；方式", "weather": "天气", "window": "窗户",
    "news": "新闻", "opinion": "看法", "version": "版本", "feature": "功能",
    "rule": "规则", "security": "安全", "alert": "警报", "dependency": "依赖",
    "contributor": "贡献者", "respect": "尊重", "claim": "说法", "source": "来源",
    "link": "链接", "discussion": "讨论", "idea": "想法", "record": "记录",
    # shared by tier 5-8 template pools
    "list": "清单；列表", "sprint": "迭代；冲刺", "ticket": "工单", "owner": "负责人",
    "brief": "简短说明", "quarter": "季度", "goal": "目标", "outcome": "结果；成果",
    "demo": "演示", "launch": "上线；发布", "milestone": "里程碑", "feedback": "反馈",
    "audit": "审查", "scope": "范围；边界", "requirement": "需求", "requirements": "需求",
    "data": "数据", "cost": "代价；成本", "approach": "方式；路径", "approaches": "方式；路径",
    "trade-off": "取舍", "balance": "平衡", "quiet": "安静的", "balcony": "阳台",
    "confidence": "信心", "progress": "进步", "credit": "肯定；认可", "mind": "头脑；心态",
    "unknown": "未知", "unknowns": "未知的事", "aligned": "达成一致的", "align": "对齐；达成一致",
    "aligns": "对齐", "aligning": "对齐", "summarise": "总结", "summarises": "总结",
    "commitment": "承诺", "measurable": "可衡量的", "live": "已上线的",
    "improve": "改进", "improves": "改进", "recommend": "推荐；建议",
    "policy": "规范；政策", "holds": "站得住", "under": "在……之下",
    "close": "关闭；结束", "closes": "关闭", "closing": "关闭", "loop": "闭环；跟进",
    "shares": "分享", "sharing": "分享", "section": "章节",
    "sprints": "迭代", "explaining": "解释", "handles": "处理", "handle": "处理",
    "double-check": "再核对一遍", "better": "更好的", "faster": "更快",
    "naturally": "自然地", "key": "关键", "carries": "承载", "carried": "承载",
    "scenario": "场景", "scenarios": "场景", "real": "真实的", "refines": "打磨",
    "refined": "打磨", "opens": "打开；开场", "opened": "打开", "turns": "转变",
    "turned": "转变", "combine": "结合", "combines": "结合", "ideas": "想法",
    "reuse": "复用", "reuses": "复用", "own": "自己的", "words": "词语",
    "today's": "今天的", "fits": "适合", "fit": "适合", "well": "好",
}
STORY_LEMMAS = {
    "says": "say", "asks": "ask", "answers": "answer", "helps": "help",
    "checks": "check", "fixes": "fix", "learns": "learn", "shows": "show",
    "smiles": "smile", "explains": "explain", "records": "record", "finishes": "finish",
    "starts": "start", "leaves": "leave", "joins": "join", "merges": "merge",
    "pushes": "push", "pulls": "pull", "reviews": "review", "tests": "test",
    "plans": "plan", "notes": "note", "tasks": "task", "steps": "step",
    "changes": "change", "results": "result", "users": "user", "days": "day",
    "weeks": "week", "meetings": "meeting", "questions": "question", "errors": "error",
    "writes": "write", "looks": "look", "points": "point", "sees": "see",
    "needs": "need", "understands": "understand", "uses": "use", "suggests": "suggest",
    "compares": "compare", "talks": "talk", "tries": "try", "reads": "read",
    "hears": "hear", "watches": "watch", "thinks": "think", "makes": "make",
    "gives": "give", "tells": "tell", "feels": "feel", "meets": "meet",
    "keeps": "keep", "moves": "move", "decides": "decide", "confirms": "confirm",
    "discusses": "discuss", "documents": "document", "repeats": "repeat", "practises": "practice",
    "thanks": "thank", "orders": "order", "works": "work", "runs": "run",
    "hands": "hand", "minutes": "minute", "commits": "commit", "branches": "branch",
    "issues": "issue", "labels": "label",
    "gets": "get", "grows": "grow", "growing": "grow", "goes": "go",
    "weighs": "weigh", "raises": "raise", "raised": "raise", "walks": "walk",
    "sets": "set", "summarizes": "summarize", "summarised": "summarise",
    "adapts": "adapt", "carries": "carry", "builds": "build", "closes": "close",
    "collects": "collect", "presents": "present", "proposes": "propose", "reflects": "reflect",
    "supports": "support", "tracks": "track", "trains": "train",
    "stresses": "stress", "stressed": "stress", "agrees": "agree", "agreed": "agree",
    "prepares": "prepare", "prepared": "prepare", "repeated": "repeat",
    "replies": "reply", "responds": "respond", "responded": "respond", "greets": "greet",
    "mentions": "mention", "follows": "follow", "hold": "hold",
    "write": "write", "fit": "fit",
}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

# light scene-flow connectives for tiers 2-4
SCENE_LINKS = [
    ("After that,", "在那之后，"),
    ("Then,", "接着，"),
    ("Later,", "后来，"),
    ("After a short break,", "稍作休息后，"),
    ("Before the next meeting,", "下一个会议前，"),
    ("Once that was done,", "做完之后，"),
]


def cap(sentence: str) -> str:
    return sentence[:1].upper() + sentence[1:]


def np_form(term: str) -> str:
    lowered = term.strip().lower()
    if lowered in ARTLESS or lowered.startswith("the "):
        return term
    first = term.split()[0] if term.split() else ""
    if first == "GitHub":
        return term
    return f"the {term}"


def zh_core(item: dict) -> str:
    meaning = str(item.get("meaning", "")).strip()
    if item.get("domain") == "daily":
        return meaning
    return meaning.split("，", 1)[0].strip()


def term_kind(item: dict) -> str:
    """Route each item to a sentence shape that keeps grammar safe."""
    term = str(item.get("term", "")).strip()
    lowered = term.lower()
    if term.endswith("..."):
        return "pattern"
    if term.endswith((".", "?", "!")):
        return "line"
    if lowered in NP_ALWAYS:
        return "np"
    if lowered in VP_COMPOUNDS:
        return "vp"
    first = re.sub(r"[^a-z]", "", lowered.split()[0]) if lowered.split() else ""
    if item.get("domain") == "daily" and first in VERB_STARTS:
        return "vp"
    return "np"


def pick(pool: list, day: int, salt: int):
    return pool[(day + salt) % len(pool)]


def pick_seq(pool: list, day: int, cursor: dict, pool_id: str = "p"):
    """Day-shuffled rotation: a template is used at most once per day and the
    order differs from day to day, so no two days share the same sequence."""
    queue = cursor.setdefault(pool_id, [])
    if not queue:
        rng = random.Random(day * 1000 + sum(map(ord, pool_id)) + len(pool))
        queue.extend(rng.sample(range(len(pool)), len(pool)))
    item = pool[queue.pop(0)]
    cursor["n"] += 1
    return item


LINE_ACKS = {
    1: [("I answer politely.", "我礼貌地回应。"), ("I nod and reply.", "我点头回应。"), ("I answer with a smile.", "我微笑着回答。")],
    2: [("I answer as best I can.", "我尽力回答。"), ("I think for a second, then answer.", "我想了一下，然后回答。"), ("I reply, and we keep chatting.", "我回答后，我们继续聊。")],
    3: [("I answer, and we go over it once more.", "我回答后，我们又过了一遍。"), ("I reply, and she notes it down.", "我回答，她把它记了下来。"), ("I answer, then try the line myself.", "我回答，然后自己把这句练了一遍。")],
    4: [("I answer clearly and note the phrasing.", "我清楚地回答，并记下了这个说法。"), ("I answer, and we compare notes.", "我回答，我们互相对了笔记。"), ("I answer, then reuse it in my update.", "我回答，然后把它用进了自己的汇报。")],
    5: [("I repeat it and write it down.", "我跟读了一遍并记了下来。"), ("I try it back, and it works.", "我试着回了一遍，效果不错。")],
    6: [("I answer, and we run it once more.", "我回答后，我们又练了一次。"), ("I repeat it until it sounds natural.", "我反复念到它听起来自然。")],
    7: [("I answer from memory, then check my notes.", "我凭记忆回答，然后核对了笔记。"), ("I respond, and the mentor approves.", "我回应后，导师表示认可。")],
    8: [("I deliver the line without a pause.", "我毫不迟疑地说出了这句。"), ("I answer, and the room nods.", "我回答后，大家都点头。")],
}


def solo_line_sentence(item: dict, tier: int, day: int, cursor: dict) -> tuple[str, str]:
    term = str(item["term"]).strip()
    core = zh_core(item)
    verb, verbz = ("asks", "问") if term.endswith("?") else ("says", "说")
    en_t, zh_t = SOLO_LINE[tier]
    spk = SPEAKERS[(day + cursor["n"]) % len(SPEAKERS)]
    cursor["n"] += 1
    acks = LINE_ACKS.get(tier) or [("", "")]
    ack_en, ack_zh = acks[(day + cursor["n"]) % len(acks)]
    cursor["n"] += 1
    en = cap(en_t.format(spk=spk, verb=verb, d1=term, d1z=core))
    zh = zh_t.format(spk=spk, verbz=verbz, d1z=core)
    if ack_en:
        en = f"{en} {ack_en}"
        zh = f"{zh}{ack_zh}"
    return en, zh


NP_PLURAL_SWAP = {
    "This is {np}.": ("These are {np}.", "这些是{z}。"),
    "{np_cap} is new to me.": ("{np_cap} are new to me.", "{z}对我来说很新。"),
    "If {np} fails, we need a clear plan.": ("If {np} fail, we need a clear plan.", "如果{z}失败，我们需要一个清晰的方案。"),
}


def term_sentence(item: dict, tier: int, day: int, cursor: dict) -> tuple[str, str]:
    kind = term_kind(item)
    term = str(item["term"]).strip()
    core = zh_core(item)
    if kind == "np":
        en_t, zh_t = pick_seq(NP_POOL[tier], day, cursor, f"np{tier}")
        if term.lower() in PLURAL_NPS and en_t in NP_PLURAL_SWAP:
            en_t, zh_t = NP_PLURAL_SWAP[en_t]
        np = np_form(term)
        en = en_t.format(np=np, np_cap=cap(np))
        zh = zh_t.format(z=core)
    elif kind == "vp":
        pool = VP_LIFE_POOL[tier] if item.get("domain") == "daily" else VP_POOL[tier]
        en_t, zh_t = pick_seq(pool, day, cursor, f"vp{tier}")
        en = en_t.format(vp=term)
        zh = zh_t.format(vz=core)
    elif kind == "pattern":
        en_t, zh_t = pick_seq(PATTERN_POOL[tier], day, cursor, f"pat{tier}")
        en = en_t.format(dl=term)
        zh = zh_t.format(dlz=core)
    else:  # a complete spoken line without a partner line: narrate it alone
        return solo_line_sentence(item, tier, day, cursor)
    starts_with_time = en[:2] in ("At", "In", "On") or en.split(",")[0].split()[0] in (
        "Before", "After", "During", "Once", "When", "While", "Then", "Later", "Today", "Tomorrow", "Yesterday")
    if 2 <= tier <= 4 and not starts_with_time and (day * 7 + cursor["n"]) % 3 == 0:
        c_en, c_zh = SCENE_LINKS[(day + cursor["n"]) % len(SCENE_LINKS)]
        en = f"{c_en} {en}"
        zh = c_zh + zh
    return cap(en), zh


def dialogue_sentence(d1: dict, d2: dict, tier: int, day: int, cursor: dict) -> tuple[str, str]:
    t1, t2 = str(d1["term"]).strip(), str(d2["term"]).strip()
    if norm_term(t1) == norm_term(t2):
        en_t, zh_t = pick_seq(ECHO_SOLE[tier], day, cursor, f"echo{tier}")
    else:
        en_t, zh_t = pick_seq(DLG_POOL[tier], day, cursor, f"dlg{tier}")
    spk = SPEAKERS[(day + cursor["n"]) % len(SPEAKERS)]
    cursor["n"] += 1
    closers = DLG_CLOSERS.get(tier) or [("", "")]
    closer_en, closer_zh = closers[(day + cursor["n"]) % len(closers)]
    cursor["n"] += 2
    en = cap(en_t.format(spk=spk, d1=t1, d2=t2, cz=closer_en, d1z=zh_core(d1), d2z=zh_core(d2)))
    zh = zh_t.format(spk=spk, cz=closer_zh, d1z=zh_core(d1), d2z=zh_core(d2))
    return en, zh


def render_items(items: list[dict], tier: int, day: int, cursor: dict) -> list[tuple[str, str]]:
    """Render a scene's items. Tiers 1-4: each spoken line stands alone with a
    natural reply beat (two learned lines never pretend to be one conversation).
    Tiers 5-8 keep the practice-framed three-turn drills."""
    out: list[tuple[str, str]] = []
    pending_line: dict | None = None
    for item in items:
        if term_kind(item) == "line":
            if tier <= 4:
                out.append(solo_line_sentence(item, tier, day, cursor))
                continue
            if pending_line is None:
                pending_line = item
                continue
            out.append(dialogue_sentence(pending_line, item, tier, day, cursor))
            pending_line = None
            continue
        if pending_line is not None:
            out.append(solo_line_sentence(pending_line, tier, day, cursor))
            pending_line = None
        out.append(term_sentence(item, tier, day, cursor))
    if pending_line is not None:
        out.append(solo_line_sentence(pending_line, tier, day, cursor))
    return out


# closing reactions for 3-turn dialogues; generic on purpose so they fit any exchange
DLG_CLOSERS = {
    5: [
        ("Good — try it in today’s task.", "好——今天的任务里就用上。"),
        ('That is the one we need today.', '今天要的就是这句。'),
        ('Nice, keep that one handy.', '不错，把这句记在手边。'),
    ],
    6: [
        ('Good point — use it in the standup.', '说得好——站会上就用它。'),
        ('Exactly, and it saves time too.', '正是，而且还省时间。'),
        ('Keep practising, it is working.', '继续练，有效果了。'),
    ],
    7: [
        ('Strong answer — keep that precision.', '回答有力——保持这种精确。'),
        ('Agreed, note it in the ticket.', '同意，把这条记到工单里。'),
        ('That is the level we need.', '我们要的就是这个水平。'),
    ],
    8: [
        ('Approved — bring it to the launch review.', '通过——带到上线评审上。'),
        ('Well said, that stays in the deck.', '说得好，这句留在材料里。'),
        ('Confirmed. This is launch ready.', '确认无误，可以上线了。'),
    ],
}

def build_scene(day: int, tier: int, scene: int, groups: list[dict], plot: dict, cursor: dict) -> tuple[str, str]:
    computer, daily, github = (g.get("items", []) for g in groups)
    start = (scene - 1) * 2
    c = computer[start:start + 2]
    d = daily[start:start + 2]
    g = github[start:start + 2]

    en_parts: list[str] = []
    zh_parts: list[str] = []

    if scene == 1:
        en_parts.append(plot["open_en"])
        zh_parts.append(plot["open_zh"])
        blocks = [c, g, d]
    elif scene == 2:
        en_parts.append(plot["life_en"])
        zh_parts.append(plot["life_zh"])
        blocks = [d, c, g]
    else:
        intro_en, intro_zh = SEG3_INTRO[tier]
        en_parts.append(intro_en)
        zh_parts.append(intro_zh)
        blocks = [g, c, d]

    for items in blocks:
        for en, zh in render_items(items, tier, day, cursor):
            en_parts.append(en)
            zh_parts.append(zh)

    if scene == 3:
        en_parts.append(plot["close_en"])
        zh_parts.append(plot["close_zh"])
    else:
        close_en, close_zh = pick(SCENE_CLOSE_POOL[tier], day, scene)
        en_parts.append(close_en)
        zh_parts.append(close_zh)

    return " ".join(en_parts), "".join(zh_parts)


def hard_type(item: dict) -> str:
    part = str(item.get("part", ""))
    if "术语" in part or "技术" in part:
        return "term"
    if item.get("domain") == "daily":
        return "idiom"
    return "term"


def segment_for_scene(day: int, tier: int, scene: int, groups: list[dict], plot: dict, cursor: dict) -> dict:
    cursor["n"] += (scene - 1) * 5  # rotate templates/closers per scene
    en, zh = build_scene(day, tier, scene, groups, plot, cursor)
    start = (scene - 1) * 2
    terms = []
    for group in groups:
        terms.extend(group.get("items", [])[start:start + 2])
    hard = [{"w": item["term"], "type": hard_type(item), "def": str(item.get("meaning", ""))} for item in terms]
    return {
        "id": f"seg-{scene:02d}",
        "spk": "Alex",
        "en": en,
        "tts": speech_text(en),
        "audio_file": f"audio/seg-{scene:02d}.mp3",
        "zh": zh,
        "hard": hard,
    }


def make_lesson(day_data: dict, plot: dict, tier: int, lexicon: dict, lemmas: dict) -> dict:
    day = int(day_data["day"])
    groups = day_data.get("groups", [])
    meta_tier = TIER_META[tier]
    cursor = {"n": 0}
    segments = [segment_for_scene(day, tier, scene, groups, plot, cursor) for scene in (1, 2, 3)]
    assert_coverage(day, groups, segments)

    all_items = [item for group in groups for item in group.get("items", [])]
    chunk_items = [group["items"][idx] for group in groups for idx in (0, 3)]
    chunks = [
        {"t": item["term"], "cn": zh_core(item), "eg": item.get("example", "")}
        for item in chunk_items if item.get("term")
    ]
    topics = " × ".join(str(group.get("topic", "")) for group in groups)
    word_count = sum(len(segment["en"].split()) for segment in segments)
    genre = TRANSFER_GENRES[(day - 1) % len(TRANSFER_GENRES)]

    merged_lexicon = {}
    for item in all_items:
        term = str(item.get("term", "")).strip()
        if term and " " not in term:
            merged_lexicon[term.lower()] = {"def": str(item.get("meaning", "")).strip()}
    for word, definition in lexicon.items():
        merged_lexicon.setdefault(word, {"def": definition})
    for inflected, lemma in lemmas.items():
        merged_lexicon.setdefault(inflected, {"lemma": lemma})

    return {
        "meta": {
            "title": f"Day {day}: {plot['title_en']}",
            "title_zh": f"第 {day} 天：{plot['title_zh']}",
            "source": f"Vocabulary Year · Day {day}",
            "url": "",
            "kind": "article",
            "lang": "en",
            "study_card": {
                "word_count": word_count,
                "segment_count": len(segments),
                "difficulty": f"{meta_tier['name']} · 词汇主线",
                "estimated_days": 1,
                "main_practice": meta_tier["practice"],
                "value_points": [
                    "当天 18 个词汇全部进入故事正文",
                    topics,
                    f"{meta_tier['name']} · 语速与句长随天数递增",
                ],
                "suggested_pace": meta_tier["pace"],
            },
        },
        "voice": {"engine": "edge", "voice": "en-US-AndrewNeural",
                  "rate": meta_tier["rate"], "speed": meta_tier["speed"]},
        "segments": segments,
        "chunks": chunks,
        "patterns": PATTERNS_BY_TIER[tier],
        "transfer_tasks": [{
            "genre": genre,
            "task": f"Use any three Day {day} vocabulary items. Retell Alex's story in your own words, then say what you did, what was difficult, and what you will do next.",
            "hint_chunks": [chunk["t"] for chunk in chunks[:3]],
        }],
        "lexicon": merged_lexicon,
    }


# ---------------------------------------------------------------------------
# coverage contract: all 18 items must appear in the spoken English
# ---------------------------------------------------------------------------

def norm_text(text: str) -> str:
    text = str(text or "").lower().replace("’", "'").replace("'", "").replace("...", " ")
    return re.sub(r"\s+", " ", text).strip()


def norm_term(term: str) -> str:
    return norm_text(str(term or "").rstrip(".!?"))


def assert_coverage(day: int, groups: list[dict], segments: list[dict]) -> None:
    haystack = norm_text(" ".join(segment["en"] for segment in segments))
    missing = []
    count = 0
    for group in groups:
        for item in group.get("items", []):
            count += 1
            if norm_term(item.get("term", "")) not in haystack:
                missing.append(str(item.get("term", "")))
    if count != 18:
        raise ValueError(f"day {day}: expected 18 vocabulary items, found {count}")
    if missing:
        raise ValueError(f"day {day}: vocabulary missing from story: {', '.join(missing)}")


# ---------------------------------------------------------------------------
# course assembly
# ---------------------------------------------------------------------------

def apply_month_hints(doc: dict) -> None:
    """Merge per-month routing hints from a story data file into the global sets."""
    for hint in doc.get("vp", []) or []:
        VP_COMPOUNDS.add(str(hint).lower())
    for hint in doc.get("np_always", []) or []:
        NP_ALWAYS.add(str(hint).lower())
    for hint in doc.get("plural", []) or []:
        PLURAL_NPS.add(str(hint).lower())
    for hint in doc.get("artless", []) or []:
        ARTLESS.add(str(hint).lower())
    for word, definition in (doc.get("lexicon") or {}).items():
        STORY_LEXICON.setdefault(str(word).lower(), str(definition))
    for inflected, lemma in (doc.get("lemmas") or {}).items():
        STORY_LEMMAS.setdefault(str(inflected).lower(), str(lemma))


def load_plots(course_id: str) -> list[dict]:
    plots: list[dict] = []
    for doc in load_content_month_files(course_id, "story"):
        month_plots = doc.get("plots", [])
        if len(month_plots) > 35:
            raise SystemExit(f"{doc['_file']}: at most 35 plot frames per file, found {len(month_plots)}")
        apply_month_hints(doc)
        plots.extend(month_plots)
    return plots


def write_course_index(course_id: str, config: dict, plots: list[dict], tier_of) -> Path:
    """Course home: day list grouped into month sections."""
    total = len(plots)
    sections = []
    days_per_month = 30
    month_count = (total + days_per_month - 1) // days_per_month
    month_titles = {
        1: "入职第一个月", 2: "第一个真实任务", 3: "上线与发布", 4: "质量与可靠",
        5: "协作与流程", 6: "数据与洞察", 7: "AI 工具上手", 8: "性能与优化",
        9: "安全与合规", 10: "独立产品", 11: "架构与决策", 12: "带团队与毕业",
    }
    for month in range(1, month_count + 1):
        start_day = (month - 1) * days_per_month + 1
        end_day = min(total, month * days_per_month)
        rows = []
        for day in range(start_day, end_day + 1):
            plot = plots[day - 1]
            tier_name = TIER_META[tier_of(day)]["name"]
            rows.append(
                f'<li><a href="day-{day:03d}/index.html"><h2>Day {day} · {plot["title_zh"]}</h2>'
                f'<p>{tier_name} · {plot["title_en"]}</p></a></li>'
            )
        label = month_titles.get(month, f"第 {month} 个月")
        sections.append(
            f'<section class="month-block"><h2 class="month-title">第 {month} 月 · {label}</h2>'
            f'<ul>{"".join(rows)}</ul></section>'
        )
    built = total
    target = config["days"]
    progress = (
        f'<div class="course-progress">已构建 <b>{built}</b> / {target} 天'
        + ("" if built >= target else " · 内容持续更新中") + "</div>"
    )
    html = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{config["title"]}</title><style>body{{font-family:-apple-system,sans-serif;max-width:820px;margin:0 auto;padding:32px 20px;line-height:1.6;background:#fafafa;color:#222}}h1{{font-size:28px;margin-bottom:4px}}.sub{{color:#666;margin-bottom:8px}}.course-progress{{color:#2d6b55;font-size:14px;margin-bottom:24px}}.month-block{{margin:26px 0}}.month-title{{font-size:19px;margin:0 0 10px;color:#163e33;border-bottom:2px solid #dfe8e4;padding-bottom:6px}}ul{{list-style:none;padding:0;margin:0}}li{{background:#fff;border:1px solid #e3e3e3;border-radius:10px;margin:8px 0;overflow:hidden}}a{{display:block;padding:12px 18px;text-decoration:none;color:#222}}a:hover{{background:#f0f7ff}}h2{{margin:0 0 3px;font-size:16px;font-weight:600}}li p{{margin:0;color:#666;font-size:13px}}.vocab-entry{{display:block;margin:22px 0 10px;padding:22px;border-radius:16px;background:linear-gradient(135deg,#163e33,#2d6b55);color:white;text-decoration:none}}.vocab-entry strong{{display:block;font-size:21px}}.vocab-entry span{{display:block;margin-top:4px;color:rgba(255,255,255,.78);font-size:14px}}.home-link{{display:inline-block;margin:8px 0 20px;color:#2d6b55;text-decoration:none;font-size:14px}}</style></head><body><h1>{config["title"]}</h1><p class="sub">{config["subtitle"]}</p>{progress}<a class="home-link" href="../../index.html">← 全部课程</a><a class="vocab-entry" href="vocabulary-month/"><strong>{config["vocab_title"]} →</strong><span>{config["vocab_subtitle"]}</span></a>{"".join(sections)}</body></html>'''
    out = ROOT / "lessons" / "week" / "courses" / course_id / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--course", default="speaking-vocab")
    args = parser.parse_args()
    course_id = args.course
    config = load_course_config(course_id)

    vocab_course = build_vocab_course(course_id)
    plots = load_plots(course_id)
    days = vocab_course["days"]
    if len(plots) != len(days):
        raise SystemExit(
            f"story frames ({len(plots)}) and vocabulary days ({len(days)}) are out of sync for {course_id}"
        )

    tier_of = make_tier_of(config.get("tier_bands", DEFAULT_TIER_BANDS))
    days_dir = ROOT / "examples" / "courses" / course_id / "days"
    out_dir = ROOT / "lessons" / "week" / "courses" / course_id
    for day_data, plot in zip(days, plots):
        day = int(day_data["day"])
        tier = tier_of(day)
        lesson = make_lesson(day_data, plot, tier, STORY_LEXICON, STORY_LEMMAS)
        out = days_dir / f"day-{day:03d}" / "segments.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(lesson, ensure_ascii=False, indent=1), encoding="utf-8")
    index_path = write_course_index(course_id, config, plots, tier_of)
    print(f"written {len(days)} progressive story lessons to {days_dir}")
    print(f"course home: {index_path}")


if __name__ == "__main__":
    main()
