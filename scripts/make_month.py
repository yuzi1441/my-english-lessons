#!/usr/bin/env python3
"""Generate days 8-28 for the first month of Immersion Reader lessons.

Week 1 is the existing beginner engineer story.  This file adds three
progressive weeks: Python/data, project/research English, and AI workflow.
"""
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WEEK_DIR = ROOT / "examples" / "custom" / "week"


def segment(en: str, zh: str, hard: list[tuple[str, str, str]]) -> dict:
    return {
        "en": en,
        "tts": en,
        "zh": zh,
        "hard": [{"w": word, "type": kind, "def": definition} for word, kind, definition in hard],
    }


def lesson(
    day: int,
    title: str,
    title_zh: str,
    week: int,
    segments: list[dict],
    chunks: list[dict],
    patterns: list[dict],
    genre: str,
    task: str,
) -> dict:
    normalized = []
    lexicon = {}
    for idx, item in enumerate(segments, 1):
        normalized.append({"id": f"seg-{idx:02d}", **item})
        for item_hard in item["hard"]:
            word = item_hard["w"]
            if " " not in word:
                lexicon[word.lower()] = {"def": item_hard["def"]}
    return {
        "meta": {
            "title": title,
            "title_zh": title_zh,
            "source": f"Month 1 · Week {week} · Day {day}",
            "url": "",
            "kind": "article",
            "lang": "en",
            "study_card": {
                "word_count": sum(len(item["en"].split()) for item in normalized),
                "segment_count": len(normalized),
                "difficulty": "入门进阶",
                "estimated_days": 1,
                "main_practice": "跟读 + 精读 + 中文讲解对照",
                "value_points": [chunks[0]["cn"], chunks[1]["cn"], "每日一次英文小练习"],
                "suggested_pace": "先猜大意 · 再听读 · 最后完成英文输出",
            },
        },
        "voice": {"engine": "edge", "voice": "en-US-AndrewNeural", "rate": "-20%", "speed": 0.8},
        "segments": normalized,
        "chunks": chunks,
        "patterns": patterns,
        "transfer_tasks": [{"genre": genre, "task": task, "hint_chunks": [item["t"] for item in chunks[:3]]}],
        "lexicon": lexicon,
    }


W = "word"
T = "term"


