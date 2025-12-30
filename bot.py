import os
import random
from zoneinfo import ZoneInfo
from datetime import datetime,timedelta
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import db
from aiohttp import web

load_dotenv()

db.init_db()

intents=discord.Intents.all()
bot=commands.Bot(command_prefix="/", intents=intents)

TZ=ZoneInfo("Asia/Taipei")

sche=AsyncIOScheduler(timezone="Asia/Taipei")

interval=dict()
'''
format:
gay:{
    hour:6,
    minute:9
    notmsg:"去打手槍"
    worktime:1
    endtime:1
    anno:False
}
'''

talk3small=["你腦霧吧",
            "喔咿咿阿依喔咿咿咿阿依",
            "ㄟㄟ快看那裏有個傻逼",
            "你知道把你女朋友形容成一把劍叫做看不劍",
            "吃~~~雞~~~~雞~~~喔~~~~喔~~~喔~~~~~~~~~",
            "麵框框超頂去吃它",
            "你知道把費米子轉一圈他的波函數會轉180度嗎?",
            "如果你餓了不吃東西，可以吃我屌",
            "又!又舔!又舔嘴唇!!!",
            "冷知識：什麼東西是綠色的掉下去會砸死人?\n台球桌",
            "如果你現在肚子餓的話，可以去廁所看看，你就會沒食慾摟~",
            "小明對芒果過敏，那他不能吃什麼?\n他不能吃芒果\n你以為我要說台球桌是不是:))))))",
            "你知道你為什麼要讀書嗎?\n我也不知道，反正你在廢下去我就打斷你的腿",
            "不要再打了，要打去練舞室打",
            "聽話，讓我看看!!!",
            "這件事是我們兩個之間的秘密，你最好不要給我告訴任何人，如果你要說出去，就給我小心一點",
            "我知道你學校在哪，也知道你讀哪一班，你最好給我好好記住，懂嗎?",
            "不要!!!杰哥不要啦，杰哥不要.....杰哥不要，杰歌",
            "前列腺高潮來臨時，腰部以下特別是陰腹部位幾乎完全麻痺",
            "這種收縮運動大概只有幾秒鐘，收縮過後就是強烈的高潮到來",
            "整個身體好像一朵雲，輕飄飄的浮在空中，完全虛脫失去重力",
            "我電腦放客廳，家人聽得道你在說什麼",
            "爸爸媽媽，你兒子在了解前列腺的事情啦",
            "彈幕一個觀眾說：台灣人文明的讓我受不了"]

tuto="/print <msg,gap,slptime>\n" \
     "輸出對應資訊\n" \
     "/stop gap <天數> <小時數> <分鐘數>\n" \
     "暫時停止bot煩，時間代表停止的間隔，過後便會馬上開始\n" \
     "/stop set <年> <月> <天數> <小時> <分鐘>\n" \
     "暫時停止bot煩，時間代表停用至什麼時候，過後便馬上開始\n" \
     "/stop forever\n" \
     "永久停止\n" \
     "/set gap <小時> <分鐘>\n" \
     "設定提醒之間的gap\n" \
     "/set msg <提示詞>\n" \
     "設定提示詞\n" \
     "/set slptime <開始睡覺時間> <停止睡覺時間>\n" \
     "設定睡覺時間\n" \
     "/startnow\n" \
     "提示計時現在結束" \
     ""

async def handle_root():
    return web.Response(text="機器運作中")

def create_web_app():
    app=web.Application()
    app.router.add_get("/", handle_root)
    return app

app=create_web_app()
runner=web.AppRunner(app)

async def notifyreset(sche,ctx):
    usr_id=ctx.author.id
    runtime=datetime.now(TZ)+timedelta(hours=interval[usr_id]['hour'],minutes=interval[usr_id]['minute'])
    curhr=datetime.now(TZ).hour
    worktime=interval[usr_id]['worktime']
    endtime=interval[usr_id]['endtime']
    
    noti_id=f"{usr_id},notify"
    anno_id=f"{usr_id},annoy"
    interval[usr_id]['anno']=True
    db.change_partial_data(usr_id,{'anno':True})
    setsche(runtime,noti_id,notifyreset,[sche,ctx])
    if (worktime>=endtime and (curhr>=worktime or curhr<=endtime)) or (worktime<endtime and (curhr>=worktime and curhr<=endtime)):
        return
    if not is_job_scheduled(sche,anno_id):setsche(datetime.now(TZ),anno_id,frequent_message,[sche,ctx,0])

