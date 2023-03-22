import time

import allure
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from litemall.log_utils import logger


# 问题一：新增产生了脏数据
# 解决方案：清理对应脏数据，清理的方式可通过接口也可通过ui的方式，数据的清理一定要放在断言之后操作，否则会影响断言结果

# 问题二：代码存在大量的强制等待
class TestLitemall:
    # 前置动作
    def setup(self):
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(3)

        self.driver.get("https://litemall.hogwarts.ceshiren.com/")
        # 问题：输入框内有默认值，此时send keys不会清空只会追加
        # 解决方案：在输入之前对输入框进行清空
        self.driver.find_element(By.XPATH, '//*[@name="username"]').clear()
        self.driver.find_element(By.XPATH, '//*[@name="username"]').send_keys("manage")
        self.driver.find_element(By.XPATH, '//*[@name="password"]').clear()
        self.driver.find_element(By.XPATH, '//*[@name="password"]').send_keys("manage123")
        # 点击登录按钮
        self.driver.find_element(By.CSS_SELECTOR, ".el-button--primary").click()
        self.driver.maximize_window()

    # 后置动作
    def teardown(self):
        self.driver.quit()

    def get_screen(self):
        # 获取时间戳
        timestamp = int(time.time())
        # 创建图片路径（注意：一定要提前创建好images文件）
        images_path = f"./images/images_{timestamp}.PNG"
        # 截图
        self.driver.save_screenshot(images_path)
        # 将截图放到报告的数据中
        allure.attach.file(images_path, name="picture", attachment_type=allure.attachment_type.PNG)

    # 新增功能
    def test_add_type(self):
        self.driver.find_element(By.XPATH, '//*[text()="商场管理"]').click()
        self.driver.find_element(By.XPATH, '//*[text()="商品类目"]').click()
        # 点击添加按钮
        self.driver.find_element(By.XPATH, '//*[text()="添加"]').click()
        # 添加商品信息
        self.driver.find_element(By.CSS_SELECTOR, ".el-input__inner").send_keys("新增商品测试777")

        # ===============使用显示等待优化
        # ele = WebDriverWait(self.driver, 10).until(
        #     expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, '.dialog-footer .el-button--primary')))
        # ele.click()

        # ===============使用显示等待优化方案二：自定义显示等待条件
        def click_exception(by, element, max_attempts=5):
            def _inner(driver):
                # 多次点击按钮
                # 实际点击次数
                actul_attempts = 0
                while actul_attempts < max_attempts:
                    # 进行点击操作
                    actul_attempts += 1  # 每次循环实际点击次数+1
                    try:
                        # 如果点击过程报错，则直接执行except罗技，并且继续循环
                        # 如果没有报错，则直接return，循环结束
                        driver.find_element(by, element).click()
                        return True
                    except Exception:
                        logger.debug("点击的时候出现了一次异常")
                # 当实际点击次数大于最大点击次数时，结束循环并抛出异常
                raise Exception("超出了最大点击次数")

            return _inner

        WebDriverWait(self.driver, 10).until(click_exception(By.CSS_SELECTOR, '.dialog-footer .el-button--primary'))

        # self.driver.find_element(By.CSS_SELECTOR, '.dialog-footer .el-button--primary').click()
        # find_elements如果没找到会返回空列表，find_element如果没找到会直接报错
        # 如果没找到程序也不应报错
        expect_ele = self.driver.find_elements(By.XPATH, '//*[text()="新增商品测试777"]')
        self.get_screen()
        # 清理脏数据
        self.driver.find_element(By.XPATH, '//*[text()="新增商品测试777"]/../..//*[text()="删除"]').click()
        logger.info(f"断言获取到的实际结果为{expect_ele}")
        # 断言产品新增后是否成功找到，如果找到则证明新增成功，如果没有找到则新增失败
        # 判断查找的结果是否为空列表，如果列表为空则证明没找到，反之代表元素已找到，用例执行成功
        assert expect_ele != []
        time.sleep(3)

    # 删除功能
    def test_delete_type(self):
        # ====================================造数据步骤
        self.driver.find_element(By.XPATH, '//*[text()="商场管理"]').click()
        self.driver.find_element(By.XPATH, '//*[text()="商品类目"]').click()
        # 点击添加按钮
        self.driver.find_element(By.XPATH, '//*[text()="添加"]').click()
        # 添加商品信息
        self.driver.find_element(By.CSS_SELECTOR, ".el-input__inner").send_keys("删除商品测试777")

        # 使用显示等待优化
        # time.sleep(5)
        # self.driver.find_element(By.XPATH, '//*[text()="确定"]').click()
        ele = WebDriverWait(self.driver, 50).until(
            expected_conditions.element_to_be_clickable((By.XPATH, '//*[text()="确定"]')))
        ele.click()

        self.driver.find_element(By.CSS_SELECTOR, '.dialog-footer .el-button--primary').click()
        # =============删除步骤
        self.driver.find_element(By.XPATH, '//*[text()="删除商品测试777"]/../..//*[text()="删除"]').click()
        # find_elements如果没找到会返回空列表，find_element如果没找到会直接报错
        # 如果没找到程序也不应报错
        # time.sleep(5)
        # 问题：代码执行速度过快，元素还未消失就被捕获
        # 解决方案：确认该元素不存在后再捕获
        WebDriverWait(self.driver, 10).until_not(
            expected_conditions.visibility_of_any_elements_located((By.XPATH, '//*[text()="删除商品测试777"]')))

        expect_ele = self.driver.find_elements(By.XPATH, '//*[text()="删除商品测试777"]')
        logger.info(f"断言获取到的实际结果为{expect_ele}")
        # 断言：删除之后获取的商品类目”删除商品测试777“是否还能获取到，如果获取到则证明删除失败，反之成功
        assert expect_ele == []
