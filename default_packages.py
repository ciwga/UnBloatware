def get_packages() -> dict:
    """
    Returns a dictionary of package groups.
    
    Returns:
        dict: A dictionary where keys are group names and values are lists of package names.
    """
    return {
        "vestel": [
            "com.vestel.vestelanalyticservice",
            "com.vestel.customeragreement",
            "com.dewav.dwgesture",
            "com.vestel.vmarket",
            "com.vestel.cloud",
            "com.assistant.icontrol",
            "com.mxtech.videoplayer.ad",
            "com.mxtech.ffmpeg.v7_vfpv3d16"
        ],
        "gapps": [
            "com.android.chrome",
            "com.google.android.googlequicksearchbox",
            "com.google.android.marvin.talkback",
            "com.google.android.apps.tachyon",
            "com.google.android.music",
            "com.google.android.tag",
            "com.google.android.videos",
            "com.google.android.calendar",
            "com.google.android.talk"
        ],
        "vendor": [
            "com.android.email",
            "com.android.stk",
            "com.example",
            "com.android.exchange"
        ],
        "facebook": [
            "com.facebook.katana",
            "com.facebook.appmanager",
            "com.facebook.services",
            "com.facebook.system"
        ],
        "netflix": [
            "com.netflix.mediaclient",
            "com.netflix.partner.activation"
        ],
        "microsoft": [
            "com.swiftkey.swiftkeyconfigurator",
            "com.swiftkey.languageprovider",
            "com.touchtype.swiftkey",
            "com.microsoft.office.outlook",
            "com.microsoft.appmanager",
            "com.microsoft.skydrive",
            "com.microsoft.office.powerpoint",
            "com.microsoft.office.excel",
            "com.microsoft.office.word",
            "com.microsoft.office.officehubrow",
            "com.skype.raider"
        ],
        "bixby": [
            "com.samsung.android.bixby.wakeup",
            "com.samsung.android.bixby.service",
            "com.samsung.android.visionintelligence",
            "com.samsung.android.bixby.agent",
            "com.samsung.android.bixby.agent.dummy",
            "com.samsung.android.bixbyvision.framework",
            "com.vlingo.midas"
        ]
    }