LESSONS = [
    lesson(8, "Lesson 8: Open the Python Notebook", "第 8 课：打开 Python 笔记本", 2, [
        segment("On Monday, I start the Python week. I open a notebook on my computer. A notebook lets me write code and see the result below it. I type a small line: print hello. The code runs, and I see the word hello. It feels simple, but I am happy.", "周一我开始 Python 学习周。我在电脑上打开一个 notebook（笔记本）。它可以让我写代码，并在下面看到结果。我输入一行小代码 print hello，代码运行后，我看到了 hello。虽然简单，但我很开心。讲解：notebook=代码笔记本，run=运行，result=结果。", [("notebook", T, "代码笔记本"), ("result", W, "结果"), ("run", W, "运行")]),
        segment("I make a new folder for the project. I give it a clear name. Clear names help me find files later. I also write a short note about the goal: read a small data file. The goal is not big. A small goal is easier to finish.", "我为项目建了一个新文件夹，并给它起了清楚的名字。清楚的名字能帮助我以后找到文件。我还写下目标：读取一个小数据文件。目标不大，小目标更容易完成。讲解：folder=文件夹，clear=清楚的，goal=目标，finish=完成。", [("folder", W, "文件夹"), ("clear", W, "清楚的"), ("goal", W, "目标")]),
        segment("Before I learn more commands, I save my work. I say the first sentence in English: I am learning Python one small step at a time. This sentence is easy, but it is useful. I read it aloud twice. English and code can grow together.", "在学习更多命令前，我先保存工作。我用英语说：我一步一步学习 Python。这句话很简单，但很有用。我大声读了两遍。英语和代码可以一起进步。讲解：save=保存，aloud=大声地，grow together=一起成长。", [("save", W, "保存"), ("aloud", W, "大声地"), ("step at a time", T, "一步一步")]),
    ], [{"t": "open a notebook", "cn": "打开代码笔记本", "eg": "I open a notebook for the project."}, {"t": "clear name", "cn": "清楚的名字", "eg": "Use a clear name for the file."}, {"t": "one step at a time", "cn": "一步一步", "eg": "I learn Python one step at a time."}, {"t": "save my work", "cn": "保存我的工作", "eg": "I save my work before I stop."}], [{"t": "A notebook lets me X.", "cn": "笔记本让我可以 X。"}, {"t": "A small goal is easier to X.", "cn": "小目标更容易 X。"}, {"t": "I am learning X one step at a time.", "cn": "我一步一步学习 X。"}], "standup_update", "Write 3 short sentences about starting a Python project. Use open a notebook, clear name, and save my work."),
    lesson(9, "Lesson 9: Names and Values", "第 9 课：名字与值", 2, [
        segment("Today I learn variables. A variable is a name for a value. I write name equals Alex. The name is Alex. Then I write minutes equals twenty. The value is twenty. A good variable name tells me what the value means.", "今天我学习变量。变量就是一个值的名字。我写 name 等于 Alex，值是 Alex。然后写 minutes 等于 twenty，值是 twenty。好的变量名会告诉我这个值是什么意思。讲解：variable=变量，value=值，mean=意思是。", [("variable", T, "变量"), ("value", T, "值"), ("mean", W, "意思是")]),
        segment("I change the value of minutes. At first, it is ten. Later, it is twenty. The name stays the same, but the value changes. This is useful when a program needs to remember new information. I read the code slowly and say each line.", "我改变 minutes 的值。开始是十，后来变成二十。名字不变，但值变了。当程序需要记住新信息时，这很有用。我慢慢读代码，并把每一行说出来。讲解：at first=起初，later=后来，stay the same=保持不变，information=信息。", [("at first", T, "起初"), ("later", W, "后来"), ("information", W, "信息")]),
        segment("Numbers and text are different kinds of values. A number can be added. Text can be joined. If I mix them by mistake, Python may show an error. I do not panic. I read the message and check the values again.", "数字和文本是不同类型的值。数字可以相加，文本可以连接。如果我不小心把它们混在一起，Python 可能会显示错误。我不慌，先读错误信息，再重新检查值。讲解：kind=种类，join=连接，mix=混合，panic=慌张。", [("text", T, "文本"), ("join", W, "连接"), ("panic", W, "慌张")]),
    ], [{"t": "a name for a value", "cn": "一个值的名字", "eg": "A variable is a name for a value."}, {"t": "stay the same", "cn": "保持不变", "eg": "The name can stay the same."}, {"t": "by mistake", "cn": "错误地;不小心地", "eg": "I mixed the values by mistake."}, {"t": "read the message", "cn": "阅读提示信息", "eg": "Read the message before you change code."}], [{"t": "A variable is X.", "cn": "变量是 X。"}, {"t": "The name stays the same, but X changes.", "cn": "名字保持不变，但 X 发生变化。"}, {"t": "I do not panic.", "cn": "我不慌。"}], "standup_update", "Write 3 short sentences explaining a variable. Use a name for a value, stay the same, and by mistake."),
    lesson(10, "Lesson 10: Small Functions", "第 10 课：小函数", 2, [
        segment("A function is a small group of instructions. I give the function a name: greet. When I call greet, it says hello. I do not write the same code many times. I write it once and use it again. This makes the program easier to read.", "函数是一小组指令。我给函数起名 greet。调用 greet 时，它会说 hello。我不需要把同样的代码写很多遍，只写一次，然后重复使用。这样程序更容易阅读。讲解：function=函数，instruction=指令，call a function=调用函数。", [("function", T, "函数"), ("instruction", T, "指令"), ("call", W, "调用")]),
        segment("Some functions take an input. I make a function called double. It takes a number and returns the number times two. I give it three, and it returns six. The function has one clear job. Clear jobs are easier to test.", "有些函数接收输入。我写一个叫 double 的函数，它接收一个数字，并返回这个数字乘以二。我给它三，它返回六。这个函数只有一个清楚的任务。任务清楚，测试就容易。讲解：input=输入，return=返回，times=乘以，job=任务。", [("input", T, "输入"), ("return", T, "返回"), ("clear job", T, "清楚的任务")]),
        segment("I write a short test for double. I expect double three to be six. The test passes. I feel more confident because the code has a small proof. A function and a test work well together.", "我为 double 写一个小测试。我期待 double three 的结果是 six，测试通过了。有了这个小证明，我更有信心。函数和测试很适合一起工作。讲解：expect=期待，pass=通过，confident=有信心的，proof=证明。", [("expect", W, "期待"), ("confident", W, "有信心的"), ("proof", W, "证明")]),
    ], [{"t": "a group of instructions", "cn": "一组指令", "eg": "A function is a group of instructions."}, {"t": "take an input", "cn": "接收一个输入", "eg": "This function takes an input."}, {"t": "return a value", "cn": "返回一个值", "eg": "The function returns a value."}, {"t": "work well together", "cn": "配合得很好", "eg": "Tests and functions work well together."}], [{"t": "It takes X and returns Y.", "cn": "它接收 X 并返回 Y。"}, {"t": "I expect X to be Y.", "cn": "我期待 X 是 Y。"}, {"t": "The test passes.", "cn": "测试通过了。"}], "code_review_comment", "Write a short code review comment about a function. Use take an input, return a value, and work well together."),
    lesson(11, "Lesson 11: Lists and Tables", "第 11 课：列表与表格", 2, [
        segment("Today I use a list. A list holds several values in one place. I make a list of prices: ten, twelve, and fifteen. The first item has position zero. Python starts counting at zero. I check the first item and see ten.", "今天我使用列表。列表把多个值放在一个地方。我建立一个价格列表：十、十二和十五。第一个项目的位置是零。Python 从零开始计数。我检查第一个项目，看到十。讲解：list=列表，hold=容纳，item=项目，position=位置。", [("list", T, "列表"), ("hold", W, "容纳"), ("item", W, "项目")]),
        segment("A table has rows and columns. A row can describe one company. The columns can hold a name, a price, and a date. I do not need to remember every number. I let the table keep the structure for me.", "表格有行和列。一行可以描述一家公司，列可以放名字、价格和日期。我不需要记住每个数字，让表格帮我保存结构。讲解：row=行，column=列，describe=描述，structure=结构。", [("row", T, "行"), ("column", T, "列"), ("structure", W, "结构")]),
        segment("I loop through the list and print each price. The computer repeats the same action. I watch the output. One price is wrong, so I check the original list. Small checks help me trust the data.", "我遍历列表并打印每个价格，电脑会重复同一个动作。我观察输出，发现一个价格不对，于是检查原始列表。小检查能帮助我相信数据。讲解：loop through=遍历，output=输出，original=原始的，trust=相信。", [("loop through", T, "遍历"), ("output", W, "输出"), ("trust", W, "相信")]),
    ], [{"t": "hold several values", "cn": "容纳多个值", "eg": "A list holds several values."}, {"t": "at position zero", "cn": "在零号位置", "eg": "The first item is at position zero."}, {"t": "loop through", "cn": "遍历", "eg": "We loop through the list."}, {"t": "trust the data", "cn": "相信数据", "eg": "Small checks help us trust the data."}], [{"t": "A list holds X.", "cn": "列表容纳 X。"}, {"t": "The first item is at X.", "cn": "第一个项目在 X。"}, {"t": "I check X.", "cn": "我检查 X。"}], "design_note", "Write 3 short sentences describing a small data table. Use hold several values, loop through, and trust the data."),
    lesson(12, "Lesson 12: Read a JSON File", "第 12 课：读取 JSON 文件", 2, [
        segment("My data is in a JSON file. JSON is a simple text format. It stores names and values with clear labels. I open the file and read it with Python. The program turns the text into a structure I can use.", "我的数据在一个 JSON 文件里。JSON 是一种简单的文本格式，用清楚的标签保存名字和值。我打开文件并用 Python 读取它，程序把文本变成我可以使用的结构。讲解：format=格式，label=标签，store=保存，turn into=变成。", [("format", T, "格式"), ("label", W, "标签"), ("store", W, "保存")]),
        segment("The file has a list of prices. I ask Python for the price of one company. If the name exists, I get a number. If it does not exist, I get nothing. I check the name before I use the result.", "文件里有一个价格列表。我向 Python 请求某家公司的价格。如果名字存在，我会得到一个数字；如果不存在，就什么也得不到。我在使用结果前先检查名字。讲解：exist=存在，result=结果，nothing=什么也没有。", [("exist", W, "存在"), ("result", W, "结果"), ("nothing", W, "什么也没有")]),
        segment("I save a clean copy after reading the file. I keep the original file safe. This small habit protects my work. When the program changes, I can compare the new data with the old data.", "读完文件后，我保存一份干净的副本，并把原始文件保护好。这个小习惯能保护我的工作。当程序发生变化时，我可以把新数据和旧数据进行比较。讲解：copy=副本，protect=保护，compare=比较，habit=习惯。", [("protect", W, "保护"), ("compare", W, "比较"), ("habit", W, "习惯")]),
    ], [{"t": "a text format", "cn": "文本格式", "eg": "JSON is a simple text format."}, {"t": "turn text into a structure", "cn": "把文本变成结构", "eg": "Python turns text into a structure."}, {"t": "if the name exists", "cn": "如果名字存在", "eg": "I get a price if the name exists."}, {"t": "keep the original safe", "cn": "保护原始文件", "eg": "Keep the original file safe."}], [{"t": "It stores X with Y.", "cn": "它用 Y 保存 X。"}, {"t": "If X exists, I get Y.", "cn": "如果 X 存在，我得到 Y。"}, {"t": "I can compare X with Y.", "cn": "我可以比较 X 和 Y。"}], "design_note", "Write a short data note about reading JSON. Use a text format, if the name exists, and keep the original safe."),
    lesson(13, "Lesson 13: Find the Error", "第 13 课：找到错误", 2, [
        segment("My program stops with an error. The message says that a key is missing. I read the last line first. It tells me where the program stopped. Then I look at the data and find a different spelling.", "我的程序因为错误停止了。错误信息说一个 key（键）缺失。我先读最后一行，它告诉我程序停在哪里。然后我查看数据，发现拼写不一样。讲解：error message=错误信息，missing=缺失的，spelling=拼写。", [("missing", W, "缺失的"), ("spelling", W, "拼写"), ("stop", W, "停止")]),
        segment("I fix the spelling and run the program again. This time, another error appears. Debugging is not one big jump. It is a series of small checks. I fix one problem, run again, and learn from the next message.", "我修正拼写，再次运行程序。这次出现了另一个错误。debugging（调试）不是一次大跳跃，而是一连串小检查。我修一个问题，再运行，再从下一条信息中学习。讲解：debug=调试，series=一连串，appear=出现。", [("debugging", T, "调试"), ("series", W, "一连串"), ("appear", W, "出现")]),
        segment("At the end, the program runs. I write down what happened. The note will help me next time. I am not afraid of errors now. An error is a message that can guide me.", "最后程序运行了。我记下发生了什么，这条笔记下次会帮助我。现在我不再害怕错误。错误是一条可以指导我的信息。讲解：write down=记下，guide=指导，at the end=最后。", [("write down", T, "记下"), ("guide", W, "指导"), ("at the end", T, "最后")]),
    ], [{"t": "the last line", "cn": "最后一行", "eg": "Read the last line first."}, {"t": "run again", "cn": "再次运行", "eg": "Fix the code and run again."}, {"t": "a series of small checks", "cn": "一连串小检查", "eg": "Debugging is a series of small checks."}, {"t": "write down", "cn": "记下", "eg": "Write down what happened."}], [{"t": "The message tells me X.", "cn": "信息告诉我 X。"}, {"t": "This time, Y appears.", "cn": "这次出现了 Y。"}, {"t": "I am not afraid of X.", "cn": "我不害怕 X。"}], "slack_message", "Write a short team message about fixing an error. Use the last line, run again, and write down."),
    lesson(14, "Lesson 14: Python Week Review", "第 14 课：Python 周复习", 2, [
        segment("This week I opened a notebook and used variables. I made a small function and tested it. I put values in a list and read a JSON file. These actions are small, but they are the basic steps of a useful program.", "这周我打开了 notebook，使用了变量。我写了一个小函数并测试它，把值放进列表，还读取了 JSON 文件。这些动作很小，却是实用程序的基础步骤。讲解：basic=基础的，action=动作，useful=有用的。", [("basic", W, "基础的"), ("action", W, "动作"), ("useful", W, "有用的")]),
        segment("I also learned how to debug. When an error appears, I read the message and check one thing at a time. I do not need to understand everything at once. I only need the next clear step.", "我还学会了怎样调试。出现错误时，我读信息，一次检查一件事。我不需要一下子理解所有内容，只需要找到下一步清楚的动作。讲解：at once=一下子，next step=下一步，clear=清楚的。", [("at once", T, "一下子"), ("next step", T, "下一步"), ("understand", W, "理解")]),
        segment("For next week, I will use Python with a small table of real data. I will read it, clean it, and ask one simple question. Learning works when I practice a little every day.", "下周我会用 Python 处理一张真实数据小表。我会读取、清理数据，再问一个简单问题。每天练习一点，学习就会有效果。讲解：real data=真实数据，clean data=清理数据，practice=练习。", [("real data", T, "真实数据"), ("clean", W, "清理"), ("practice", W, "练习")]),
    ], [{"t": "the basic steps", "cn": "基础步骤", "eg": "These are the basic steps."}, {"t": "one thing at a time", "cn": "一次一件事", "eg": "Check one thing at a time."}, {"t": "the next clear step", "cn": "下一步清楚的动作", "eg": "Find the next clear step."}, {"t": "practice every day", "cn": "每天练习", "eg": "I practice a little every day."}], [{"t": "This week I X.", "cn": "这周我做了 X。"}, {"t": "I do not need to X at once.", "cn": "我不需要一下子 X。"}, {"t": "Learning works when X.", "cn": "当 X 时，学习会有效果。"}], "standup_update", "Write a weekly review with three sentences. Use the basic steps, one thing at a time, and practice every day."),
    lesson(15, "Lesson 15: Ask a Good Data Question", "第 15 课：提出一个好的数据问题", 3, [
        segment("I start a small research project. Before I open the data, I write one question. I ask: did the company's sales grow this year? A clear question gives the project a direction. Without a question, a table is only a pile of numbers.", "我开始一个小研究项目。在打开数据前，我先写下一个问题：这家公司的销售额今年增长了吗？清楚的问题会给项目一个方向。没有问题，表格只是一堆数字。讲解：research=研究，sales=销售额，direction=方向，pile=一堆。", [("research", T, "研究"), ("sales", W, "销售额"), ("direction", W, "方向")]),
        segment("I decide what to measure. I need sales for two years, not every number in the report. I write the source next to each value. A source helps another person check my work.", "我决定测量什么。我需要两年的销售额，而不是报告里的每一个数字。我把来源写在每个值旁边。来源能帮助另一个人检查我的工作。讲解：measure=测量，report=报告，source=来源，value=数值。", [("measure", W, "测量"), ("source", T, "来源"), ("value", W, "数值")]),
        segment("The first result is not surprising. Sales grew a little. I do not tell a big story yet. I check the period, the unit, and the original document. Good research starts with a small, testable question.", "第一个结果并不意外，销售额增长了一点。我暂时不讲一个很大的故事，而是检查期间、单位和原始文件。好的研究从一个小而可验证的问题开始。讲解：surprising=令人意外的，period=期间，unit=单位，testable=可验证的。", [("period", W, "期间"), ("unit", W, "单位"), ("testable", W, "可验证的")]),
    ], [{"t": "give the project a direction", "cn": "给项目一个方向", "eg": "A clear question gives the project a direction."}, {"t": "what to measure", "cn": "要测量什么", "eg": "Decide what to measure first."}, {"t": "next to each value", "cn": "在每个数值旁边", "eg": "Write the source next to each value."}, {"t": "tell a big story", "cn": "讲一个很大的故事", "eg": "Do not tell a big story too early."}], [{"t": "I ask: X?", "cn": "我问：X 吗？"}, {"t": "I need X, not Y.", "cn": "我需要 X，而不是 Y。"}, {"t": "I do not X yet.", "cn": "我暂时不 X。"}], "design_note", "Write a research question and two data rules. Use what to measure, next to each value, and tell a big story."),
    lesson(16, "Lesson 16: Clean the Data", "第 16 课：清理数据", 3, [
        segment("The table has three empty cells. Empty cells are not zero. I mark them as missing. If I change them to zero, the average will be wrong. I also find two dates with different formats. I make the format the same.", "表格里有三个空单元格。空单元格不等于零，我把它们标记为缺失。如果把它们改成零，平均值就会错误。我还发现两个日期格式不同，于是统一格式。讲解：empty=空的，missing=缺失的，average=平均值，format=格式。", [("empty", W, "空的"), ("missing", W, "缺失的"), ("average", W, "平均值")]),
        segment("One company name has an extra space. Another name uses a short form. I remove the extra space and choose one name. Clean names make it possible to group the rows correctly.", "一家公司的名字多了一个空格，另一家用了缩写。我去掉多余空格，并统一成一个名字。干净的名字能让我们正确地把各行分组。讲解：extra=多余的，short form=缩写，remove=去掉，group=分组。", [("extra", W, "多余的"), ("short form", T, "缩写"), ("group", W, "分组")]),
        segment("I keep a note of every change. The clean file is useful, but the note is also important. It tells me what I changed and why. Another researcher can repeat my steps.", "我记录每一次改动。干净的文件很有用，但改动记录同样重要。它告诉我改了什么、为什么改。另一个研究者可以重复我的步骤。讲解：repeat=重复，change=改动，step=步骤，researcher=研究者。", [("repeat", W, "重复"), ("record", W, "记录"), ("researcher", W, "研究者")]),
    ], [{"t": "empty is not zero", "cn": "空值不等于零", "eg": "Remember that empty is not zero."}, {"t": "make the format the same", "cn": "统一格式", "eg": "Make the date format the same."}, {"t": "remove the extra space", "cn": "去掉多余空格", "eg": "Remove the extra space first."}, {"t": "keep a note of", "cn": "记录……", "eg": "Keep a note of every change."}], [{"t": "X is not Y.", "cn": "X 不等于 Y。"}, {"t": "I make X the same.", "cn": "我把 X 统一。"}, {"t": "It tells me what and why.", "cn": "它告诉我是什么以及为什么。"}], "design_note", "Write a short data-cleaning note. Use empty is not zero, make the format the same, and keep a note of."),
    lesson(17, "Lesson 17: Read a Simple Chart", "第 17 课：读懂一张简单图表", 3, [
        segment("The clean data is ready. I make a line chart for sales over time. The line goes up slowly. A chart lets me see a direction faster than a long table. It is a picture of the data, not the whole explanation.", "清理后的数据准备好了。我做了一张销售额随时间变化的折线图。线条缓慢向上。图表比长表格更快让我们看到方向，但它只是数据的图像，不是完整解释。讲解：line chart=折线图，over time=随时间，direction=方向，explanation=解释。", [("line chart", T, "折线图"), ("over time", T, "随时间"), ("explanation", W, "解释")]),
        segment("I compare two companies. Company A is larger, but Company B grows faster. The answer changes when I change the question. Size and growth are different ideas. I say exactly what the chart shows.", "我比较两家公司。A 公司更大，但 B 公司增长更快。当我改变问题时，答案也会改变。规模和增长是不同的概念。我准确说出图表显示了什么。讲解：compare=比较，larger=更大的，grow faster=增长更快，idea=概念。", [("compare", W, "比较"), ("growth", T, "增长"), ("exactly", W, "准确地")]),
        segment("A chart can hide a detail. The vertical axis starts at fifty, not zero. The change looks very large. I check the axis before I make a strong claim. Good readers ask how the chart was made.", "图表可能隐藏一个细节：纵轴从五十开始，而不是从零开始，所以变化看起来很大。在做出强烈结论前，我先检查坐标轴。好的读者会问图表是怎样制作的。讲解：axis=坐标轴，hide=隐藏，claim=结论/主张，vertical=垂直的。", [("axis", T, "坐标轴"), ("hide", W, "隐藏"), ("claim", W, "主张")]),
    ], [{"t": "over time", "cn": "随着时间", "eg": "Sales grow over time."}, {"t": "grow faster", "cn": "增长更快", "eg": "Company B grows faster."}, {"t": "what the chart shows", "cn": "图表显示的内容", "eg": "Say what the chart shows."}, {"t": "make a strong claim", "cn": "做出强烈结论", "eg": "Check the data before you make a strong claim."}], [{"t": "X is larger, but Y grows faster.", "cn": "X 更大，但 Y 增长更快。"}, {"t": "The answer changes when X.", "cn": "当 X 时，答案会变化。"}, {"t": "I check X before Y.", "cn": "我在 Y 前检查 X。"}], "design_note", "Describe a chart in 3 sentences. Use over time, grow faster, and what the chart shows."),
    lesson(18, "Lesson 18: Evidence and Story", "第 18 课：证据与故事", 3, [
        segment("A headline says the company is winning. I do not accept the headline immediately. I look for evidence: sales, profit, users, and cash. One good number is not enough to explain a whole business.", "一个标题说这家公司正在获胜。我不会马上接受这个标题，而是寻找证据：销售额、利润、用户和现金。一个漂亮数字不足以解释整个生意。讲解：headline=标题，evidence=证据，profit=利润，cash=现金。", [("headline", W, "标题"), ("evidence", T, "证据"), ("profit", W, "利润")]),
        segment("The company has more users, but each user spends less. The user number is positive, but the picture is mixed. I write both facts in my note. Honest research keeps good and bad evidence together.", "公司的用户更多了，但每个用户花的钱更少。用户数量是积极信号，但整体情况很复杂。我把两个事实都写进笔记。诚实的研究会把好证据和坏证据放在一起。讲解：spend=花费，positive=积极的，mixed=复杂的/好坏混合。", [("spend", W, "花费"), ("positive", W, "积极的"), ("mixed", W, "好坏混合的")]),
        segment("I separate fact from opinion. The fact is: sales grew five percent. My opinion is: the growth may continue. I label the opinion clearly. This small habit keeps my thinking clean.", "我把事实和观点分开。事实是销售额增长了百分之五，观点是增长可能继续。我清楚标注观点。这个小习惯能让思考保持干净。讲解：separate=分开，opinion=观点，continue=继续，label=标注。", [("separate", W, "分开"), ("opinion", T, "观点"), ("continue", W, "继续")]),
    ], [{"t": "look for evidence", "cn": "寻找证据", "eg": "Look for evidence behind the headline."}, {"t": "the picture is mixed", "cn": "整体情况复杂", "eg": "The picture is mixed."}, {"t": "separate fact from opinion", "cn": "区分事实与观点", "eg": "Separate fact from opinion."}, {"t": "label clearly", "cn": "清楚标注", "eg": "Label your opinion clearly."}], [{"t": "I do not accept X immediately.", "cn": "我不会马上接受 X。"}, {"t": "The fact is X.", "cn": "事实是 X。"}, {"t": "My opinion is X.", "cn": "我的观点是 X。"}], "design_note", "Write a short research note that separates fact and opinion. Use look for evidence, the picture is mixed, and separate fact from opinion."),
    lesson(19, "Lesson 19: Explain a Number", "第 19 课：解释一个数字", 3, [
        segment("My manager asks about the five percent growth. I answer with a complete sentence. Sales grew five percent from last year. I also say where the number comes from. A number is stronger when people can check it.", "经理问我百分之五的增长。我用完整句子回答：销售额比去年增长百分之五。我还说明数字来自哪里。一个可以被检查的数字更有说服力。讲解：complete=完整的，from last year=与去年相比，stronger=更有说服力。", [("complete", W, "完整的"), ("from last year", T, "与去年相比"), ("checkable", W, "可检查的")]),
        segment("She asks if the growth is real or caused by a one-time event. I check the notes. One large order made this quarter special. I add this limit to the explanation. Context changes the meaning of a number.", "她问增长是真实的，还是一次性事件造成的。我检查记录，发现一笔大订单让这个季度很特殊。我把这个限制补进解释。上下文会改变数字的含义。讲解：one-time=一次性的，quarter=季度，limit=限制，context=上下文。", [("one-time", T, "一次性的"), ("quarter", T, "季度"), ("context", T, "上下文")]),
        segment("I do not need a long speech. I need a clear number, a source, and one important limit. This is enough for a useful update. Short evidence is easier for a busy team to remember.", "我不需要一大段演讲，只需要一个清楚的数字、一个来源和一个重要限制。这样就足够做出有用的更新。简短的证据更容易让忙碌的团队记住。讲解：speech=演讲，limit=限制，update=更新，busy=忙碌的。", [("speech", W, "演讲"), ("update", W, "更新"), ("busy", W, "忙碌的")]),
    ], [{"t": "where the number comes from", "cn": "数字的来源", "eg": "Say where the number comes from."}, {"t": "a one-time event", "cn": "一次性事件", "eg": "The result may be a one-time event."}, {"t": "add a limit", "cn": "补充一个限制", "eg": "Add a limit to the explanation."}, {"t": "a useful update", "cn": "有用的更新", "eg": "This is enough for a useful update."}], [{"t": "X grew Y from last year.", "cn": "X 比去年增长了 Y。"}, {"t": "X is caused by Y.", "cn": "X 是由 Y 造成的。"}, {"t": "This is enough for X.", "cn": "这对 X 已经足够。"}], "standup_update", "Write a 3-sentence update about one number. Use where the number comes from, a one-time event, and add a limit."),
    lesson(20, "Lesson 20: A Small Research Note", "第 20 课：一份小研究笔记", 3, [
        segment("I write a short note about the company. First, I state the question. Then I give two facts from the data. After that, I explain one risk. The note is not a final answer. It is a clear starting point for discussion.", "我写一份关于这家公司的短笔记。先说明问题，再给出两个数据事实，然后解释一个风险。这份笔记不是最终答案，而是一个清楚的讨论起点。讲解：state=说明，risk=风险，discussion=讨论，starting point=起点。", [("state", W, "说明"), ("risk", T, "风险"), ("starting point", T, "起点")]),
        segment("I use simple words. I do not hide a weak fact behind a big word. I write: sales grew, but cash fell. This sentence is short and honest. The reader can ask the next question.", "我使用简单词语，不用大词掩盖弱证据。我写：销售额增长了，但现金减少了。这句话短而诚实，读者可以继续问下一个问题。讲解：hide behind=躲在……后面，weak=弱的，honest=诚实的，reader=读者。", [("hide", W, "掩盖"), ("weak", W, "弱的"), ("honest", W, "诚实的")]),
        segment("I finish with a next step. I will read the next report and compare the cash number. A good note tells me what to do next, not only what I saw before.", "我最后写下一步行动：继续阅读下一份报告，并比较现金数字。一份好的笔记不只告诉我以前看到了什么，也告诉我下一步要做什么。讲解：finish with=以……结束，compare=比较，next step=下一步。", [("finish with", T, "以……结束"), ("compare", W, "比较"), ("what to do next", T, "下一步做什么")]),
    ], [{"t": "state the question", "cn": "说明问题", "eg": "State the question first."}, {"t": "hide a weak fact", "cn": "掩盖一个弱事实", "eg": "Do not hide a weak fact."}, {"t": "a starting point", "cn": "一个起点", "eg": "The note is a starting point."}, {"t": "what to do next", "cn": "下一步做什么", "eg": "The note tells me what to do next."}], [{"t": "First, I X.", "cn": "首先，我 X。"}, {"t": "X grew, but Y fell.", "cn": "X 增长了，但 Y 下降了。"}, {"t": "I will X next.", "cn": "接下来我会 X。"}], "design_note", "Write a short research note with a question, two facts, and a next step. Use state the question, a starting point, and what to do next."),
    lesson(21, "Lesson 21: Research Week Review", "第 21 课：研究英语周复习", 3, [
        segment("This week I learned to ask a clear data question. I cleaned empty cells and checked dates. I read a chart and looked for evidence. These steps slow me down, but they make the answer safer.", "这周我学会提出清楚的数据问题。我清理空单元格，检查日期，阅读图表并寻找证据。这些步骤会让我慢一点，但能让答案更安全。讲解：cell=单元格，safe=安全的，slow down=放慢。", [("cell", W, "单元格"), ("evidence", T, "证据"), ("slow down", T, "放慢")]),
        segment("I also practiced explaining a number. I gave the source and the context. I separated fact from opinion. When I do not know, I say I do not know. Honest uncertainty is better than a confident guess.", "我还练习解释一个数字，说明来源和上下文，区分事实与观点。不知道时，我就说不知道。诚实的不确定性比自信的猜测更好。讲解：uncertainty=不确定性，confident=自信的，guess=猜测。", [("uncertainty", W, "不确定性"), ("guess", W, "猜测"), ("better than", T, "比……更好")]),
        segment("Next week I will use English with AI tools. I will write a clear prompt, check the answer, and keep a record of the source. The goal is not to sound clever. The goal is to think clearly.", "下周我会用英语配合 AI 工具。我会写清楚的提示词，检查答案，并记录来源。目标不是听起来聪明，而是清楚地思考。讲解：tool=工具，prompt=提示词，source=来源，sound clever=听起来聪明。", [("tool", W, "工具"), ("prompt", T, "提示词"), ("think clearly", T, "清楚地思考")]),
    ], [{"t": "ask a clear question", "cn": "提出清楚的问题", "eg": "Ask a clear question first."}, {"t": "look for evidence", "cn": "寻找证据", "eg": "Look for evidence in the data."}, {"t": "better than a confident guess", "cn": "比自信的猜测更好", "eg": "Uncertainty is better than a confident guess."}, {"t": "think clearly", "cn": "清楚地思考", "eg": "The goal is to think clearly."}], [{"t": "These steps make X safer.", "cn": "这些步骤让 X 更安全。"}, {"t": "When I do not know, I X.", "cn": "不知道时，我会 X。"}, {"t": "The goal is not X. The goal is Y.", "cn": "目标不是 X，目标是 Y。"}], "standup_update", "Write a weekly review. Use ask a clear question, better than a confident guess, and think clearly."),
    lesson(22, "Lesson 22: Write a Better Prompt", "第 22 课：写出更好的提示词", 4, [
        segment("I ask an AI tool to explain a Python error. My first prompt is too short: fix this. The answer is vague. I add the goal, the error message, and the code around the error. The second answer is more useful.", "我让 AI 工具解释一个 Python 错误。我的第一个提示词太短：修复这个。答案很模糊。我补充目标、错误信息和错误附近的代码，第二个答案更有用。讲解：vague=模糊的，around=附近，useful=有用的。", [("prompt", T, "提示词"), ("vague", W, "模糊的"), ("around", W, "附近")]),
        segment("A good prompt gives the model a role and a format. I say: act as a patient teacher. Explain the error in three short steps. Use simple English and Chinese notes. The format makes the answer easier to read.", "好的提示词会给模型一个角色和格式。我说：请像耐心的老师一样，用三个短步骤解释错误，使用简单英语和中文笔记。格式会让答案更容易阅读。讲解：role=角色，format=格式，patient=耐心的，step=步骤。", [("role", T, "角色"), ("format", T, "格式"), ("patient", W, "耐心的")]),
        segment("I do not ask the model to guess missing facts. I tell it to say when it is unsure. A clear limit protects the answer. Prompts are instructions, not magic words.", "我不要求模型猜测缺失事实，而是告诉它不确定时要说出来。清楚的限制可以保护答案。提示词是指令，不是魔法词。讲解：guess=猜测，unsure=不确定的，limit=限制，magic=魔法的。", [("unsure", W, "不确定的"), ("limit", T, "限制"), ("instruction", T, "指令")]),
    ], [{"t": "too short", "cn": "太短", "eg": "The first prompt is too short."}, {"t": "act as a teacher", "cn": "像老师一样工作", "eg": "Act as a patient teacher."}, {"t": "in three short steps", "cn": "用三个短步骤", "eg": "Explain it in three short steps."}, {"t": "say when you are unsure", "cn": "不确定时说出来", "eg": "Say when you are unsure."}], [{"t": "My first prompt is X.", "cn": "我的第一个提示词是 X。"}, {"t": "Explain X in Y steps.", "cn": "用 Y 个步骤解释 X。"}, {"t": "Tell it to X.", "cn": "告诉它 X。"}], "design_note", "Write a prompt for an English tutor. Use act as a teacher, in three short steps, and say when you are unsure."),
    lesson(23, "Lesson 23: Give the AI Context", "第 23 课：给 AI 上下文", 4, [
        segment("The model does not know my whole project. I give it context before I ask a question. I explain the user, the goal, the current behavior, and the problem. Context helps the model choose a better answer.", "模型不知道我的整个项目。我在提问前先给它上下文，说明用户、目标、当前行为和问题。上下文能帮助模型选择更好的答案。讲解：context=上下文，behavior=行为，choose=选择。", [("context", T, "上下文"), ("behavior", W, "行为"), ("choose", W, "选择")]),
        segment("I also show one good example and one bad example. Examples make the difference clear. If I want a short answer, I show the length and tone. The model follows a pattern more easily when I show it.", "我还给出一个好例子和一个坏例子。例子会让差别清楚。如果我想要短答案，我会示范长度和语气。给出模式后，模型更容易遵循。讲解：example=例子，tone=语气，pattern=模式，follow=遵循。", [("example", W, "例子"), ("tone", W, "语气"), ("pattern", T, "模式")]),
        segment("Too much context can also be a problem. I keep the useful parts and remove old notes. A focused context saves time and reduces confusion. Good prompting is partly good editing.", "上下文太多也可能成为问题。我保留有用部分，删除旧笔记。聚焦的上下文能节省时间并减少混乱。好的提示词工作有一部分就是好的编辑。讲解：focused=聚焦的，reduce=减少，confusion=混乱，edit=编辑。", [("focused", W, "聚焦的"), ("reduce", W, "减少"), ("confusion", W, "混乱")]),
    ], [{"t": "give it context", "cn": "给它上下文", "eg": "Give the model context first."}, {"t": "show one example", "cn": "展示一个例子", "eg": "Show one good example."}, {"t": "follow a pattern", "cn": "遵循一个模式", "eg": "The model can follow a pattern."}, {"t": "remove old notes", "cn": "删除旧笔记", "eg": "Remove old notes from the prompt."}], [{"t": "I explain X before I ask Y.", "cn": "我在问 Y 前解释 X。"}, {"t": "Examples make X clear.", "cn": "例子让 X 变清楚。"}, {"t": "I keep X and remove Y.", "cn": "我保留 X，删除 Y。"}], "design_note", "Write a prompt context block for a small coding problem. Use give it context, show one example, and remove old notes."),
    lesson(24, "Lesson 24: Check the AI Answer", "第 24 课：检查 AI 的答案", 4, [
        segment("The AI gives me a confident answer. I do not trust the tone by itself. I check the code in my own project. I run a small test and compare the result with the answer. The test is the judge.", "AI 给了我一个听起来很自信的答案。我不会只相信语气，而是在自己的项目里检查代码。我运行一个小测试，把结果和答案比较。测试才是裁判。讲解：confident=自信的，tone=语气，judge=裁判，compare=比较。", [("confident", W, "自信的"), ("by itself", T, "单独地"), ("judge", W, "裁判")]),
        segment("The answer uses a library function I do not know. I open the official documentation. The documentation says the function has a limit. The AI did not mention the limit. I add the missing detail to my note.", "答案使用了一个我不认识的库函数。我打开官方文档，文档说这个函数有一个限制，而 AI 没有提到。我把缺失细节补进笔记。讲解：library=库，official=官方的，documentation=文档，limit=限制。", [("library", T, "库"), ("official", W, "官方的"), ("documentation", T, "文档")]),
        segment("AI is useful for a first draft, not a final authority. I keep the helpful part and correct the weak part. My responsibility is to check before I use the answer.", "AI 适合做第一稿，不是最终权威。我保留有用部分，修正薄弱部分。在使用答案前进行检查，是我的责任。讲解：draft=草稿，authority=权威，responsibility=责任，correct=修正。", [("draft", W, "草稿"), ("authority", W, "权威"), ("responsibility", T, "责任")]),
    ], [{"t": "trust the tone", "cn": "相信语气", "eg": "Do not trust the tone by itself."}, {"t": "run a small test", "cn": "运行一个小测试", "eg": "Run a small test first."}, {"t": "official documentation", "cn": "官方文档", "eg": "Check the official documentation."}, {"t": "a first draft", "cn": "第一稿", "eg": "AI can make a first draft."}], [{"t": "I do not trust X by itself.", "cn": "我不会单独相信 X。"}, {"t": "The documentation says X.", "cn": "文档说 X。"}, {"t": "My responsibility is to X.", "cn": "我的责任是 X。"}], "code_review_comment", "Write a review comment about checking an AI answer. Use run a small test, official documentation, and a first draft."),
    lesson(25, "Lesson 25: Facts, Sources, and Uncertainty", "第 25 课：事实、来源与不确定性", 4, [
        segment("I ask AI about a company's market. The answer lists several facts, but it gives no sources. I mark those claims as unverified. A smooth paragraph is not proof. I need a document, a date, or a direct link.", "我问 AI 一家公司的市场情况。答案列出几个事实，却没有来源。我把这些说法标记为未验证。流畅的段落不是证据，我需要文件、日期或直接链接。讲解：claim=说法/主张，unverified=未验证的，proof=证据，direct=直接的。", [("claim", T, "说法"), ("unverified", T, "未验证的"), ("proof", W, "证据")]),
        segment("One source is old. The market may have changed since then. I write the date beside the fact. I also use careful language: the report says, the data suggests, or I do not know yet.", "一个来源很旧，市场可能已经变化。我把日期写在事实旁边，也使用谨慎表达：报告说、数据暗示，或者我还不知道。讲解：old=旧的，changed=变化的，suggest=暗示，careful=谨慎的。", [("suggest", W, "暗示"), ("careful", W, "谨慎的"), ("beside", W, "在旁边")]),
        segment("This does not make research weak. It makes the boundary clear. Good work shows what is known, what is likely, and what still needs checking.", "这不会让研究变弱，反而会让边界清楚。好的工作会显示什么是已知的、什么是可能的，以及什么还需要检查。讲解：boundary=边界，likely=可能的，still needs checking=仍需检查。", [("boundary", T, "边界"), ("likely", W, "可能的"), ("known", W, "已知的")]),
    ], [{"t": "give no sources", "cn": "没有给出来源", "eg": "The answer gives no sources."}, {"t": "mark a claim as unverified", "cn": "把说法标为未验证", "eg": "Mark the claim as unverified."}, {"t": "the data suggests", "cn": "数据暗示", "eg": "The data suggests a change."}, {"t": "the boundary is clear", "cn": "边界清楚", "eg": "Now the boundary is clear."}], [{"t": "The report says X.", "cn": "报告说 X。"}, {"t": "The data suggests X.", "cn": "数据暗示 X。"}, {"t": "I do not know yet.", "cn": "我还不知道。"}], "design_note", "Write three cautious sentences about a source. Use mark a claim as unverified, the data suggests, and I do not know yet."),
    lesson(26, "Lesson 26: Use an API Carefully", "第 26 课：谨慎使用 API", 4, [
        segment("My small program calls an API. An API is a door to another service. I send a request and receive a response. The response has data and a status code. I print the status before I trust the data.", "我的小程序调用一个 API。API 是通往另一个服务的一扇门。我发送请求并收到响应。响应有数据和状态码。我在相信数据前先打印状态。讲解：API=程序接口，request=请求，response=响应，status code=状态码。", [("API", T, "程序接口"), ("response", T, "响应"), ("status code", T, "状态码")]),
        segment("The request fails when the key is missing. I keep the key outside the code. A secret should not appear in a public file or a screenshot. I use an environment variable instead.", "当 key 缺失时，请求失败。我把 key 放在代码外。秘密不应该出现在公开文件或截图里，我改用环境变量。讲解：secret=秘密，public=公开的，screenshot=截图，environment variable=环境变量。", [("secret", T, "秘密"), ("public", W, "公开的"), ("screenshot", W, "截图")]),
        segment("I also set a limit on requests. A free service may have a small quota. If I call it too often, the program may stop. Good code handles the limit and tells the user what happened.", "我还给请求设置限制。免费服务可能只有很小的配额。如果调用太频繁，程序可能停止。好的代码会处理限制，并告诉用户发生了什么。讲解：quota=配额，often=经常地，handle=处理，happen=发生。", [("quota", T, "配额"), ("handle", W, "处理"), ("happen", W, "发生")]),
    ], [{"t": "a door to another service", "cn": "通往另一个服务的门", "eg": "An API is a door to another service."}, {"t": "send a request", "cn": "发送请求", "eg": "The program sends a request."}, {"t": "keep the key outside the code", "cn": "把 key 放在代码外", "eg": "Keep the key outside the code."}, {"t": "set a limit", "cn": "设置限制", "eg": "Set a limit on requests."}], [{"t": "I send X and receive Y.", "cn": "我发送 X 并收到 Y。"}, {"t": "A secret should not appear in X.", "cn": "秘密不应该出现在 X 中。"}, {"t": "If X, the program may Y.", "cn": "如果 X，程序可能 Y。"}], "design_note", "Write a short API safety note. Use send a request, keep the key outside the code, and set a limit."),
    lesson(27, "Lesson 27: Write the Project Update", "第 27 课：写项目更新", 4, [
        segment("It is Friday. I write an update for the team. I start with what is done: the data reader works and the first chart is ready. Then I say what is next: check two more sources and improve the labels.", "周五，我给团队写一份更新。先写已经完成的：数据读取器能工作，第一张图表准备好了。然后写下一步：检查两个来源并改进标签。讲解：update=更新，done=完成的，improve=改进，label=标签。", [("update", W, "更新"), ("done", W, "完成的"), ("improve", W, "改进")]),
        segment("I mention one risk. The data may be one month late. This means the chart is useful for a first look, but not for a final decision. The team can now choose the next check.", "我提到一个风险：数据可能晚了一个月。这意味着图表适合初步查看，但不适合做最终决策。团队现在可以选择下一项检查。讲解：late=晚的，first look=初步查看，decision=决定，choose=选择。", [("late", W, "晚的"), ("first look", T, "初步查看"), ("decision", T, "决定")]),
        segment("I keep the message short. A good update answers three questions: what changed, what is blocked, and what will happen next. Clear writing helps the team move.", "我把消息写得简短。好的更新回答三个问题：改了什么、什么被卡住了、接下来会发生什么。清楚的写作能帮助团队前进。讲解：blocked=被阻塞的，move=推进，what changed=发生了什么变化。", [("blocked", W, "被阻塞的"), ("move", W, "推进"), ("what changed", T, "发生了什么变化")]),
    ], [{"t": "what is done", "cn": "已经完成的内容", "eg": "Start with what is done."}, {"t": "what is next", "cn": "下一步是什么", "eg": "Then say what is next."}, {"t": "for a first look", "cn": "用于初步查看", "eg": "The chart is useful for a first look."}, {"t": "what is blocked", "cn": "什么被卡住了", "eg": "Say what is blocked."}], [{"t": "I start with X.", "cn": "我从 X 开始。"}, {"t": "This means X, but not Y.", "cn": "这意味着 X，但不是 Y。"}, {"t": "A good update answers X.", "cn": "好的更新回答 X。"}], "slack_message", "Write a project update with done, next, and one risk. Use what is done, what is next, and what is blocked."),
    lesson(28, "Lesson 28: The Month Project", "第 28 课：月度小项目", 4, [
        segment("At the end of the month, I combine my skills. I ask one question about a small company dataset. I read a JSON file, clean the values, and make a chart. Then I ask an AI tool to help me explain the result.", "月底，我把学到的技能结合起来。我针对一份小公司的数据提出一个问题，读取 JSON 文件，清理数值并制作图表，然后请 AI 工具帮我解释结果。讲解：combine=结合，dataset=数据集，result=结果。", [("combine", W, "结合"), ("dataset", T, "数据集"), ("result", W, "结果")]),
        segment("I do not copy the answer without checking. I compare it with the chart and the source. I correct one wrong detail. I write a short note with facts, limits, and a next step. The note is simple, but it is mine.", "我不会不检查就复制答案。我把答案和图表、来源进行比较，修正一个错误细节。我写一份包含事实、限制和下一步的短笔记。笔记很简单，但它是我自己的。讲解：copy=复制，detail=细节，limit=限制，mine=我的。", [("detail", W, "细节"), ("limit", T, "限制"), ("mine", W, "我的")]),
        segment("I present the project in three minutes. I say the question, the evidence, and the uncertainty. I do not need perfect English. I need clear English and honest thinking. This is my next small step.", "我用三分钟介绍这个项目，说清问题、证据和不确定性。我不需要完美英语，只需要清楚的英语和诚实的思考。这就是我的下一小步。讲解：present=介绍/展示，perfect=完美的，honest thinking=诚实思考。", [("present", W, "介绍;展示"), ("perfect", W, "完美的"), ("uncertainty", T, "不确定性")]),
    ], [{"t": "combine my skills", "cn": "结合我的技能", "eg": "I combine my skills in one project."}, {"t": "without checking", "cn": "没有检查就……", "eg": "Do not copy it without checking."}, {"t": "facts, limits, and a next step", "cn": "事实、限制和下一步", "eg": "The note has facts, limits, and a next step."}, {"t": "clear English", "cn": "清楚的英语", "eg": "I need clear English."}], [{"t": "I do not X without Y.", "cn": "没有 Y，我不会 X。"}, {"t": "I need X, not Y.", "cn": "我需要 X，而不是 Y。"}, {"t": "This is my next step.", "cn": "这是我的下一步。"}], "standup_update", "Write a 3-minute project presentation in 5 short sentences. Use combine my skills, without checking, and clear English."),
]