async def frequent_message(sche,ctx,count):
    usr_id=ctx.author.id
    if not interval[usr_id]['anno'] or count>50:
        interval[usr_id]['anno']=False
        db.change_partial_data(usr_id,{'anno':False})
        return
    count+=1
    await ctx.send(f"{ctx.author.mention}{interval[usr_id]['notmsg']}")
    runtime=datetime.now(TZ)+timedelta(seconds=1,milliseconds=500)
    anno_id=f"{usr_id},annoy"
    setsche(runtime,anno_id,frequent_message,[sche,ctx,count])

def is_job_scheduled(sche, job_id:str)->bool:
    job=sche.get_job(job_id)
    return job is not None

def setsche(date,job_id,func,args):
    sche.add_job(
        func=func,
        trigger="date",
        id=job_id,
        run_date=date,
        args=args
    )
    
def init_usr(usr_id):
    interval[usr_id]={
        'hour':1,
        'minute':0,
        'notmsg':"去讀書拉小學生",
        'worktime':23,
        'endtime':8,
        'anno':False
    }
    db.init_usr(usr_id,interval[usr_id])

@bot.command(name="helpme")
async def helpme(ctx,sub:str|None=None):
    await ctx.send(tuto)

@bot.command(name="print")
async def print_data(ctx,sub:str|None=None):
    """
    用法：
    /print <msg,gap,slptime>
    """
    global interval
    usr_id=ctx.author.id
    worktime=interval[usr_id]['worktime']
    endtime=interval[usr_id]['endtime']
    if sub=="msg":
        reply_text=interval[usr_id]['notmsg']
    elif sub=="gap":
        reply_text=f"{interval[usr_id]['hour']}小時{interval[usr_id]['minute']}分鐘"
    elif sub=="slptime":
        reply_text=f"睡覺時間：{worktime}~{endtime}"
    else:
        reply_text="參數錯誤，格式應為 /print <msg,gap,slptime>"
    await ctx.send(reply_text)

@bot.command(name="stop")
async def stop(ctx,*sub:str):
    """
    用法：
    /stop gap <天數> <小時數> <分鐘數>
    /stop set <年> <月> <天數> <小時> <分鐘>
    /stop forever
    """
    global interval
    usr_id=ctx.author.id
    sleep_id=f"{usr_id},sleep"
    noti_id=f"{usr_id},notify"
    anno_id=f"{usr_id},annoy"
    if is_job_scheduled(sche,sleep_id):
        reply_text="別吵林北，林北在睡覺"
    else:
        try:
            if sub[0]=="gap":
                try:
                    runtime=datetime.now(TZ)+timedelta(days=int(sub[1]),hours=int(sub[2]),minutes=int(sub[3]))
                    if is_job_scheduled(sche,noti_id):sche.remove_job(noti_id)
                    if is_job_scheduled(sche,anno_id):sche.remove_job(anno_id)
                    setsche(runtime,sleep_id,notifyreset,[sche,ctx])
                    reply_text=f"設定成功，將會等待{sub[1]}天{sub[2]}小時{sub[3]}分\n請你務必要知道你自己在做什麼，為你自己的選擇負責任"
                except:
                    reply_text="參數錯誤，格式應為/stop gap <天數> <小時數> <分鐘數>"
            elif sub[0]=="set":
                try:
                    runtime=datetime(year=int(sub[1]),month=int(sub[2]),day=int(sub[3]),hour=int(sub[4]),minute=int(sub[5]))
                    if runtime<datetime.now(TZ):
                        reply_text="不可設過去的時間"
                    else:
                        setsche(runtime,sleep_id,notifyreset,[sche,ctx])
                        reply_text=f"設定成功，將會等至{sub[1]}年{sub[2]}月{sub[3]}日{sub[4]}點{sub[5]}分\n請你務必要知道你自己在做什麼，為你自己的選擇負責任"
                except:
                    reply_text="參數錯誤，格式應為/stop set <年> <月> <天數> <小時> <分鐘>"
            elif sub[0]=="forever":
                reply_text="你傻逼吧你真以為有這種功能喔"
            else:
                reply_text="參數錯誤，格式應為/stop <gap,set,forever>"
        except:
            reply_text="參數錯誤，格式應為/stop <gap,set>"
    await ctx.send(reply_text)

