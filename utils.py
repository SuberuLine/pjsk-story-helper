import logging
import cv2

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def capture_region(d, left, top, right, bottom, filename="region_screenshot.png"):
    try:
        screen = d.screenshot(format="opencv")
        if screen is None:
            logging.error("指定位置截图失败，返回None")
            return None
        
        height, width = screen.shape[:2]
        left = max(0, min(left, width-1))
        right = max(left+1, min(right, width))
        top = max(0, min(top, height-1))
        bottom = max(top+1, min(bottom, height))
        
        region_image = screen[top:bottom, left:right]
        cv2.imwrite(filename, region_image)
        return region_image
    except Exception as e:
        logging.error(f"指定位置截图过程中发生错误: {e}")
        return None