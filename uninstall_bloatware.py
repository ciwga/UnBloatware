# _*_ coding:utf-8 _*_
import fileinput
import subprocess
import os
import time

adb = os.path.dirname(os.path.realpath(__file__)) + "/" + "adb/adb.exe"
file1 = os.path.dirname(os.path.realpath(__file__)) + "/" + "package1.txt"
file2 = os.path.dirname(os.path.realpath(__file__)) + "/" + "package2.txt"

vestel = ["com.vestel.vestelanalyticservice",
          "com.vestel.customeragreement",
          "com.dewav.dwgesture",
          "com.vestel.vmarket",
          "com.vestel.cloud",
          "com.example",
          "com.assistant.icontrol",
          "com.mxtech.videoplayer.ad",
          "com.mxtech.ffmpeg.v7_vfpv3d16"]
gapps = ["com.android.chrome",
         "com.google.android.googlequicksearchbox",
         "com.google.android.marvin.talkback",
         "com.google.android.apps.tachyon",
         "com.google.android.music",
         "com.google.android.tag",
         "com.google.android.videos",
         "com.google.android.calendar",
         "com.google.android.talk"]
vendor = ["com.android.email",
          "com.android.stk",
          "com.android.exchange"]
facebook = ["com.facebook.katana",
            "com.facebook.appmanager",
            "com.facebook.services",
            "com.facebook.system"]
netflix = ["com.netflix.mediaclient",
           "com.netflix.partner.activation"]
microsoft = ["com.swiftkey.swiftkeyconfigurator",
             "com.swiftkey.languageprovider",
             "com.touchtype.swiftkey",
             "com.microsoft.office.outlook",
             "com.microsoft.appmanager",
             "com.microsoft.skydrive",
             "com.microsoft.office.powerpoint",
             "com.microsoft.office.excel",
             "com.microsoft.office.word",
             "com.microsoft.office.officehubrow",
             "com.skype.raider"]
bixby = ["com.samsung.android.bixby.wakeup",
         "com.samsung.android.bixby.service",
         "com.samsung.android.visionintelligence",
         "com.samsung.android.bixby.agent",
         "com.samsung.android.bixby.agent.dummy",
         "com.samsung.android.bixbyvision.framework",
         "com.vlingo.midas"]


def deleter(name):
    os.system('cls')
    print("\033[1;31;40m"+str(name)+" "+"Uninstalling Packages...\033[0m")
    for i in name:
        subprocess.run([adb, "shell", "pm uninstall -k --user 0", i])
    os.system("taskkill /f /im adb.exe")
    print('DONE')
    time.sleep(3)


def listpack():
    out = subprocess.PIPE
    get_names = subprocess.run([adb, "shell", "pm list packages"], stdout=out)
    with open(file1, 'w+', encoding='utf-8') as f1:
        for name in get_names.stdout.decode(
                'utf-8'):
            f1.write(name.strip("\n"))
    with open(file2, 'w+', encoding='utf-8') as f2:
        for line in fileinput.input(file1):
            f2.write(line.replace('package:', ''))
    with open(file2, 'r', encoding='utf-8') as words:
        reading = words.read().split('\n')
        os.system('cls')
        for word in reading:
            print(word)
    os.remove(file1)
    os.remove(file2)
    os.system("taskkill /f /im adb.exe")


def menu():
    info = print("\x1b[1;32;40mPackages\x1b[0m\n1.Vestel\n2.Google",
                 "\n3.Facebook\n4.Microsoft\n5.Netflix\n6.VendorApps",
                 "\n7.Bixby\n8.Get all packages")
    pack = {1: vestel,
            2: gapps,
            3: facebook,
            4: microsoft,
            5: netflix,
            6: vendor,
            7: bixby}
    try:
        numbers = int(input('Choose One: '))
        if numbers == 8:
            listpack()
        else:
            deleter(pack[numbers])
            os.system('cls')
            return info, menu()
    except ValueError:
        menu()


menu()
