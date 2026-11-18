#---IMPORTS--#
import random
from tkinter import *
from tkinter import ttk
import pygame as pg
from pathlib import Path

#---SETUP---#
assets_dir = Path(__file__).resolve().parent / "assets"

deck = []

hand = []
dealer = []

dealertotal = [0,0]
playertotal = [0,0]

money = 100 #sets starting money
betVal = 0 #current bet value

def FormatCard(tcard): #format as card[[minimum value,maximum value], Name, Suit(1st letter)]
    card=[]
    if (tcard[1] == 1):
        card = [[1,11],"Ace", ""]
    elif (tcard[1] == 11):
        card = [[10, 10],"Jack", ""]
    elif (tcard[1] == 12):
        card = [[10, 10],"Queen", ""]
    elif (tcard[1] == 13):
        card = [[10, 10],"King", ""]
    else:
        card =  [[tcard[1], tcard[1]], tcard[1], ""]

    if (tcard[0] == '0'):
        card[2] = "S"
    elif (tcard[0] == '1'):
        card[2] = "H"
    elif (tcard[0] == '2'):
            card[2] = "D"
    elif (tcard[0] == '3'):
            card[2] = "C"

    return card

for i in range(0,4): #generate full deck of cards
    for j in range(1, 14): #13 for each suit, starting at 1
        deck.append(FormatCard([i,j])) #format to desired way

def draw(): #draws random card and deletes from deck, returns drawn card
    global deck
    n = len(deck)
    index = random.randint(0,(n-1))
    card = deck[index]
    ndeck = []
    for i in range(n):
        if (n != index):
            ndeck.append(deck[i])
    deck = ndeck
    return card

def displayHand(hand, hide): #returns array of cards
    n = len(hand)
    if (hide == True):
        return((hand[0])[1])
    a=[]
    for i in range (n):
        a.append((hand[i])[1])
    return a

def calcTotal(hand): #calculates maximum and minimum value of hand (returns both as an array [max, min])
    n = len(hand)
    total = [0, 0]
    for i in range(n):
        total[0] += ((hand[i])[0])[0]
        total[1] += ((hand[i])[0])[1]
    return total

def findCardSprite(card): #returns file path to sprite for desired card
    suit = card[2]
    num = card[1]
    file=""
    if (num==1):
        num = 'A'
    elif (num == 11):
        num='J'
    elif (num == 12):
        num='Q'
    elif (num == 13):
        num = 'K'

    file = suit + num + ".jpg"
    return str(assets_dir / "cards/IndividualCards/" + file) #returns full file path for any card in the deck
#---GAME---#
#draw 2 cards each and calc total value
dealer.append(draw())
dealer.append(draw())
hand.append(draw())
hand.append(draw())

dealertotal = calcTotal(dealer)
playertotal = calcTotal(hand)

def tkpg(): #tkinter initialises pygame and then closes
    global root
    root.destroy()
    game()

def addBet(val, BetButton):
    global betVal, money

    if betVal + val >= 0 and (val <= 0 or money >= val):
        betVal += val
        money += (-1*val)
        BetButton.text = "BET: " + str(betVal)

def game():
    global money
    #print("Game")
    pg.init()
    screen = pg.display.set_mode((1280,720))
    pg.display.set_caption('BlackJack')
    pg.display.set_icon(pg.image.load("assets/cards/IndividualCards/AS.png"))
    clock = pg.time.Clock()
    font = pg.font.Font(None, 36)
    running=True

    ##buttons
    BetButton = button(100, 100, 100, 50, "BET: " + str(betVal), font, lambda: None)
    AddButton = button(210, 100, 50, 50, "+", font, lambda: addBet(10, BetButton))
    SubButton = button(40, 100, 50, 50, "-", font, lambda: addBet(-10, BetButton))

    while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            AddButton.handle_event(event)
            SubButton.handle_event(event)

    # fill the screen with a color to wipe away anything from last frame
        screen.fill("#15AA1A")

    # RENDER YOUR GAME HERE
        moneyCount = font.render("Money: " + str(money), True, (255, 255, 255))
        screen.blit(moneyCount, (10, 10))  # top-left corner with 10px padding
        #betShow = font.render("Bet: " + str(betVal), True, (255,255,255))
        #screen.blit(betVal, (10, 10))
        BetButton.draw(screen)
        AddButton.draw(screen)
        SubButton.draw(screen)
       

    # flip() the display to put your work on screen
        pg.display.flip()
        clock.tick(60)  # limits FPS to 60

    pg.quit()

class button: #adds class to save time making buttons (x,y, width, height, text, font, colour, hover colour, text colour)
    def __init__(self, x, y, width, height, text, font, on_click=None,
                 color=("#19440A"), hover_color=("#44F808"),
                 text_color=("#FFFFFF")):
        self.rect = pg.Rect(x, y, width, height)
        self.font = font
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.on_click = on_click  # function to call when clicked

    def is_hovered(self):
        return self.rect.collidepoint(pg.mouse.get_pos())

    def handle_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.on_click:
                    self.on_click()
                return True
        return False

    def draw(self, surface):
        color = self.hover_color if self.is_hovered() else self.color
        pg.draw.rect(surface, color, self.rect, border_radius=8)
        label = self.font.render(self.text, True, self.text_color)
        surface.blit(label, label.get_rect(center=self.rect.center))


#---TKinter---# (I HATE TKINTER IDK WHY I DID THIS PART)
root = Tk()

#styles
style = ttk.Style()
style.configure("Title.TLabel", foreground="#FFFFFF", background="#15AA1A", anchor="center",
                font=("Helvetica", 48, "bold"))
style.configure("Button.TButton", foreground="#FFFFFF", background="#0D7010", anchor="center",
                font=("Helvetica", 30), padding=15)
style.configure("Game.TFrame", background="#15AA1A")

#window
root.title("BlackJack") #top bar title
root.geometry("800x600") #set windo size
frm = ttk.Frame(root, padding=10, style="Game.TFrame") #general formatting of frame
frm.grid(sticky="nsew")
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
frm.columnconfigure(0, weight=1)
frm.rowconfigure(0, weight=1)
frm.rowconfigure(1, weight=1)
frm.rowconfigure(2, weight=1)

#elements
ttk.Label(frm, text="BlackJack", style="Title.TLabel").grid(column=0, row=0, sticky="n", )
##add 2 side by side images from the assets folder (folder inside same directory as this python file)

img_left = PhotoImage(file=str(assets_dir / "cards/IndividualCards/AS.png")).zoom(4,4)
img_right = PhotoImage(file=str(assets_dir / "cards/IndividualCards/KH.png")).zoom(4,4)
frm.images = [img_left, img_right]
img_frm = ttk.Frame(frm, style="Game.TFrame")
img_frm.grid(column=0, row=1)

ttk.Label(img_frm, image=img_left).grid(column=0, row=0, padx=5)
ttk.Label(img_frm, image=img_right).grid(column=1, row=0, padx=5)

ttk.Button(frm, text="PLAY", command=tkpg, style="Button.TButton").grid(column=0, row=2, sticky="s")

root.mainloop()