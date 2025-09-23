import subprocess

from fastapi import FastAPI, HTTPException, BackgroundTasks, Body
from starlette.middleware.cors import CORSMiddleware

from src.config.settings import Config

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.mongodb import MongoDBJobStore

from src.data.database.connection import db
from src.data.repositories.WebsiteStateRepository import WebsiteStateRepository
from utils import logging

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # hoặc chỉ định domain front-end
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db.connect(Config.MONGODB_URI)
WebsiteStateRepository.init_states(Config.WEBSITES)
crawl_processes = {}

# Persistent job store với MongoDB
jobstores = {
    'default': MongoDBJobStore(
        host=Config.MONGODB_URI,
        database=Config.MONGODB_DATABASE,
        collection='apscheduler_jobs'
    )
}
scheduler = BackgroundScheduler(jobstores=jobstores, timezone="Asia/Ho_Chi_Minh")
scheduler.start()


@app.get("/websites")
def list_websites():
    return WebsiteStateRepository.get_all()


@app.post("/websites/enable")
def enable_websites(names: list[str] = Body(..., embed=True)):
    updated = []
    for name in names:
        ws = WebsiteStateRepository.get_by_name(name)
        if ws:
            WebsiteStateRepository.set_state(name, True)
            updated.append(name)
    return {"message": f"Enabled: {updated}"}


@app.post("/websites/disable")
def disable_websites(names: list[str] = Body(..., embed=True)):
    updated = []
    for name in names:
        ws = WebsiteStateRepository.get_by_name(name)
        if ws:
            WebsiteStateRepository.set_state(name, False)
            updated.append(name)
    return {"message": f"Disabled: {updated}"}


@app.post("/crawl_now")
def crawl_now(websites: list[str] = None, background_tasks: BackgroundTasks = None):
    """
    Cào ngay lập tức các website (hoặc tất cả nếu không truyền)
    """
    if websites is None:
        websites = [ws.name for ws in WebsiteStateRepository.get_all() if ws.enabled]
    background_tasks.add_task(run_crawl, websites)
    return {"message": f"Started crawling: {websites}"}

@app.post("/stop_now")
def stop_now(websites: list[str] = None):
    """
    Dừng các tiến trình cào ngay lập tức
    """
    global crawl_processes
    stopped = []
    if not websites:
        websites = list(crawl_processes.keys())
    for name in websites:
        proc = crawl_processes.get(name)
        if proc and proc.poll() is None:  # Nếu process còn chạy
            proc.terminate()
            stopped.append(name)
            crawl_processes.pop(name, None)
    return {"message": f"Stopped crawling: {stopped}"}

@app.post("/schedule_crawl")
def schedule_crawl(interval_hours: int = 24, websites: list[str] = None):
    """
    Lên lịch cào vào các mốc giờ cố định trong ngày:
    - 12h: chạy 2h và 14h
    - 24h: chỉ chạy 2h sáng
    """
    if interval_hours not in [12, 24]:
        raise HTTPException(status_code=400, detail="interval_hours must be 12 hoặc 24")
    if websites is None:
        websites = [ws.name for ws in WebsiteStateRepository.get_all() if ws.enabled]

    if interval_hours == 12:
        hours = [2, 14]
    else:  # 24h
        hours = [2]

    # Nếu chỉ có 1 giờ, truyền số nguyên, nếu nhiều giờ truyền list số nguyên
    hour_arg = hours[0] if len(hours) == 1 else hours

    job_id = "crawl_main"  # Luôn dùng 1 job_id duy nhất
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    scheduler.add_job(
        run_crawl,
        trigger='cron',
        id=job_id,
        hour=hour_arg,
        minute=0,
        args=[websites],  # truyền danh sách web vào job
        replace_existing=True
    )
    return {"message": f"Scheduled crawl for {websites or 'all'} at hours {hours} (every {interval_hours}h from 2AM)"}


def run_crawl(websites=None):
    logging.info(f"Scheduler triggered crawl for: {websites}")
    global crawl_processes
    if not websites:
        websites = [ws.name for ws in WebsiteStateRepository.get_all() if ws.enabled]
    for name in websites:
        proc = subprocess.Popen(["python", "main.py", "--action", "test", "--website", name])
        crawl_processes[name] = proc


@app.get("/current_schedule")
def current_schedule():
    job = scheduler.get_job("crawl_main")
    if not job:
        return {"message": "No schedule found"}
    # Lấy thông tin trigger và args
    trigger = str(job.trigger)
    args = job.args
    next_run = job.next_run_time
    return {
        "trigger": trigger,
        "args": args,
        "next_run_time": str(next_run)
    }