#!/usr/bin/env python3

import os
import sys
import re
import time
import traceback
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import scrolledtext
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib.request

USING_BROWSER='firefox'

URL_PATTERN = r'(http|https)://www.archdaily.com/\d+(/.*){0,1}'
URL_PATTERN_CN = r'(http|https)://www.archdaily.cn/cn/\d+(/.*){0,1}'
save_path = ''
failed_input = []

def TravelProject( pid, is_cn) :
    if pid is None:
        return False

    global save_path
    pid = str( pid)
    if USING_BROWSER == 'chrome':
        DesiredCapabilities.CHROME[ 'pageLoadStrategy'] = "none"
        browser = webdriver.Chrome()
    elif USING_BROWSER == 'firefox':
        browser = webdriver.Firefox()
    else:
        print( 'wrong setting with USING_BROWSER')
        exit( 255)
    browser.maximize_window()
    if is_cn :
        start_page = 'https://www.archdaily.cn/cn/%s/' % ( pid)
    else :
        start_page = 'https://www.archdaily.com/%s/' % ( pid)
    print( "打开:%s" % ( start_page))
    browser.get( start_page)
    try :
        WebDriverWait( browser, 30).until(
            EC.presence_of_element_located(( By.XPATH, '//ul[@class="gallery-thumbs"]/li[1]/a[@class="gallery-thumbs-link"]'))
        )
        time.sleep( 10)
    except :
        print( "页面加载超时!")
        browser.close()
        return False

    try :
        no_button = browser.find_element_by_xpath( "//div[@class='afd-modal-body']/a[2]")
        print( '点击"否"按钮，拒绝切换语言...')
        no_button.click()
        time.sleep( 3)
    except :
        pass

    try :
        close_button = browser.find_element_by_xpath( "//div[@id='kenneth-modal-content']/div/a[@class='kth-modal__close__icon']")
        print( '点击"X"，关闭登陆窗口...')
        close_button.click()
        time.sleep( 3)
    except :
        pass

    try :
        cookie_button = browser.find_element_by_xpath( "//button[@id='gdpr-consent']")
        print( '点击"I ACCEPT"按钮，接受Cookie政策...')
        cookie_button.click()
        time.sleep( 5)
    except :
        pass

    try :
        title = browser.find_element_by_xpath( "//div[@id='content']//h1")
        title = title.text
        title = title.replace( '/', '-').replace( '\\', '-')
        title = title.replace( ':', '').replace( '|', '').replace( '<', '').replace( '>', '').replace( '"', '')
        title = title.strip()
    except Exception as e:
        print( type(e))
        print( e)
        print( '未能找到项目标题，抓图失败!!!')
        browser.close()
        return False

    print( "项目ID: %s\n项目名称: %s" % ( pid, title))
    try :
        project_save_path = save_path + title + "/"
        os.makedirs( project_save_path)
    except :
        pass

    try :
        gallery_entry = browser.find_element_by_xpath( '//ul[@class="gallery-thumbs"]/li[1]/a[@class="gallery-thumbs-link"]')
        print( '点击相册入口...')
        if USING_BROWSER == 'chrome':
            ActionChains( browser).move_to_element( gallery_entry).perform()
        time.sleep( 5)
        gallery_entry.click()
        time.sleep( 3)
    except Exception as e:
        print( type(e))
        print( e)
        print( '未找到相册入口，抓图失败!!!')
        browser.close()
        return False

    while True :
        try :
            WebDriverWait( browser, 30).until(
                EC.presence_of_element_located(( By.XPATH, "//a[@id='original-size-image']"))
            )
            time.sleep( 1)
        except Exception as e:
            print( type(e))
            print( e)
            print( "页面加载超时!")
            browser.close()
            return False

        try :
            cookie_button = browser.find_element_by_xpath( "//button[@id='gdpr-consent']")
            print( '点击"I ACCEPT"按钮，接受Cookie政策...')
            cookie_button.click()
            time.sleep( 3)
        except :
            pass

        try :
            page_number = browser.find_element_by_xpath( '//div[@class="afd-gal-mob-count"]/span[@class="js-gal-current"]')
            page_number = page_number.get_attribute( "innerHTML")
            page_number = int( page_number)
            total_page = browser.find_element_by_xpath( '//div[@class="afd-gal-mob-count"]/span[@class="js-gal-length"]')
            total_page = total_page.get_attribute( "innerHTML")
            total_page = int( total_page[ 1:])
            original_size_link = browser.find_element_by_xpath( "//a[@id='original-size-image']")
            img_url = original_size_link.get_attribute( 'href')
            if img_url.startswith( 'https://') :
                img_url = 'http://' + img_url[ 8:]
            filename = project_save_path + ( '%03d-' % ( page_number)) + re.search( r'[^/]+\.(jpg|png)', img_url).group( 0)
            print( '下载原始尺寸图片链接:\n\t%s -> %s' % ( img_url, filename))
        except Exception as e:
            print( type(e))
            print( e)
            print( "抓取图片失败!!!")
            browser.close()
            return False

        if os.path.exists( filename) :
            print( "文件已存在,跳过...")
        else :
            try :
                urllib.request.urlretrieve( img_url, filename = filename)
            except :
                print( "下载超时,重试中...")
                time.sleep( 10)
                try :
                    urllib.request.urlretrieve( img_url, filename = filename)
                except :
                    print( "下载超时,重试中...")
                    time.sleep( 10)
                    try :
                        urllib.request.urlretrieve( img_url, filename = filename)
                    except :
                        print( "下载图片失败!!!")
                        try :
                            os.remove( filename)
                        except :
                            pass
                        browser.close()
                        return False

        if page_number >= total_page :
            print( "已到达最后一页，项目'%s'抓图完毕." % ( title))
            browser.close()
            return True

        try :
            next_page = browser.find_element_by_xpath( "//a[@id='next-image']")
            print( "点击下一页...")
            next_page.click()
            time.sleep( 3)
        except Exception as e:
            print( type(e))
            print( e)
            print( "页面加载超时!")
            browser.close()
            return False

