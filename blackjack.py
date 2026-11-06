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
    print("working for now!")
    global root
    root.destroy()
    game()


def game():
    print("Game")
    pg.init()
    screen = pg.display.set_mode((1280,720))
    clock = pg.time.Clock()
    running=True


#---TKinter---#
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