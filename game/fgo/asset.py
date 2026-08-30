
import cv2


class Asset:

    # Battle
    chooseFriendIcon = cv2.imread('./assets/fgo/battle/chooseFriendIcon.png')

    gobackBtnImage = cv2.imread('./assets/fgo/etc/gobackBtn.png')
    OKBtnImage = cv2.imread('./assets/fgo/battle/ok.png')
    YesBtnImage = cv2.imread('./assets/fgo//etc/yesBtn.png')
    CloseBtnImage = cv2.imread('./assets/fgo/etc/closeBtn.png')
    # same "關閉" text but the plain white pill-button style used by
    # reward/support popups (e.g. the 友情點數 popup) - doesn't match
    # CloseBtnImage's style (different background chrome), so it needs a
    # separate template.
    CloseBtnPillImage = cv2.imread('./assets/fgo/etc/closeBtnPill.png')
    BackToLobbyBtnImage = cv2.imread('./assets/fgo/etc/backToLobbyBtn.png')



