import uiautomator2 as u2
import time
import processer
import utils
import logging
import threading
from config import *

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
d = u2.connect(ADB_HOST)
logging.info(f"设备信息: {d.info}")

FIRST_ENTER = True
PAUSE_EVENT = threading.Event()
READING_STATE = {}

def main():
    global FIRST_ENTER, PAUSE_EVENT

    if d.info['displayHeight'] != 1080 or d.info['displayWidth'] != 1920:
        logging.error('请确保分辨率为1920x1080!')
        exit()

    network_error_checker_thread = threading.Thread(target=network_error_checker, daemon=True)
    network_error_checker_thread.start()

    while True:
        if PAUSE_EVENT.is_set():
            time.sleep(1)
            continue

        if is_main_page():
            time.sleep(1)
            d.click(*COORDINATES['MAIN_PAGE_STORY_BTN'])
            time.sleep(1)

        if is_story_page():
            time.sleep(1)
            d.click(*COORDINATES['MAIN_STORY_BTN'])
            time.sleep(1)

        if is_story_home():
            if FIRST_ENTER:
                set_unreaded_filter()
                FIRST_ENTER = False
            save_reading_state()  # 保存当前阅读状态

        start_story()
        d.click(*COORDINATES['FORWARD_BUTTON'])

def check_network_error_retryable():
    # 检查网络错误是否可重试
    utils.capture_region(d, 625, 450, 1315, 700, "./img/network_error.png")
    similarity = processer.compare_images("./img/network_error.png", "./img/resources/network_error_retryable.png")
    logging.info(f"当前为错误弹窗概率: {similarity * 100:.2f}%")
    return similarity > NETWORK_ERROR_SIMILARITY_THRESHOLD

def network_error_checker():
    global PAUSE_EVENT
    while True:
        if check_network_error_retryable():
            logging.warning("检测到网络错误弹窗，脚本已暂停。")
            PAUSE_EVENT.set()
            time.sleep(1)
            d.click(*COORDINATES['NETWORK_ERROR_RETRY_BUTTON'])  # 点击重试
            time.sleep(1)
            restore_reading_state()  # 恢复阅读状态
            PAUSE_EVENT.clear()
            logging.info("脚本继续运行")
        time.sleep(NETWORK_ERROR_CHECK_INTERVAL)  # 每10秒检查一次

def save_reading_state():
    global READING_STATE
    READING_STATE['last_click_time'] = time.time()  # 保存最后一次点击时间
    # todo: more state

def restore_reading_state():
    global READING_STATE
    last_click_time = READING_STATE.get('last_click_time', time.time())
    current_time = time.time()
    
    # 模拟等待一段时间，以便重新进入原来的阅读状态
    while current_time - last_click_time < READING_STATE_RESTORE_WAIT_TIME:  # 等待5秒后继续
        time.sleep(1)

def set_unreaded_filter():
    # 设置过滤只剩未读/跳过剧情
    d.click(*COORDINATES['FILTER_BUTTON'])
    time.sleep(CLICK_INTERVAL)
    d.click(*COORDINATES['FILTER_OPTION'])
    time.sleep(CLICK_INTERVAL)
    d.click(*COORDINATES['FILTER_CONFIRM'])
    time.sleep(CLICK_INTERVAL)

def is_main_page():
    utils.capture_region(d, 1300, 943, 1556, 1016, "./img/main_page.png")
    similarity = processer.compare_images("./img/main_page.png", "./img/resources/main_page_story_btn.png")
    logging.info(f"当前主页相似度: {similarity * 100:.2f}%")
    if similarity > MAIN_PAGE_STORY_BTN_SIMILARITY_THRESHOLD:
        logging.info("当前为主页，准备进入故事页面")
        return True
    else:
        return False
    