def write_lessons() -> None:
    for data in LESSONS:
        day_number = int(data["meta"]["source"].split("Day ")[-1])
        out_dir = WEEK_DIR / f"day-{day_number:02d}"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "segments.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"written: {out_dir / 'segments.json'}")


def write_index() -> None:
    items = []
    for day in range(1, 29):
        path = WEEK_DIR / f"day-{day:02d}" / "segments.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        card = data["meta"]["study_card"]
        week = (day - 1) // 7 + 1
        if day in {1, 8, 15, 22}:
            items.append(f'<h2 class="week-title">第 {week} 周</h2>')
        items.append(f'<li><a href="day-{day:02d}/index.html"><h3>{data["meta"]["title"]}</h3><p>{data["meta"]["title_zh"]} · {card["word_count"]} 词 · 约 15–20 分钟</p></a></li>')
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>英语学习月计划 · Month 1</title>
<style>
body{{font-family:-apple-system,sans-serif;max-width:760px;margin:0 auto;padding:32px 20px;line-height:1.6;background:#fafafa;color:#222}}
h1{{font-size:28px;margin-bottom:4px}} .sub{{color:#666;margin-bottom:24px}}
ul{{list-style:none;padding:0}} li{{background:#fff;border:1px solid #e3e3e3;border-radius:10px;margin-bottom:10px;overflow:hidden}}
a{{display:block;padding:14px 18px;text-decoration:none;color:#222}} a:hover{{background:#f0f7ff}}
h3{{margin:0 0 3px;font-size:17px}} p{{margin:0;color:#666;font-size:13px}}
.week-title{{margin:26px 0 10px;color:#315c91;font-size:20px}}
.vocab-entry{{display:block;margin:22px 0 30px;padding:22px;border-radius:16px;background:linear-gradient(135deg,#163e33,#2d6b55);color:white}}
.vocab-entry strong{{display:block;font-size:21px}} .vocab-entry span{{display:block;margin-top:4px;color:rgba(255,255,255,.78);font-size:14px}}
</style>
</head>
<body>
<h1>英语学习月计划 · Month 1</h1>
<p class="sub">第 1 周工作英语入门 · 第 2 周 Python 与数据 · 第 3 周研究表达 · 第 4 周 AI 工作流 · 每天约 15–20 分钟</p>
<a class="vocab-entry" href="vocabulary-month/"><strong>30 天专业英语词汇强化 →</strong><span>计算机 × 日常交流 × GitHub · 每天 18 个 · 与口语课并行</span></a>
<ul>{''.join(items)}</ul>
</body>
</html>
"""
    (ROOT / "lessons" / "week" / "index.html").write_text(html, encoding="utf-8")
    print("written: lessons/week/index.html")


if __name__ == "__main__":
    write_lessons()
    write_index()