@bot.command(name="set")
async def set(ctx,*sub:str):
    '''
    用法:
    /set gap <小時> <分鐘>
    /set msg <提示詞>
    /set slptime <開始睡覺時間> <停止睡覺時間>
    '''
    global interval
    usr_id=ctx.author.id
    try:
        if sub[0]=="gap":
            try:
                hour=int(sub[1])
                minute=int(sub[2])
                interval[usr_id]["hour"]=hour
                interval[usr_id]["minute"]=minute
                db.change_partial_data(usr_id,{"hour":hour,"minute":minute})
                reply_text="設定成功"
            except:
                reply_text="參數錯誤，格式應為/set gap <小時> <分鐘>"
        elif sub[0]=="msg":
            try:
                newnotmsg=sub[1]
                for i in range(2,len(sub)):
                    newnotmsg+=f" {sub[i]}"
                interval[usr_id]["notmsg"]=newnotmsg
                db.change_partial_data(usr_id,{"notmsg":newnotmsg})
                reply_text="設定成功"
            except:
                reply_text="參數錯誤，格式應為/set msg <提示詞>"
        elif sub[0]=="slptime":
            try:
                worktime=int(sub[1])
                endtime=int(sub[2])
                interval[usr_id]['worktime']=worktime
                interval[usr_id]['endtime']=endtime
                db.change_partial_data(usr_id,{"worktime":worktime,"endtime":endtime})
                reply_text="設定成功"
            except:
                reply_text="參數錯誤，格式應為/set slptime <開始睡覺時間> <停止睡覺時間>"
        else:
            reply_text="參數錯誤，格式應為/set <gap,msg,slptime>"
    except:
        reply_text="參數錯誤，格式應為/set <gap,msg,slptime>"
    await ctx.send(reply_text)

@bot.command(name="startnow")
async def startnow(ctx,sub:str|None=None):
    usr_id=ctx.author.id
    setsche(datetime.now(TZ),f"{usr_id},notify",notifyreset,[sche,ctx])

@bot.command(name="fuckurmom")
async def fkmom(ctx,sub:str|None=None):
    await ctx.send("正在前往幹你媽的路上")

@bot.event
async def on_message(message:discord.Message):
    global interval
    if message.author==bot.user:
        return
    usr_id=message.author.id
    if usr_id not in interval:
        usr_data=db.getdata(usr_id)
        interval[usr_id]=usr_data
        if usr_data is None:init_usr(usr_id)
    worktime=interval[usr_id]['worktime']
    endtime=interval[usr_id]['endtime']
    curhr=datetime.now(TZ).hour
    if ((worktime>=endtime and (curhr>=worktime or curhr<=endtime)) or (worktime<endtime and (curhr>=worktime and curhr<=endtime))):
        await message.channel.send("去睡覺")
        return
    if interval[usr_id]['anno']==True:
        interval[usr_id]['anno']=False
        db.change_partial_data(usr_id,{'anno':False})
    if message.author==bot.user:
        return
    if message.content.startswith('/'):
        await bot.process_commands(message)
    else:
        await message.channel.send(talk3small[random.randint(0,len(talk3small)-1)])

@bot.event
async def on_ready():
    print(f"已登入為 {bot.user} (ID: {bot.user.id})")
    sche.start()

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("非法指令，想知道可用指令請打/helpme")

async def setup():
    global runner
    await runner.setup()
    site=web.TCPSite(runner,"0.0.0.0",os.getenv("PORT"))
    await site.start()
    db.get_conn()
    return runner

async def clean():
    global runner
    await runner.cleanup()

if __name__=='__main__':
    try:
        asyncio.run(setup())
        bot.run(os.getenv("TOKEN"))
    finally:
        try:
            asyncio.run(clean(runner))
            sche.shutdown(wait=False)
        except:
            pass
        conn=db._conn
        try:
            if conn is not None and not conn.closed:
                conn.close()
        except:
            pass