def is_story_page():
    utils.capture_region(d, 80, 200, 1330, 600, "./img/story_page.png")
    similarity = processer.compare_images("./img/story_page.png", "./img/resources/main_story_btn.png")
    logging.info(f"当前故事页相似度: {similarity * 100:.2f}%")
    if similarity > STORY_PAGE_SIMILARITY_THRESHOLD:
        logging.info("当前为主线故事页")
        return True
    else:
        return False

def is_story_home():
    utils.capture_region(d, 8, 440, 136, 640, "./img/story_home.png")
    similarity = processer.compare_images("./img/story_home.png", "./img/resources/story_home.png")

    if similarity > STORY_HOME_SIMILARITY_THRESHOLD:
        logging.info("当前为主线故事页")
        return True
    else:
        return False
    
def start_story():
    is_unreaded = check_unreaded()
    d.click(*COORDINATES['START_STORY'])
    time.sleep(CLICK_INTERVAL)
    for _ in range(SWIPE_COUNT):
        d.swipe(*SWIPE_START, *SWIPE_END, duration=SWIPE_DURATION)
        time.sleep(SWIPE_DURATION)
    time.sleep(CLICK_INTERVAL)
    d.screenshot("./img/current_story_template.png")
    time.sleep(CLICK_INTERVAL)
    if is_unreaded:
        click_from_bottom_to_top()
    else:
        d.click(*COORDINATES['READING_END_CLICK'])
    time.sleep(CLICK_INTERVAL)
    d.click(*COORDINATES['CONTINUOUS_READ'])
    time.sleep(CLICK_INTERVAL)
    d.click(*COORDINATES['NO_VOICE_ENTER'])
    time.sleep(STORY_START_WAIT_TIME)
    logging.info("开始阅读")

    last_click_time = time.time()
    while True:
        if PAUSE_EVENT.is_set():
            time.sleep(1)
            continue
        d.click(*COORDINATES['READING_CLICK'])
        current_time = time.time()
        # 如果当前时间与上次点击时间差大于3秒，则检查是否阅读结束
        if current_time - last_click_time > 3:
            if not is_reading():
                break
            last_click_time = current_time
    logging.info("阅读结束")
    time.sleep(1)

def is_reading():
    d.screenshot("./img/current_story_progress.png")
    similarity = processer.compare_images("./img/current_story_progress.png", "./img/current_story_template.png")
    logging.info(f"当前阅读进度相似度: {similarity * 100:.2f}%")
    if similarity < READING_END_SIMILARITY_THRESHOLD:
        return True
    else:
        logging.info("阅读结束")
        return False
    
def check_unreaded():
    utils.capture_region(d, 666, 428, 698, 460, "./img/unreaded_icon.png")
    similarity = processer.compare_images("./img/unreaded_icon.png", "./img/resources/unreaded_icon.png")
    logging.info(f"当前未读进度概率: {similarity * 100:.2f}%")
    return similarity > UNREADED_ICON_SIMILARITY_THRESHOLD

def click_from_bottom_to_top():
    x, y = UNREADED_STORY_CLICK_START
    max_attempts = UNREADED_STORY_MAX_ATTEMPTS
    
    for attempt in range(max_attempts):
        d.click(x, y)
        time.sleep(CLICK_INTERVAL)
        
        utils.capture_region(d, 827, 778, 1087, 851, "./img/start_btn.png")
        similarity = processer.compare_images("./img/start_btn.png", "./img/resources/start_btn.png")
        logging.info(f"第{attempt+1}次点击，开始按钮相似度: {similarity * 100:.2f}%")
        
        if similarity > START_BUTTON_SIMILARITY_THRESHOLD:
            logging.info(f"在第{attempt+1}次点击时找到了开始按钮")
            return True
        
        # 每次点击后，y坐标向上移动一定距离 默认为170
        y -= UNREADED_STORY_CLICK_STEP 
    
    logging.info(f"{UNREADED_STORY_MAX_ATTEMPTS}次点击都没有找到开始按钮")
    return False

if __name__ == "__main__":
    main()
