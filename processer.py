import cv2
from skimage.metrics import structural_similarity as ssim

def preprocess_image(image):
    # 转换为灰度图
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 应用高斯模糊进行降噪
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # 应用自适应阈值二值化
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                cv2.THRESH_BINARY, 11, 2)
    
    return thresh

def compare_images(image_path1, image_path2):
    img1 = cv2.imread(image_path1)
    img2 = cv2.imread(image_path2)

    if img1 is None or img2 is None:
        raise ValueError("无法读取一个或两个图像文件")

    # 确保两个图像都是3通道的
    if len(img1.shape) == 2:
        img1 = cv2.cvtColor(img1, cv2.COLOR_GRAY2BGR)
    if len(img2.shape) == 2:
        img2 = cv2.cvtColor(img2, cv2.COLOR_GRAY2BGR)

    # 预处理图片
    processed1 = preprocess_image(img1)
    processed2 = preprocess_image(img2)
    
    # 计算结构相似性指数 (SSIM)
    similarity_index, _ = ssim(processed1, processed2, full=True)
    
    return similarity_index

def main():
    image1_path = "path/to/image1.jpg"
    image2_path = "path/to/image2.jpg"
    
    similarity = compare_images(image1_path, image2_path)
    
    print(f"结构相似性指数 (SSIM): {similarity:.4f}")
    
    if similarity > 0.95 :
        print("这两张图片非常相似")
    elif similarity > 0.85:
        print("这两张图片比较相似")
    else:
        print("这两张图片差异较大")

if __name__ == "__main__":
    main()