def SelectPath() :
    global window
    global save_path
    if len( save_path) > 0 :
        return
    opts = {}
    opts[ 'initialdir'] = '~/'
    opts[ 'title'] = '选择图片保存的位置'
    window.update()
    dir = filedialog.askdirectory( **opts)
    window.update()
    if len( dir) < 1 :
        print( '操作被取消.')
        window.destroy()
        sys.exit( 1)
    save_path = dir + '/'

        
def Start( input_list) :
    SelectPath()
    global window
    global failed_input
    failed_input = []
    for line in input_list.splitlines() :
        line = line.strip()
        if len( line) <= 0 :
            continue
        pid = None
        is_cn = False
        try :
            pid = int( line)
        except :
            if re.match( URL_PATTERN, line) is None :
                if re.match( URL_PATTERN_CN, line) is None :
                    print( "不支持这个URL:\n\t%s\n" % ( line))
                else :
                    pid = re.search( r'\d+', line).group( 0)
                    is_cn = True
            else :
                pid = re.search( r'\d+', line).group( 0)
        try :
            if not TravelProject( pid, is_cn) :
                failed_input.append( line)
        except Exception as e:
            print( type(e))
            print( e)
            print( "出现异常,跳过当前项目!")
            failed_input.append( line)
    window.update()
    if len( failed_input) > 0 :
        global text
        msg = "\n".join( failed_input)
        messagebox.showwarning( "抓取结束", "下列URL抓取失败了:\n" + msg)
        text.delete( "1.0", 'end')
        text.insert( "end", msg)
        window.update()
    else :
        messagebox.showinfo( "抓取结束", "所有项目都已成功抓取!")
        window.destroy()
        sys.exit( 0)

window = tk.Tk()
window.title( 'ArchDaily抓取工具')
tk.Label( window, text='输入要抓取的URL,各占一行:').pack()
text = scrolledtext.ScrolledText( window)
text.pack()
tk.Button( window, text='开始', command = lambda:Start( text.get( "1.0", "end-1c"))).pack()
window.mainloop()

